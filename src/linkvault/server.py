from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import __version__
from .auth import AuthStore, User
from .config import load_config
from .store import BookmarkFilters, BookmarkStore


def make_store() -> BookmarkStore:
    return BookmarkStore(load_config().data_path)


def make_auth_store() -> AuthStore:
    return AuthStore(load_config().data_path)


class LinkVaultHandler(BaseHTTPRequestHandler):
    server_version = f"LinkVault/{__version__}"

    def do_GET(self) -> None:
        store = make_store()
        auth_store = make_auth_store()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/healthz":
            self.send_json({"ok": True, "version": __version__})
        elif path == "/api/setup/status":
            config = load_config()
            self.send_json(
                {
                    "setup_required": auth_store.setup_required(),
                    "setup_token_required": bool(config.setup_token),
                }
            )
        elif path == "/api/me":
            user = self.current_user(auth_store)
            self.send_json(
                {
                    "authenticated": user is not None,
                    "setup_required": auth_store.setup_required(),
                    "user": user.to_dict() if user else None,
                }
            )
        elif path == "/api/bookmarks":
            if not self.require_auth(auth_store):
                return
            params = parse_qs(parsed_url.query)
            query = get_query_param(params, "q")
            filters = filters_from_query(params)
            self.send_json(
                {
                    "bookmarks": [bookmark.to_dict() for bookmark in store.list(query=query, filters=filters)],
                    "query": query,
                    "filters": filters.to_dict(),
                }
            )
        elif path.startswith("/api/bookmarks/"):
            if not self.require_auth(auth_store):
                return
            bookmark = store.get(path.rsplit("/", 1)[-1])
            if not bookmark:
                self.send_json({"error": "bookmark not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json(bookmark.to_dict())
        elif path == "/api/dedup":
            if not self.require_auth(auth_store):
                return
            self.send_json({"groups": store.dedup_groups()})
        elif path == "/api/dedup/dry-run":
            if not self.require_auth(auth_store):
                return
            self.send_json(store.dedup_dry_run())
        elif path == "/":
            self.send_html(index_html())
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        store = make_store()
        auth_store = make_auth_store()

        try:
            payload = self.read_json()
        except (json.JSONDecodeError, ValueError):
            self.send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            if path == "/api/setup":
                user = auth_store.create_initial_user(
                    str(payload.get("username", "")),
                    str(payload.get("password", "")),
                    str(payload.get("setup_token", "")),
                    load_config().setup_token,
                )
                session_id = auth_store.create_session(user.id)
                self.send_json(
                    {"user": user.to_dict(), "setup_required": False},
                    HTTPStatus.CREATED,
                    headers=[session_cookie_header(session_id)],
                )
            elif path == "/api/login":
                user = auth_store.authenticate(str(payload.get("username", "")), str(payload.get("password", "")))
                if not user:
                    self.send_json({"error": "invalid username or password"}, HTTPStatus.UNAUTHORIZED)
                    return
                session_id = auth_store.create_session(user.id)
                self.send_json({"user": user.to_dict()}, headers=[session_cookie_header(session_id)])
            elif path == "/api/logout":
                auth_store.delete_session(self.session_cookie())
                self.send_json({"logged_out": True}, headers=[expired_session_cookie_header()])
            elif path == "/api/bookmarks/bulk":
                if not self.require_auth(auth_store):
                    return
                self.send_json(store.bulk_update(payload))
            elif path == "/api/bookmarks":
                if not self.require_auth(auth_store):
                    return
                bookmark = store.add(payload)
                self.send_json(bookmark.to_dict(), HTTPStatus.CREATED)
            elif path == "/api/import/browser-html":
                if not self.require_auth(auth_store):
                    return
                html = str(payload.get("html", ""))
                self.send_json(store.import_browser_html(html), HTTPStatus.CREATED)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PATCH(self) -> None:
        self.update_bookmark()

    def do_PUT(self) -> None:
        self.update_bookmark()

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/bookmarks/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.require_auth(make_auth_store()):
            return

        deleted = make_store().delete(path.rsplit("/", 1)[-1])
        if not deleted:
            self.send_json({"error": "bookmark not found"}, HTTPStatus.NOT_FOUND)
            return
        self.send_json({"deleted": True})

    def update_bookmark(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/bookmarks/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.require_auth(make_auth_store()):
            return

        try:
            payload = self.read_json()
            bookmark = make_store().update(path.rsplit("/", 1)[-1], payload)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except json.JSONDecodeError:
            self.send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return

        if not bookmark:
            self.send_json({"error": "bookmark not found"}, HTTPStatus.NOT_FOUND)
            return
        self.send_json(bookmark.to_dict())

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length)
        payload = json.loads(body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("json object expected")
        return payload

    def current_user(self, auth_store: AuthStore) -> User | None:
        return auth_store.user_for_session(self.session_cookie())

    def require_auth(self, auth_store: AuthStore) -> User | None:
        user = self.current_user(auth_store)
        if user:
            return user
        self.send_json({"error": "authentication required"}, HTTPStatus.UNAUTHORIZED)
        return None

    def session_cookie(self) -> str:
        cookie_header = self.headers.get("cookie", "")
        if not cookie_header:
            return ""
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        morsel = cookie.get("linkvault_session")
        return morsel.value if morsel else ""

    def send_json(
        self,
        payload: dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
        headers: list[tuple[str, str]] | None = None,
    ) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        for name, value in headers or []:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def index_html() -> str:
    return """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LinkVault</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 960px; }
    input, textarea, button { font: inherit; padding: .55rem; }
    input, textarea { width: 100%; box-sizing: border-box; margin: .25rem 0 .75rem; }
    button { border: 1px solid #222; background: #fff; border-radius: 6px; cursor: pointer; margin-right: .35rem; }
    pre { background: #f2f2f2; padding: 1rem; overflow: auto; }
    .row { border-top: 1px solid #ddd; padding: .75rem 0; }
    .muted { color: #555; }
    .error { color: #b00020; }
    .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
    .actions { margin: .65rem 0; }
    .edit-form { margin-top: .75rem; padding: .75rem; border: 1px solid #ddd; border-radius: 6px; }
    .edit-form textarea { min-height: 4rem; }
    .bulk-actions { border: 1px solid #ddd; border-radius: 6px; padding: .75rem; margin: 1rem 0; }
    [hidden] { display: none !important; }
  </style>
</head>
<body>
  <div class="toolbar">
    <div>
      <h1>LinkVault MVP</h1>
      <p>Links speichern, importieren, bearbeiten und Dubletten als Dry-Run pruefen.</p>
    </div>
    <div id="userbar" hidden>
      <span id="current-user"></span>
      <button id="logout" type="button">Logout</button>
    </div>
  </div>

  <section id="auth-panel">
    <h2 id="auth-title">Login</h2>
    <p id="auth-help" class="muted"></p>
    <form id="setup-form" hidden>
      <label>Setup-Token <input name="setup_token" autocomplete="one-time-code"></label>
      <label>Benutzername <input name="username" autocomplete="username" required></label>
      <label>Passwort <input name="password" type="password" autocomplete="new-password" minlength="12" required></label>
      <button>Admin anlegen</button>
    </form>
    <form id="login-form" hidden>
      <label>Benutzername <input name="username" autocomplete="username" required></label>
      <label>Passwort <input name="password" type="password" autocomplete="current-password" required></label>
      <button>Einloggen</button>
    </form>
    <p id="auth-error" class="error"></p>
  </section>

  <main id="app" hidden>

  <h2>Bookmark speichern</h2>
  <form id="bookmark-form">
    <label>URL <input name="url" required placeholder="https://example.com?utm_source=test"></label>
    <label>Titel <input name="title" placeholder="Optional"></label>
    <label>Beschreibung <input name="description" placeholder="Optional"></label>
    <label>Tags <input name="tags" placeholder="proxmox, homelab"></label>
    <label>Collections <input name="collections" placeholder="Homelab/Proxmox"></label>
    <label><input name="favorite" type="checkbox" style="width:auto"> Favorit</label>
    <label><input name="pinned" type="checkbox" style="width:auto"> Pin</label>
    <button>Speichern</button>
  </form>

  <h2>Browser-Bookmarks importieren</h2>
  <form id="import-form">
    <label>Netscape Bookmark HTML <textarea name="html" rows="6" placeholder="Exportierte Bookmark-HTML hier einfuegen"></textarea></label>
    <button>Importieren</button>
  </form>

  <h2>Bookmarks</h2>
  <label>Suche <input id="search" placeholder="Titel, URL, Domain, Tag, Collection"></label>
  <div class="filters">
    <label><input id="filter-favorite" type="checkbox" style="width:auto"> Nur Favoriten</label>
    <label><input id="filter-pinned" type="checkbox" style="width:auto"> Nur Pins</label>
    <label>Domain <input id="filter-domain" placeholder="github.com"></label>
    <label>Tag <input id="filter-tag" placeholder="selfhost"></label>
    <label>Collection <input id="filter-collection" placeholder="Development"></label>
  </div>
  <button id="refresh">Aktualisieren</button>
  <section class="bulk-actions">
    <h3>Bulk-Aktionen</h3>
    <p class="muted"><span id="selected-count">0</span> Bookmarks ausgewaehlt.</p>
    <button id="select-visible" type="button">Sichtbare auswaehlen</button>
    <button id="clear-selection" type="button">Auswahl leeren</button>
    <form id="bulk-form">
      <label>Tags hinzufuegen <input name="add_tags" placeholder="selfhost, docs"></label>
      <label>Tags entfernen <input name="remove_tags" placeholder="inbox, old"></label>
      <label>Collections setzen <input name="set_collections" placeholder="Development, Reading"></label>
      <label>Favorit
        <select name="favorite">
          <option value="">Nicht aendern</option>
          <option value="true">Setzen</option>
          <option value="false">Entfernen</option>
        </select>
      </label>
      <label>Pin
        <select name="pinned">
          <option value="">Nicht aendern</option>
          <option value="true">Setzen</option>
          <option value="false">Entfernen</option>
        </select>
      </label>
      <button>Auf Auswahl anwenden</button>
      <button id="bulk-delete" type="button">Auswahl loeschen</button>
    </form>
  </section>
  <div id="bookmarks"></div>

  <h2>Dubletten Dry-Run</h2>
  <button id="dry-run">Dry-Run aktualisieren</button>
  <pre id="dedup-output">Noch keine Daten geladen.</pre>
  </main>

  <script>
    const bookmarksEl = document.querySelector('#bookmarks');
    const dedupOutput = document.querySelector('#dedup-output');
    const authPanel = document.querySelector('#auth-panel');
    const authTitle = document.querySelector('#auth-title');
    const authHelp = document.querySelector('#auth-help');
    const authError = document.querySelector('#auth-error');
    const setupForm = document.querySelector('#setup-form');
    const loginForm = document.querySelector('#login-form');
    const appEl = document.querySelector('#app');
    const userbar = document.querySelector('#userbar');
    const currentUser = document.querySelector('#current-user');
    const selectedIds = new Set();

    async function loadAuth() {
      authError.textContent = '';
      const response = await fetch('/api/me');
      const payload = await response.json();
      if (payload.authenticated) {
        showApp(payload.user);
        await refreshAll();
        return;
      }

      appEl.hidden = true;
      userbar.hidden = true;
      authPanel.hidden = false;
      if (payload.setup_required) {
        const statusResponse = await fetch('/api/setup/status');
        const status = await statusResponse.json();
        authTitle.textContent = 'Erstes Setup';
        authHelp.textContent = status.setup_token_required
          ? 'Setup-Token aus /etc/linkvault/linkvault.env eingeben und Admin anlegen.'
          : 'Admin anlegen. Fuer produktive Installationen sollte LINKVAULT_SETUP_TOKEN gesetzt sein.';
        setupForm.hidden = false;
        loginForm.hidden = true;
      } else {
        authTitle.textContent = 'Login';
        authHelp.textContent = 'Mit deinem LinkVault-Admin anmelden.';
        setupForm.hidden = true;
        loginForm.hidden = false;
      }
    }

    function showApp(user) {
      authPanel.hidden = true;
      appEl.hidden = false;
      userbar.hidden = false;
      currentUser.textContent = user ? user.username : '';
    }

    async function refreshBookmarks() {
      const query = document.querySelector('#search').value.trim();
      const params = new URLSearchParams();
      if (query) params.set('q', query);
      if (document.querySelector('#filter-favorite').checked) params.set('favorite', 'true');
      if (document.querySelector('#filter-pinned').checked) params.set('pinned', 'true');
      for (const [param, selector] of [
        ['domain', '#filter-domain'],
        ['tag', '#filter-tag'],
        ['collection', '#filter-collection']
      ]) {
        const value = document.querySelector(selector).value.trim();
        if (value) params.set(param, value);
      }
      const response = await fetch(`/api/bookmarks?${params.toString()}`);
      if (response.status === 401) {
        await loadAuth();
        return;
      }
      const payload = await response.json();
      bookmarksEl.innerHTML = '';
      selectedIds.clear();
      updateSelectedCount();
      for (const bookmark of payload.bookmarks) {
        const row = document.createElement('div');
        row.className = 'row';
        row.dataset.bookmarkId = bookmark.id;
        row.innerHTML = `
          <label><input data-role="select-bookmark" type="checkbox" style="width:auto"> Auswaehlen</label>
          <strong>${escapeHtml(bookmark.title)}</strong>
          <div><a href="${escapeAttr(bookmark.url)}">${escapeHtml(bookmark.url)}</a></div>
          <div class="muted">${escapeHtml(bookmark.domain)} · tags: ${escapeHtml(bookmark.tags.join(', ') || '-')} · collections: ${escapeHtml(bookmark.collections.join(', ') || '-')}</div>
          <div>${escapeHtml(bookmark.description || '')}</div>
          <div class="muted">notes: ${escapeHtml(bookmark.notes || '-')}</div>
          <div class="muted">favicon: ${escapeHtml(bookmark.favicon_url || '-')}</div>
          <div class="actions">
            <button data-action="favorite">${bookmark.favorite ? 'Favorit entfernen' : 'Favorit setzen'}</button>
            <button data-action="pin">${bookmark.pinned ? 'Pin entfernen' : 'Pin setzen'}</button>
            <button data-action="delete">Loeschen</button>
          </div>
          <details>
            <summary>Bearbeiten</summary>
            <form class="edit-form" data-role="edit">
              <label>URL <input name="url" required value="${escapeAttr(bookmark.url)}"></label>
              <label>Titel <input name="title" value="${escapeAttr(bookmark.title)}"></label>
              <label>Beschreibung <textarea name="description">${escapeHtml(bookmark.description || '')}</textarea></label>
              <label>Tags <input name="tags" value="${escapeAttr(bookmark.tags.join(', '))}"></label>
              <label>Collections <input name="collections" value="${escapeAttr(bookmark.collections.join(', '))}"></label>
              <label>Notizen <textarea name="notes">${escapeHtml(bookmark.notes || '')}</textarea></label>
              <button>Speichern</button>
            </form>
          </details>
        `;
        row.querySelector('[data-action="favorite"]').addEventListener('click', () => patchBookmark(bookmark.id, {favorite: !bookmark.favorite}));
        row.querySelector('[data-action="pin"]').addEventListener('click', () => patchBookmark(bookmark.id, {pinned: !bookmark.pinned}));
        row.querySelector('[data-action="delete"]').addEventListener('click', () => deleteBookmark(bookmark.id));
        row.querySelector('[data-role="select-bookmark"]').addEventListener('change', (event) => {
          if (event.target.checked) {
            selectedIds.add(bookmark.id);
          } else {
            selectedIds.delete(bookmark.id);
          }
          updateSelectedCount();
        });
        row.querySelector('[data-role="edit"]').addEventListener('submit', async (event) => {
          event.preventDefault();
          await patchBookmark(bookmark.id, Object.fromEntries(new FormData(event.target)));
        });
        bookmarksEl.appendChild(row);
      }
    }

    async function refreshDryRun() {
      const response = await fetch('/api/dedup/dry-run');
      if (response.status === 401) {
        await loadAuth();
        return;
      }
      dedupOutput.textContent = JSON.stringify(await response.json(), null, 2);
    }

    async function patchBookmark(id, data) {
      await fetch(`/api/bookmarks/${id}`, {
        method: 'PATCH',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      });
      await refreshAll();
    }

    async function deleteBookmark(id) {
      await fetch(`/api/bookmarks/${id}`, {method: 'DELETE'});
      await refreshAll();
    }

    async function refreshAll() {
      await refreshBookmarks();
      await refreshDryRun();
    }

    function updateSelectedCount() {
      document.querySelector('#selected-count').textContent = String(selectedIds.size);
    }

    function selectedBookmarkIds() {
      return Array.from(selectedIds);
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
    }

    function escapeAttr(value) {
      return escapeHtml(value).replace(/`/g, '&#96;');
    }

    document.querySelector('#bookmark-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.target));
      data.favorite = data.favorite === 'on';
      data.pinned = data.pinned === 'on';
      await fetch('/api/bookmarks', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      });
      event.target.reset();
      await refreshAll();
    });

    document.querySelector('#bulk-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const ids = selectedBookmarkIds();
      if (!ids.length) return;
      const formData = Object.fromEntries(new FormData(event.target));
      const payload = {ids};
      for (const key of ['add_tags', 'remove_tags', 'set_collections']) {
        if (formData[key] && String(formData[key]).trim()) payload[key] = formData[key];
      }
      if (formData.favorite) payload.favorite = formData.favorite;
      if (formData.pinned) payload.pinned = formData.pinned;
      await bulkUpdate(payload);
      event.target.reset();
    });

    document.querySelector('#bulk-delete').addEventListener('click', async () => {
      const ids = selectedBookmarkIds();
      if (!ids.length) return;
      await bulkUpdate({ids, delete: true});
    });

    document.querySelector('#select-visible').addEventListener('click', () => {
      document.querySelectorAll('[data-role="select-bookmark"]').forEach((checkbox) => {
        checkbox.checked = true;
        selectedIds.add(checkbox.closest('.row').dataset.bookmarkId);
      });
      updateSelectedCount();
    });

    document.querySelector('#clear-selection').addEventListener('click', () => {
      selectedIds.clear();
      document.querySelectorAll('[data-role="select-bookmark"]').forEach((checkbox) => {
        checkbox.checked = false;
      });
      updateSelectedCount();
    });

    async function bulkUpdate(payload) {
      await fetch('/api/bookmarks/bulk', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(payload)
      });
      await refreshAll();
    }

    setupForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      authError.textContent = '';
      const response = await fetch('/api/setup', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(Object.fromEntries(new FormData(event.target)))
      });
      const payload = await response.json();
      if (!response.ok) {
        authError.textContent = payload.error || 'Setup fehlgeschlagen.';
        return;
      }
      event.target.reset();
      showApp(payload.user);
      await refreshAll();
    });

    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      authError.textContent = '';
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(Object.fromEntries(new FormData(event.target)))
      });
      const payload = await response.json();
      if (!response.ok) {
        authError.textContent = payload.error || 'Login fehlgeschlagen.';
        return;
      }
      event.target.reset();
      showApp(payload.user);
      await refreshAll();
    });

    document.querySelector('#logout').addEventListener('click', async () => {
      await fetch('/api/logout', {method: 'POST'});
      await loadAuth();
    });

    document.querySelector('#import-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.target));
      await fetch('/api/import/browser-html', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      });
      event.target.reset();
      await refreshAll();
    });

    document.querySelector('#refresh').addEventListener('click', refreshBookmarks);
    document.querySelector('#dry-run').addEventListener('click', refreshDryRun);
    document.querySelector('#search').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-favorite').addEventListener('change', refreshBookmarks);
    document.querySelector('#filter-pinned').addEventListener('change', refreshBookmarks);
    document.querySelector('#filter-domain').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-tag').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-collection').addEventListener('input', refreshBookmarks);
    loadAuth();
  </script>
</body>
</html>"""


def get_query_param(params: dict[str, list[str]], key: str) -> str:
    return params.get(key, [""])[0].strip()


def optional_bool_query_param(params: dict[str, list[str]], key: str) -> bool | None:
    value = get_query_param(params, key).lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return None


def filters_from_query(params: dict[str, list[str]]) -> BookmarkFilters:
    return BookmarkFilters(
        favorite=optional_bool_query_param(params, "favorite"),
        pinned=optional_bool_query_param(params, "pinned"),
        domain=get_query_param(params, "domain"),
        tag=get_query_param(params, "tag"),
        collection=get_query_param(params, "collection"),
    )


def session_cookie_header(session_id: str) -> tuple[str, str]:
    return (
        "Set-Cookie",
        f"linkvault_session={session_id}; Path=/; Max-Age=2592000; HttpOnly; SameSite=Lax",
    )


def expired_session_cookie_header() -> tuple[str, str]:
    return (
        "Set-Cookie",
        "linkvault_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax",
    )


def main() -> None:
    config = load_config()
    server = ThreadingHTTPServer((config.host, config.port), LinkVaultHandler)
    print(f"LinkVault listening on http://{config.host}:{config.port}")
    print(f"LinkVault data path: {config.data_path}")
    server.serve_forever()


if __name__ == "__main__":
    main()
