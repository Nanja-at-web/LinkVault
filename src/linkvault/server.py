from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import __version__
from .store import BookmarkFilters, BookmarkStore


def make_store() -> BookmarkStore:
    data_path = Path(os.environ.get("LINKVAULT_DATA", "data/linkvault.sqlite3"))
    return BookmarkStore(data_path)


class LinkVaultHandler(BaseHTTPRequestHandler):
    server_version = f"LinkVault/{__version__}"

    def do_GET(self) -> None:
        store = make_store()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/healthz":
            self.send_json({"ok": True, "version": __version__})
        elif path == "/api/bookmarks":
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
            bookmark = store.get(path.rsplit("/", 1)[-1])
            if not bookmark:
                self.send_json({"error": "bookmark not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json(bookmark.to_dict())
        elif path == "/api/dedup":
            self.send_json({"groups": store.dedup_groups()})
        elif path == "/api/dedup/dry-run":
            self.send_json(store.dedup_dry_run())
        elif path == "/":
            self.send_html(index_html())
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        store = make_store()

        try:
            payload = self.read_json()
        except json.JSONDecodeError:
            self.send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            if path == "/api/bookmarks":
                bookmark = store.add(payload)
                self.send_json(bookmark.to_dict(), HTTPStatus.CREATED)
            elif path == "/api/import/browser-html":
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

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
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
  </style>
</head>
<body>
  <h1>LinkVault MVP</h1>
  <p>Links speichern, importieren, bearbeiten und Dubletten als Dry-Run pruefen.</p>

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
  <div id="bookmarks"></div>

  <h2>Dubletten Dry-Run</h2>
  <button id="dry-run">Dry-Run aktualisieren</button>
  <pre id="dedup-output">Noch keine Daten geladen.</pre>

  <script>
    const bookmarksEl = document.querySelector('#bookmarks');
    const dedupOutput = document.querySelector('#dedup-output');

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
      const payload = await response.json();
      bookmarksEl.innerHTML = '';
      for (const bookmark of payload.bookmarks) {
        const row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = `
          <strong>${escapeHtml(bookmark.title)}</strong>
          <div><a href="${escapeAttr(bookmark.url)}">${escapeHtml(bookmark.url)}</a></div>
          <div class="muted">${escapeHtml(bookmark.domain)} · tags: ${escapeHtml(bookmark.tags.join(', ') || '-')} · collections: ${escapeHtml(bookmark.collections.join(', ') || '-')}</div>
          <div>${escapeHtml(bookmark.description || '')}</div>
          <div class="muted">favicon: ${escapeHtml(bookmark.favicon_url || '-')}</div>
          <button data-action="favorite">${bookmark.favorite ? 'Favorit entfernen' : 'Favorit setzen'}</button>
          <button data-action="pin">${bookmark.pinned ? 'Pin entfernen' : 'Pin setzen'}</button>
          <button data-action="delete">Loeschen</button>
        `;
        row.querySelector('[data-action="favorite"]').addEventListener('click', () => patchBookmark(bookmark.id, {favorite: !bookmark.favorite}));
        row.querySelector('[data-action="pin"]').addEventListener('click', () => patchBookmark(bookmark.id, {pinned: !bookmark.pinned}));
        row.querySelector('[data-action="delete"]').addEventListener('click', () => deleteBookmark(bookmark.id));
        bookmarksEl.appendChild(row);
      }
    }

    async function refreshDryRun() {
      const response = await fetch('/api/dedup/dry-run');
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
    refreshAll();
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


def main() -> None:
    host = os.environ.get("LINKVAULT_HOST", "127.0.0.1")
    port = int(os.environ.get("LINKVAULT_PORT", "3080"))
    server = ThreadingHTTPServer((host, port), LinkVaultHandler)
    print(f"LinkVault listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
