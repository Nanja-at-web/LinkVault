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


def linkvault_identity() -> dict[str, Any]:
    return {
        "app": "LinkVault",
        "version": __version__,
        "health": "/healthz",
    }


class LinkVaultHandler(BaseHTTPRequestHandler):
    server_version = f"LinkVault/{__version__}"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.send_header("content-length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        store = make_store()
        auth_store = make_auth_store()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/healthz":
            self.send_json({"ok": True, "version": __version__})
        elif path == "/.well-known/linkvault":
            self.send_json(linkvault_identity())
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
        elif path == "/api/dedup/merges":
            if not self.require_auth(auth_store):
                return
            self.send_json({"events": store.merge_history()})
        elif path == "/api/tokens":
            if not self.require_session_auth(auth_store):
                return
            self.send_json({"tokens": [token.to_dict() for token in auth_store.list_api_tokens()]})
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
            elif path == "/api/tokens":
                if not self.require_session_auth(auth_store):
                    return
                self.send_json(auth_store.create_api_token(str(payload.get("name", ""))), HTTPStatus.CREATED)
            elif path == "/api/bookmarks/bulk":
                if not self.require_auth(auth_store):
                    return
                self.send_json(store.bulk_update(payload))
            elif path == "/api/dedup/merge":
                if not self.require_auth(auth_store):
                    return
                self.send_json(store.merge_duplicates(payload))
            elif path == "/api/bookmarks/preflight":
                if not self.require_auth(auth_store):
                    return
                self.send_json(
                    store.duplicate_preflight(
                        str(payload.get("url", "")),
                        exclude_id=str(payload.get("exclude_id", "")),
                    )
                )
            elif path == "/api/bookmarks/suggestions":
                if not self.require_auth(auth_store):
                    return
                self.send_json(store.category_suggestions(payload))
            elif path == "/api/bookmarks":
                if not self.require_auth(auth_store):
                    return
                if not to_bool(payload.get("allow_duplicate", False)):
                    preflight = store.duplicate_preflight(str(payload.get("url", "")))
                    if preflight["has_matches"]:
                        self.send_json(
                            {
                                "error": "duplicate candidate found",
                                "preflight": preflight,
                            },
                            HTTPStatus.CONFLICT,
                        )
                        return
                bookmark = store.add(payload)
                self.send_json(bookmark.to_dict(), HTTPStatus.CREATED)
            elif path == "/api/import/browser-html":
                if not self.require_auth(auth_store):
                    return
                html = str(payload.get("data") or payload.get("html") or "")
                self.send_json(store.import_browser_html(html), HTTPStatus.CREATED)
            elif path == "/api/import/browser-html/preview":
                if not self.require_auth(auth_store):
                    return
                html = str(payload.get("data") or payload.get("html") or "")
                self.send_json(store.preview_browser_html_import(html))
            elif path == "/api/import/chromium-json":
                if not self.require_auth(auth_store):
                    return
                data = str(payload.get("data", ""))
                self.send_json(store.import_chromium_json(data), HTTPStatus.CREATED)
            elif path == "/api/import/chromium-json/preview":
                if not self.require_auth(auth_store):
                    return
                data = str(payload.get("data", ""))
                self.send_json(store.preview_chromium_json_import(data))
            elif path == "/api/import/firefox-json":
                if not self.require_auth(auth_store):
                    return
                data = str(payload.get("data", ""))
                self.send_json(store.import_firefox_json(data), HTTPStatus.CREATED)
            elif path == "/api/import/firefox-json/preview":
                if not self.require_auth(auth_store):
                    return
                data = str(payload.get("data", ""))
                self.send_json(store.preview_firefox_json_import(data))
            elif path == "/api/import/safari-zip":
                if not self.require_auth(auth_store):
                    return
                data = str(payload.get("data", ""))
                self.send_json(store.import_safari_zip(data), HTTPStatus.CREATED)
            elif path == "/api/import/safari-zip/preview":
                if not self.require_auth(auth_store):
                    return
                data = str(payload.get("data", ""))
                self.send_json(store.preview_safari_zip_import(data))
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
        if path.startswith("/api/tokens/"):
            auth_store = make_auth_store()
            if not self.require_session_auth(auth_store):
                return
            deleted = auth_store.delete_api_token(path.rsplit("/", 1)[-1])
            if not deleted:
                self.send_json({"error": "api token not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"deleted": True})
            return
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
        return auth_store.user_for_session(self.session_cookie()) or auth_store.user_for_api_token(self.api_token())

    def require_auth(self, auth_store: AuthStore) -> User | None:
        user = self.current_user(auth_store)
        if user:
            return user
        self.send_json({"error": "authentication required"}, HTTPStatus.UNAUTHORIZED)
        return None

    def require_session_auth(self, auth_store: AuthStore) -> User | None:
        user = auth_store.user_for_session(self.session_cookie())
        if user:
            return user
        self.send_json({"error": "browser login required"}, HTTPStatus.UNAUTHORIZED)
        return None

    def api_token(self) -> str:
        authorization = self.headers.get("authorization", "").strip()
        if authorization.lower().startswith("bearer "):
            return authorization.split(" ", 1)[1].strip()
        return self.headers.get("x-linkvault-token", "").strip()

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
        self.send_cors_headers()
        for name, value in headers or []:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def send_cors_headers(self) -> None:
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("access-control-allow-headers", "content-type, authorization, x-linkvault-token")
        self.send_header("access-control-max-age", "86400")


def index_html() -> str:
    return """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LinkVault</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f4;
      --panel: #ffffff;
      --ink: #191b18;
      --muted: #62675f;
      --line: #d8ddd2;
      --accent: #1f7a5b;
      --accent-strong: #12543e;
      --warn: #9f3d26;
      --soft: #eef4ea;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.45;
    }
    a { color: var(--accent-strong); overflow-wrap: anywhere; }
    h1, h2, h3 { line-height: 1.15; margin: 0 0 .75rem; }
    h1 { font-size: 2rem; }
    h2 { font-size: 1.25rem; }
    h3 { font-size: 1rem; }
    input, textarea, button, select { font: inherit; }
    input, textarea, select {
      width: 100%;
      border: 1px solid #b9c0b1;
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: .65rem .7rem;
      margin: .25rem 0 .8rem;
    }
    textarea { min-height: 7rem; resize: vertical; }
    button {
      border: 1px solid #9aa392;
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      cursor: pointer;
      padding: .55rem .75rem;
      margin: .2rem .25rem .2rem 0;
    }
    button:hover { border-color: var(--accent); color: var(--accent-strong); }
    button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
    button.primary:hover { background: var(--accent-strong); color: #fff; }
    pre { background: #edf0ea; padding: 1rem; overflow: auto; border-radius: 6px; }
    label { display: block; font-weight: 650; }
    label.check {
      display: inline-flex;
      align-items: center;
      gap: .45rem;
      font-weight: 600;
      margin-right: .8rem;
    }
    label.check input, input[type="checkbox"] { width: auto; margin: 0; }
    .shell { max-width: 1240px; margin: 0 auto; padding: 1.25rem; }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 0 .9rem;
      border-bottom: 1px solid var(--line);
    }
    .subtitle { margin: 0; color: var(--muted); max-width: 58rem; }
    .nav {
      display: flex;
      flex-wrap: wrap;
      gap: .45rem;
      margin: 1rem 0;
    }
    .nav button {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: .45rem .65rem;
      margin: 0;
    }
    .nav button.active {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 1rem;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 1rem;
      box-shadow: 0 1px 2px rgba(25, 27, 24, .04);
    }
    .panel-header {
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: .75rem;
    }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: .75rem 1rem;
    }
    .full { grid-column: 1 / -1; }
    .muted { color: var(--muted); }
    .error { color: #b00020; }
    .actions, .inline-actions { display: flex; flex-wrap: wrap; gap: .35rem; align-items: center; }
    .edit-form { margin-top: .75rem; padding-top: .75rem; border-top: 1px solid var(--line); }
    .edit-form textarea { min-height: 4.5rem; }
    .notice {
      border: 1px solid #b8c6ae;
      border-radius: 8px;
      padding: .9rem;
      margin: 1rem 0 0;
      background: var(--soft);
    }
    .suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: .4rem;
      margin-top: .5rem;
    }
    .suggestions button {
      margin: 0;
      padding: .4rem .55rem;
    }
    .filters {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: .75rem 1rem;
      align-items: end;
    }
    .bookmark-controls {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(12rem, 16rem);
      gap: .75rem 1rem;
      align-items: end;
      margin-bottom: .75rem;
    }
    .drawer {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fafbf8;
      margin: .75rem 0;
      padding: .75rem;
    }
    .drawer summary {
      cursor: pointer;
      font-weight: 750;
    }
    .drawer-body { margin-top: .75rem; }
    .control-strip {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: .6rem;
      margin: .25rem 0 .75rem;
    }
    .filter-summary { color: var(--muted); font-size: .92rem; }
    .view-settings {
      display: grid;
      grid-template-columns: minmax(12rem, 18rem) minmax(0, 1fr);
      gap: .75rem 1rem;
      align-items: start;
    }
    .field-options {
      display: flex;
      flex-wrap: wrap;
      gap: .45rem .8rem;
      padding-top: .2rem;
    }
    .preference-status { min-height: 1.4rem; }
    .tab-panel[hidden] { display: none !important; }
    .stack { display: grid; gap: 1rem; }
    .mini-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: .75rem;
    }
    .mini-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .8rem;
      background: #fff;
    }
    .bulk-actions {
      margin: 0;
    }
    .bookmark-list { display: grid; gap: .75rem; }
    .bookmark-list.view-grid {
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      align-items: start;
    }
    .row {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .8rem;
    }
    .view-compact .row { padding: .6rem .7rem; }
    .view-compact .bookmark-layout {
      grid-template-columns: minmax(0, 1fr) auto;
      gap: .5rem;
    }
    .view-compact .bookmark-actions button { padding: .35rem .5rem; }
    .view-grid .row { min-height: 100%; }
    .view-grid .bookmark-layout {
      grid-template-columns: minmax(0, 1fr);
    }
    .view-grid .bookmark-side {
      justify-items: start;
      min-width: 0;
    }
    .bookmark-head {
      display: flex;
      justify-content: space-between;
      gap: .9rem;
      align-items: start;
    }
    .bookmark-main { min-width: 0; flex: 1; }
    .bookmark-title { font-size: 1rem; font-weight: 750; overflow-wrap: anywhere; margin-bottom: .15rem; }
    .bookmark-url { display: inline-block; margin: .1rem 0 .2rem; font-size: .95rem; }
    .select-pill {
      display: inline-flex;
      align-items: center;
      gap: .4rem;
      min-width: max-content;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: .25rem .45rem;
      background: #f7f9f5;
      font-size: .9rem;
      font-weight: 650;
    }
    .meta-line { color: var(--muted); font-size: .92rem; overflow-wrap: anywhere; }
    .description { margin: .45rem 0; font-size: .95rem; }
    .badge {
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: .1rem .4rem;
      margin: .15rem .2rem .15rem 0;
      font-size: .85rem;
      background: #f7f9f5;
    }
    .bookmark-layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: .8rem;
      align-items: start;
    }
    .bookmark-side {
      display: grid;
      gap: .4rem;
      justify-items: end;
      min-width: 9.5rem;
    }
    .bookmark-actions { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .45rem; }
    .bookmark-actions button { margin: 0; padding: .45rem .6rem; }
    .bookmark-meta { display: grid; gap: .15rem; }
    .duplicate-match { border-top: 1px solid var(--line); padding: .9rem 0; }
    .dedup-group { border-top: 1px solid var(--line); padding: 1rem 0; }
    .dedup-header { display: flex; justify-content: space-between; gap: 1rem; align-items: start; margin-bottom: .8rem; }
    .dedup-title { margin: 0; }
    .dedup-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: .75rem; }
    .dedup-box { border: 1px solid var(--line); border-radius: 8px; padding: .8rem; background: #fff; }
    .dedup-winner { border-color: #8cad7a; background: #fbfdf8; }
    .dedup-item { border-top: 1px solid var(--line); padding-top: .65rem; margin-top: .65rem; }
    .dedup-item:first-child { border-top: 0; padding-top: 0; margin-top: 0; }
    .dedup-diff { margin-top: .85rem; }
    .diff-row { display: grid; grid-template-columns: minmax(8rem, .7fr) minmax(0, 1.3fr); gap: .75rem; padding: .55rem 0; border-top: 1px solid var(--line); }
    .diff-row:first-child { border-top: 0; }
    .diff-values { display: grid; gap: .35rem; }
    .diff-winner { font-weight: 700; }
    .history-list { display: grid; gap: .6rem; }
    .empty { color: var(--muted); border: 1px dashed #aeb7a6; border-radius: 8px; padding: 1rem; background: #fafbf8; }
    .shortcut-hint { color: var(--muted); margin: .35rem 0 0; font-size: .9rem; }
    @media (max-width: 760px) {
      .shell { padding: .75rem; }
      .toolbar, .panel-header { display: block; }
      .form-grid, .filters, .bookmark-controls, .view-settings { grid-template-columns: 1fr; }
      .bookmark-head, .bookmark-layout { display: block; }
      .bookmark-list.view-grid { grid-template-columns: 1fr; }
      .bookmark-side { justify-items: start; min-width: 0; margin-top: .65rem; }
      .select-pill { margin-top: .65rem; }
      h1 { font-size: 1.6rem; }
    }
    [hidden] { display: none !important; }
  </style>
</head>
<body>
<div class="shell">
  <div class="toolbar">
    <div>
      <h1>LinkVault MVP</h1>
      <p class="subtitle">Links speichern, importieren, bearbeiten und Dubletten sicher zusammenfuehren.</p>
      <p class="shortcut-hint">Shortcuts: Ctrl/Cmd+K Suche, N Speichern, I Import, D Dubletten, B Bookmarks.</p>
    </div>
    <div id="userbar" hidden>
      <span id="current-user"></span>
      <button id="logout" type="button">Logout</button>
    </div>
  </div>

  <section id="auth-panel" class="panel">
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

  <nav id="app-nav" class="nav" hidden>
    <button type="button" data-tab-trigger="save">Speichern</button>
    <button type="button" data-inbox-trigger>Inbox</button>
    <button type="button" data-tab-trigger="import">Import</button>
    <button type="button" data-tab-trigger="bookmarks">Bookmarks</button>
    <button type="button" data-tab-trigger="dedup">Dubletten</button>
    <button type="button" data-tab-trigger="operations">Betrieb</button>
  </nav>

  <main id="app" class="workspace" hidden>
  <section id="save" class="panel tab-panel" data-tab-panel="save">
    <div class="panel-header">
      <div>
        <h2>Bookmark speichern</h2>
        <p class="subtitle">Beim Speichern prueft LinkVault zuerst auf moegliche Dubletten.</p>
      </div>
    </div>
    <form id="bookmark-form" class="form-grid">
      <label class="full">URL <input name="url" required placeholder="https://example.com?utm_source=test"></label>
      <label>Titel <input name="title" placeholder="Optional"></label>
      <label>Beschreibung <input name="description" placeholder="Optional"></label>
      <label>Tags <input name="tags" placeholder="proxmox, homelab"></label>
      <label>Collections <input name="collections" placeholder="Homelab/Proxmox"></label>
      <div class="full inline-actions">
        <label class="check"><input name="favorite" type="checkbox"> Favorit</label>
        <label class="check"><input name="pinned" type="checkbox"> Pin</label>
        <button id="suggest-categories" type="button">Vorschlaege</button>
        <button class="primary">Speichern</button>
      </div>
    </form>
    <section id="category-suggestions" class="notice" hidden></section>
    <section id="duplicate-preflight" class="notice" hidden></section>
  </section>

  <section id="import" class="panel tab-panel" data-tab-panel="import" hidden>
    <h2>Browser-Bookmarks importieren</h2>
    <form id="import-form">
      <label>Format
        <select name="format">
          <option value="browser-html">Browser-HTML / Netscape</option>
          <option value="chromium-json">Chromium-JSON: Chrome, Edge, Brave, Vivaldi, Opera</option>
          <option value="firefox-json">Firefox-JSON: bookmarks backup</option>
          <option value="safari-zip">Safari-ZIP: archive with Bookmarks.html</option>
        </select>
      </label>
      <label class="full">Importdatei <input name="file" type="file"></label>
      <label class="full">Importdaten <textarea name="data" rows="8" placeholder="Bookmark-HTML, Chromium-JSON oder Firefox-JSON hier einfuegen. Safari-ZIP bitte als Datei auswaehlen."></textarea></label>
      <div class="inline-actions">
        <button id="import-preview-button" type="button">Vorschau pruefen</button>
        <button>Importieren</button>
      </div>
    </form>
    <section id="import-preview-output" class="notice" hidden></section>
  </section>

  <section id="bookmarks-panel" class="panel tab-panel" data-tab-panel="bookmarks" hidden>
    <div class="panel-header">
      <div>
        <h2>Bookmarks</h2>
        <p class="subtitle"><span id="bookmark-count">0</span> Treffer. Standardansicht zeigt aktive Bookmarks; gemergte Dubletten lassen sich optional einblenden.</p>
      </div>
      <button id="refresh" type="button">Aktualisieren</button>
    </div>
    <div class="bookmark-controls">
      <label>Suche <input id="search" placeholder="Titel, URL, Domain, Tag, Collection"></label>
      <label>Status
        <select id="filter-status">
          <option value="active">Aktive Bookmarks</option>
          <option value="merged_duplicate">Gemergte Dubletten</option>
          <option value="all">Alle anzeigen</option>
        </select>
      </label>
    </div>

    <div class="control-strip">
      <span id="filter-summary" class="filter-summary">Keine Zusatzfilter aktiv.</span>
      <span class="inline-actions">
        <button id="show-inbox" type="button">Inbox anzeigen</button>
        <button id="show-active" type="button">Alle aktiven</button>
      </span>
      <span class="filter-summary"><span id="selected-count">0</span> ausgewaehlt</span>
    </div>

    <details class="drawer" id="view-drawer">
      <summary>Ansicht</summary>
      <div class="drawer-body view-settings">
        <label>Layout
          <select id="bookmark-view">
            <option value="compact">Compact List</option>
            <option value="detailed">Detailed List</option>
            <option value="grid">Grid/Card</option>
          </select>
        </label>
        <div>
          <strong>Anzeigen</strong>
          <div class="field-options">
            <label class="check"><input type="checkbox" data-display-field="title"> Titel</label>
            <label class="check"><input type="checkbox" data-display-field="description"> Beschreibung</label>
            <label class="check"><input type="checkbox" data-display-field="notes"> Notizen</label>
            <label class="check"><input type="checkbox" data-display-field="tags"> Tags</label>
            <label class="check"><input type="checkbox" data-display-field="collections"> Collections</label>
            <label class="check"><input type="checkbox" data-display-field="domain"> Domain</label>
            <label class="check"><input type="checkbox" data-display-field="date"> Datum</label>
            <label class="check"><input type="checkbox" data-display-field="favoritePin"> Favorit/Pin</label>
            <label class="check"><input type="checkbox" data-display-field="status"> Status</label>
          </div>
          <div class="inline-actions">
            <button id="save-view-preferences" type="button">Als Standard speichern</button>
            <button id="reset-view-preferences" type="button">Zuruecksetzen</button>
          </div>
          <p id="view-preference-status" class="muted preference-status"></p>
        </div>
      </div>
    </details>

    <details class="drawer" id="filter-drawer">
      <summary>Filter</summary>
      <div class="drawer-body filters">
        <label class="check"><input id="filter-favorite" type="checkbox"> Nur Favoriten</label>
        <label class="check"><input id="filter-pinned" type="checkbox"> Nur Pins</label>
        <label>Domain <input id="filter-domain" placeholder="github.com"></label>
        <label>Tag <input id="filter-tag" placeholder="selfhost"></label>
        <label>Collection <input id="filter-collection" placeholder="Development"></label>
      </div>
    </details>

    <details class="drawer" id="bulk-drawer">
      <summary>Bulk-Aktionen</summary>
      <section id="bulk" class="bulk-actions drawer-body">
        <div class="inline-actions">
          <button id="select-visible" type="button">Sichtbare auswaehlen</button>
          <button id="clear-selection" type="button">Auswahl leeren</button>
        </div>
        <form id="bulk-form" class="form-grid">
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
          <div class="full inline-actions">
            <button>Auf Auswahl anwenden</button>
            <button id="bulk-delete" type="button">Auswahl loeschen</button>
          </div>
        </form>
      </section>
    </details>
    <div id="bookmarks" class="bookmark-list"></div>
  </section>

  <section id="dedup" class="panel tab-panel" data-tab-panel="dedup" hidden>
    <div class="panel-header">
      <div>
        <h2>Dubletten</h2>
        <p class="subtitle">Gewinner pruefen, Daten uebernehmen und Verlierer ohne hartes Loeschen markieren.</p>
      </div>
      <button id="dry-run" type="button">Dry-Run aktualisieren</button>
    </div>
    <div id="dedup-output" class="notice">Noch keine Daten geladen.</div>
  </section>

  <section id="operations" class="panel tab-panel" data-tab-panel="operations" hidden>
    <div class="panel-header">
      <div>
        <h2>Betrieb</h2>
        <p class="subtitle">Gesundheit, Setup-Status und letzte Merge-Aktionen an einem Ort.</p>
      </div>
      <button id="refresh-operations" type="button">Aktualisieren</button>
    </div>
    <div class="stack">
      <div class="mini-grid" id="operations-status"></div>
      <section class="mini-card">
        <h3>API-Token fuer Companion Extension</h3>
        <p class="muted">Token erlauben Import und Automatisierung ohne Browser-Login. Der Klartext wird nur einmal angezeigt.</p>
        <form id="api-token-form" class="inline-actions">
          <label>Name <input name="name" placeholder="Firefox auf MacBook" required></label>
          <button>Token erstellen</button>
        </form>
        <div id="api-token-created" class="notice" hidden></div>
        <div id="api-token-list" class="history-list"></div>
      </section>
      <section class="mini-card">
        <h3>Letzte Merge-Aktionen</h3>
        <div id="merge-history" class="history-list"></div>
      </section>
    </div>
  </section>
  </main>
</div>

  <script>
    const bookmarksEl = document.querySelector('#bookmarks');
    const dedupOutput = document.querySelector('#dedup-output');
    const duplicatePreflight = document.querySelector('#duplicate-preflight');
    const categorySuggestions = document.querySelector('#category-suggestions');
    const importPreviewOutput = document.querySelector('#import-preview-output');
    const authPanel = document.querySelector('#auth-panel');
    const authTitle = document.querySelector('#auth-title');
    const authHelp = document.querySelector('#auth-help');
    const authError = document.querySelector('#auth-error');
    const setupForm = document.querySelector('#setup-form');
    const loginForm = document.querySelector('#login-form');
    const appEl = document.querySelector('#app');
    const appNav = document.querySelector('#app-nav');
    const userbar = document.querySelector('#userbar');
    const currentUser = document.querySelector('#current-user');
    const bookmarkCount = document.querySelector('#bookmark-count');
    const filterSummary = document.querySelector('#filter-summary');
    const operationsStatus = document.querySelector('#operations-status');
    const mergeHistoryEl = document.querySelector('#merge-history');
    const apiTokenForm = document.querySelector('#api-token-form');
    const apiTokenCreated = document.querySelector('#api-token-created');
    const apiTokenList = document.querySelector('#api-token-list');
    const selectedIds = new Set();
    let activeTab = 'bookmarks';
    const defaultViewPreferences = {
      view: 'compact',
      fields: {
        title: true,
        description: false,
        notes: false,
        tags: true,
        collections: true,
        domain: true,
        date: false,
        favoritePin: true,
        status: true
      }
    };
    const viewFieldPresets = {
      compact: {
        title: true,
        description: false,
        notes: false,
        tags: true,
        collections: true,
        domain: true,
        date: false,
        favoritePin: true,
        status: true
      },
      detailed: {
        title: true,
        description: true,
        notes: true,
        tags: true,
        collections: true,
        domain: true,
        date: true,
        favoritePin: true,
        status: true
      },
      grid: {
        title: true,
        description: true,
        notes: false,
        tags: true,
        collections: true,
        domain: true,
        date: false,
        favoritePin: true,
        status: true
      }
    };
    let viewPreferences = clonePreferences(defaultViewPreferences);

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
      appNav.hidden = true;
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
      appNav.hidden = false;
      userbar.hidden = false;
      currentUser.textContent = user ? user.username : '';
      loadViewPreferences();
      setActiveTab(activeTab);
    }

    function setActiveTab(tab) {
      activeTab = tab;
      document.querySelectorAll('[data-tab-panel]').forEach((panel) => {
        panel.hidden = panel.dataset.tabPanel !== tab;
      });
      document.querySelectorAll('[data-tab-trigger]').forEach((button) => {
        button.classList.toggle('active', button.dataset.tabTrigger === tab);
      });
    }

    function clearBookmarkFilters() {
      document.querySelector('#search').value = '';
      document.querySelector('#filter-favorite').checked = false;
      document.querySelector('#filter-pinned').checked = false;
      document.querySelector('#filter-domain').value = '';
      document.querySelector('#filter-tag').value = '';
      document.querySelector('#filter-collection').value = '';
      document.querySelector('#filter-status').value = 'active';
    }

    async function showInbox() {
      setActiveTab('bookmarks');
      clearBookmarkFilters();
      document.querySelector('#filter-collection').value = 'Inbox';
      await refreshBookmarks();
    }

    async function showActiveBookmarks() {
      setActiveTab('bookmarks');
      clearBookmarkFilters();
      await refreshBookmarks();
    }

    async function refreshBookmarks() {
      const query = document.querySelector('#search').value.trim();
      const params = new URLSearchParams();
      if (query) params.set('q', query);
      if (document.querySelector('#filter-favorite').checked) params.set('favorite', 'true');
      if (document.querySelector('#filter-pinned').checked) params.set('pinned', 'true');
      const status = document.querySelector('#filter-status').value;
      if (status && status !== 'active') params.set('status', status);
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
      updateFilterSummary(query, status);
      bookmarksEl.innerHTML = '';
      bookmarksEl.className = `bookmark-list view-${viewPreferences.view}`;
      selectedIds.clear();
      updateSelectedCount();
      bookmarkCount.textContent = String(payload.bookmarks.length);
      if (!payload.bookmarks.length) {
        bookmarksEl.innerHTML = '<div class="empty">Keine Bookmarks fuer diese Suche gefunden.</div>';
        return;
      }
      for (const bookmark of payload.bookmarks) {
        const row = document.createElement('div');
        row.className = 'row';
        row.dataset.bookmarkId = bookmark.id;
        const showTitle = shouldShowField('title');
        const showDescription = shouldShowField('description');
        const showNotes = shouldShowField('notes');
        const showTags = shouldShowField('tags');
        const showCollections = shouldShowField('collections');
        const showDomain = shouldShowField('domain');
        const showDate = shouldShowField('date');
        const showFavoritePin = shouldShowField('favoritePin');
        const showStatus = shouldShowField('status');
        row.innerHTML = `
          <div class="bookmark-layout">
            <div class="bookmark-main">
              ${showTitle ? `<div class="bookmark-title">${escapeHtml(bookmark.title)}</div>` : ''}
              <a class="bookmark-url" href="${escapeAttr(bookmark.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(bookmark.url)}</a>
              <div class="bookmark-meta">
                ${showDomain ? `<div class="meta-line">${escapeHtml(bookmark.domain || 'ohne Domain')}</div>` : ''}
                ${showDate ? `<div class="meta-line">Hinzugefuegt: ${escapeHtml(shortDate(bookmark.created_at))} · Geaendert: ${escapeHtml(shortDate(bookmark.updated_at))}</div>` : ''}
                ${showFavoritePin ? `<div class="meta-line">${bookmark.favorite ? 'Favorit' : 'kein Favorit'} · ${bookmark.pinned ? 'Pin' : 'kein Pin'}</div>` : ''}
                ${showStatus && bookmark.status !== 'active' ? `<div class="meta-line">Status: ${escapeHtml(bookmark.status)}${bookmark.merged_into ? ` · zusammengefuehrt in ${escapeHtml(bookmark.merged_into.slice(0, 8))}` : ''}</div>` : ''}
              </div>
              <div>${showTags ? renderBadges('tag', bookmark.tags) : ''}${showCollections ? renderBadges('collection', bookmark.collections) : ''}</div>
              ${showDescription && bookmark.description ? `<p class="description">${escapeHtml(bookmark.description)}</p>` : ''}
              ${showNotes && bookmark.notes ? `<div class="meta-line">Notizen: ${escapeHtml(bookmark.notes)}</div>` : ''}
            </div>
            <div class="bookmark-side">
              <label class="select-pill"><input data-role="select-bookmark" type="checkbox"> Auswaehlen</label>
              <div class="bookmark-actions">
                <button data-action="favorite">${bookmark.favorite ? 'Favorit aus' : 'Favorit an'}</button>
                <button data-action="pin">${bookmark.pinned ? 'Pin aus' : 'Pin an'}</button>
                <button data-action="delete">Loeschen</button>
              </div>
            </div>
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
      renderDedupDryRun(await response.json());
    }

    async function refreshOperations() {
      const [healthResponse, setupResponse, mergeResponse, tokenResponse] = await Promise.all([
        fetch('/healthz'),
        fetch('/api/setup/status'),
        fetch('/api/dedup/merges'),
        fetch('/api/tokens')
      ]);
      if (mergeResponse.status === 401 || tokenResponse.status === 401) {
        await loadAuth();
        return;
      }
      const health = await healthResponse.json();
      const setup = await setupResponse.json();
      const mergeHistory = await mergeResponse.json();
      const tokens = await tokenResponse.json();
      renderOperations(health, setup, mergeHistory.events || [], tokens.tokens || []);
    }

    function renderDedupDryRun(payload) {
      if (!payload.group_count) {
        dedupOutput.textContent = 'Keine Dubletten gefunden.';
        return;
      }
      dedupOutput.innerHTML = `<p><strong>${payload.group_count}</strong> Dublettengruppe(n) gefunden. Gewinner werden aktualisiert, Verlierer bleiben erhalten und werden nur als Dublette markiert.</p>`;
      for (const group of payload.groups) {
        const losers = group.items.filter((item) => item.id !== group.winner.id);
        const section = document.createElement('section');
        section.className = 'dedup-group';
        section.innerHTML = `
          <div class="dedup-header">
            <div>
              <h3 class="dedup-title">${escapeHtml(group.reason)}</h3>
              <p class="muted">${escapeHtml(group.normalized_url)} · Score ${group.score} · ${group.items.length} Bookmarks</p>
            </div>
            <button type="button" class="primary" data-merge>Zusammenfuehren</button>
          </div>
          <div class="dedup-grid">
            <div class="dedup-box dedup-winner">
              <strong>Gewinner-Vorschlag</strong>
              ${renderDedupItem(group.winner, true)}
            </div>
            <div class="dedup-box">
              <strong>Verlierer werden markiert</strong>
              ${losers.map((item) => renderDedupItem(item, false)).join('')}
            </div>
            <div class="dedup-box">
              <strong>Merge-Aktion</strong>
              ${renderMergePlan(group.merge_plan, losers.length)}
            </div>
          </div>
          <details class="dedup-diff" open>
            <summary>Unterschiede: Titel, Beschreibung, Tags, Collections, Notizen, Favorite/Pin</summary>
            ${renderDifferences(group.differences, group.winner.id)}
          </details>
        `;
        section.querySelectorAll('[data-open-item]').forEach((button) => {
          button.addEventListener('click', () => openBookmark(button.dataset.openItem));
        });
        section.querySelector('[data-merge]').addEventListener('click', async () => {
          await mergeDuplicates(group.merge_plan.winner_id, group.merge_plan.loser_ids);
        });
        dedupOutput.appendChild(section);
      }
    }

    function renderDedupItem(bookmark, isWinner) {
      return `
        <div class="dedup-item">
          <p><strong>${escapeHtml(bookmark.title || bookmark.url)}</strong></p>
          <p><a href="${escapeAttr(bookmark.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(bookmark.url)}</a></p>
          <p class="muted">${escapeHtml(bookmark.domain || 'ohne Domain')} · ${bookmark.favorite ? 'Favorit' : 'kein Favorit'} · ${bookmark.pinned ? 'Pin' : 'kein Pin'}</p>
          <p>${renderBadges('tag', bookmark.tags)}${renderBadges('collection', bookmark.collections)}</p>
          ${bookmark.description ? `<p>${escapeHtml(bookmark.description)}</p>` : ''}
          ${bookmark.notes ? `<p class="muted">Notizen: ${escapeHtml(bookmark.notes)}</p>` : ''}
          <button type="button" data-open-item="${escapeAttr(bookmark.id)}">${isWinner ? 'Gewinner oeffnen' : 'Verlierer oeffnen'}</button>
        </div>
      `;
    }

    function renderMergePlan(plan, loserCount) {
      return `
        <p>${loserCount} Verlierer werden als <code>merged_duplicate</code> markiert.</p>
        <p>Tags danach: ${escapeHtml(plan.move_tags.join(', ') || '-')}</p>
        <p>Collections danach: ${escapeHtml(plan.move_collections.join(', ') || '-')}</p>
        <p>Notizen: Verlierer-Notizen werden angehaengt.</p>
        <p>Favorite: ${plan.keep_favorite ? 'ja' : 'nein'} · Pin: ${plan.keep_pinned ? 'ja' : 'nein'}</p>
        <p><strong>Hartes Loeschen: nein.</strong> Originaldaten bleiben erhalten.</p>
      `;
    }

    function renderDifferences(differences, winnerId) {
      if (!differences.length) return '<p>Keine Feldunterschiede. Der Merge markiert trotzdem die doppelten URLs.</p>';
      return differences.map((difference) => `
        <div class="diff-row">
          <strong>${escapeHtml(fieldLabel(difference.field))}</strong>
          <div class="diff-values">
            ${difference.values.map((item) => `
              <div class="${item.id === winnerId ? 'diff-winner' : ''}">
                <code>${escapeHtml(item.id.slice(0, 8))}</code>${item.id === winnerId ? ' Gewinner' : ' Verlierer'}: ${escapeHtml(formatValue(item.value))}
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    }

    function fieldLabel(field) {
      return {
        url: 'URL',
        title: 'Titel',
        description: 'Beschreibung',
        tags: 'Tags',
        collections: 'Collections',
        notes: 'Notizen',
        favorite: 'Favorite',
        pinned: 'Pin'
      }[field] || field;
    }

    function formatValue(value) {
      return Array.isArray(value) ? value.join(', ') : String(value || '-');
    }

    function renderBadges(kind, values) {
      if (!values.length) return '';
      const prefix = kind === 'tag' ? '#' : '';
      return values.map((value) => `<span class="badge">${prefix}${escapeHtml(value)}</span>`).join('');
    }

    async function loadCategorySuggestions(form) {
      const formData = Object.fromEntries(new FormData(form));
      const response = await fetch('/api/bookmarks/suggestions', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(formData)
      });
      if (response.status === 401) {
        await loadAuth();
        return;
      }
      renderCategorySuggestions(await response.json(), form);
    }

    function renderCategorySuggestions(payload, form) {
      categorySuggestions.hidden = false;
      const tagButtons = payload.suggested_tags.map((tag) => `<button type="button" data-suggest-kind="tags" data-suggest-value="${escapeAttr(tag)}">#${escapeHtml(tag)}</button>`).join('');
      const collectionButtons = payload.suggested_collections.map((collection) => `<button type="button" data-suggest-kind="collections" data-suggest-value="${escapeAttr(collection)}">${escapeHtml(collection)}</button>`).join('');
      categorySuggestions.innerHTML = `
        <h3>Sortier-Vorschlaege</h3>
        <p class="muted">${escapeHtml(payload.domain || 'ohne Domain')} · ${payload.reasons.map(escapeHtml).join(' · ') || 'Noch keine Regel gefunden.'}</p>
        <p>Neue Links ohne Collection landen automatisch in <strong>Inbox</strong>.</p>
        <div class="suggestions">${tagButtons || '<span class="muted">Keine neuen Tags.</span>'}</div>
        <div class="suggestions">${collectionButtons || '<span class="muted">Keine neuen Collections.</span>'}</div>
      `;
      categorySuggestions.querySelectorAll('[data-suggest-kind]').forEach((button) => {
        button.addEventListener('click', () => {
          addCommaValue(form.elements[button.dataset.suggestKind], button.dataset.suggestValue);
        });
      });
    }

    function addCommaValue(input, value) {
      const values = input.value.split(',').map((item) => item.trim()).filter(Boolean);
      if (!values.includes(value)) values.push(value);
      input.value = values.join(', ');
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

    async function mergeDuplicates(winnerId, loserIds) {
      if (!loserIds.length) return;
      await fetch('/api/dedup/merge', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({winner_id: winnerId, loser_ids: loserIds})
      });
      await refreshAll();
    }

    async function refreshAll() {
      await refreshBookmarks();
      await refreshDryRun();
      await refreshOperations();
    }

    function renderImportPreview(payload) {
      importPreviewOutput.hidden = false;
      if (!payload.total) {
        importPreviewOutput.innerHTML = '<strong>Keine Bookmarks im HTML gefunden.</strong>';
        return;
      }

      const rows = payload.records.map((record) => {
        const status = {
          create: 'Neu',
          duplicate_existing: 'Existiert schon',
          duplicate_in_import: 'Doppelt im Import',
          invalid_skipped: 'Uebersprungen'
        }[record.action] || record.action;
        const suggestionTags = (record.suggestions?.suggested_tags || []).map((tag) => `#${escapeHtml(tag)}`).join(' ');
        const suggestionCollections = (record.suggestions?.suggested_collections || []).map(escapeHtml).join(', ');
        const duplicateHint = record.duplicate_bookmark
          ? `<p class="muted">Vorhanden: ${escapeHtml(record.duplicate_bookmark.title)} · ${escapeHtml(record.duplicate_bookmark.url)}</p>`
          : record.duplicate_of_index
            ? `<p class="muted">Doppelt zu Import-Zeile ${record.duplicate_of_index}</p>`
            : '';
        const errorHint = record.error ? `<p class="muted">Grund: ${escapeHtml(record.error)}</p>` : '';
        return `
          <div class="mini-card">
            <p><strong>${escapeHtml(status)}</strong> · ${escapeHtml(record.title || record.url)}</p>
            <p><a href="${escapeAttr(record.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(record.url)}</a></p>
            <p class="muted">${escapeHtml(record.domain || '-')} · Collections: ${escapeHtml((record.collections || []).join(', ') || '-')} · Tags: ${escapeHtml((record.tags || []).join(', ') || '-')}</p>
            ${duplicateHint}
            ${errorHint}
            <p class="muted">Vorschlaege: ${suggestionTags || 'keine neuen Tags'} · ${suggestionCollections || 'keine neuen Collections'}</p>
          </div>
        `;
      }).join('');

      importPreviewOutput.innerHTML = `
        <h3>Import-Vorschau</h3>
        <p>${payload.total} gefunden · ${payload.create} neu · ${payload.duplicate_existing} existieren schon · ${payload.duplicate_in_import} doppelt im Import · ${payload.invalid_skipped || 0} ungueltig/intern uebersprungen</p>
        <div class="stack">${rows}</div>
      `;
    }

    function renderImportResult(payload) {
      importPreviewOutput.hidden = false;
      importPreviewOutput.innerHTML = `
        <h3>Import abgeschlossen</h3>
        <p>${payload.created} neue Bookmarks importiert. ${payload.duplicates_skipped} Dubletten uebersprungen. ${payload.invalid_skipped || 0} ungueltige/interne URLs uebersprungen.</p>
      `;
    }

    function importEndpoint(format, preview = false) {
      const endpoints = {
        'browser-html': '/api/import/browser-html',
        'chromium-json': '/api/import/chromium-json',
        'firefox-json': '/api/import/firefox-json',
        'safari-zip': '/api/import/safari-zip'
      };
      const base = endpoints[format] || '/api/import/browser-html';
      return preview ? `${base}/preview` : base;
    }

    async function importPayloadFromForm(form) {
      const data = Object.fromEntries(new FormData(form));
      const file = form.elements.file?.files?.[0];
      if (file) {
        data.data = data.format === 'safari-zip'
          ? await readFileAsBase64(file)
          : await file.text();
      }
      delete data.file;
      return data;
    }

    function readFileAsBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = String(reader.result || '');
          resolve(result.includes(',') ? result.split(',', 2)[1] : result);
        };
        reader.onerror = () => reject(reader.error || new Error('Datei konnte nicht gelesen werden.'));
        reader.readAsDataURL(file);
      });
    }

    function renderOperations(health, setup, mergeEvents, apiTokens) {
      operationsStatus.innerHTML = `
        <div class="mini-card">
          <h3>Health</h3>
          <p><strong>${health.ok ? 'OK' : 'Fehler'}</strong></p>
          <p class="muted">Version ${escapeHtml(health.version || '-')}</p>
        </div>
        <div class="mini-card">
          <h3>Setup</h3>
          <p><strong>${setup.setup_required ? 'Erforderlich' : 'Abgeschlossen'}</strong></p>
          <p class="muted">Setup-Token Pflicht: ${setup.setup_token_required ? 'ja' : 'nein'}</p>
        </div>
        <div class="mini-card">
          <h3>Dubletten-Merges</h3>
          <p><strong>${mergeEvents.length}</strong> letzte Ereignisse</p>
          <p class="muted">Nicht-destruktive Merge-Historie</p>
        </div>
        <div class="mini-card">
          <h3>API-Token</h3>
          <p><strong>${apiTokens.length}</strong> aktiv</p>
          <p class="muted">Fuer Extension, Importer und Automatisierung</p>
        </div>
      `;

      renderApiTokens(apiTokens);

      if (!mergeEvents.length) {
        mergeHistoryEl.innerHTML = '<div class="empty">Noch keine Merge-Aktionen vorhanden.</div>';
        return;
      }

      mergeHistoryEl.innerHTML = mergeEvents.map((event) => `
        <div class="mini-card">
          <p><strong>${escapeHtml(event.winner_after.title || event.winner_after.url)}</strong></p>
          <p class="muted">Gewinner ${escapeHtml(event.winner_id.slice(0, 8))} · ${event.loser_ids.length} Verlierer · ${escapeHtml(event.created_at)}</p>
          <p>Tags: ${escapeHtml((event.winner_after.tags || []).join(', ') || '-')}</p>
          <p>Collections: ${escapeHtml((event.winner_after.collections || []).join(', ') || '-')}</p>
          <p>Notizen: ${escapeHtml(event.winner_after.notes || '-')}</p>
        </div>
      `).join('');
    }

    function renderApiTokens(tokens) {
      if (!tokens.length) {
        apiTokenList.innerHTML = '<div class="empty">Noch keine API-Token vorhanden.</div>';
        return;
      }
      apiTokenList.innerHTML = tokens.map((token) => `
        <div class="mini-card">
          <p><strong>${escapeHtml(token.name)}</strong></p>
          <p class="muted">Prefix ${escapeHtml(token.token_prefix)}... · erstellt ${escapeHtml(token.created_at)} · zuletzt genutzt ${escapeHtml(token.last_used_at || 'nie')}</p>
          <button type="button" data-delete-token="${escapeAttr(token.id)}">Token loeschen</button>
        </div>
      `).join('');
      apiTokenList.querySelectorAll('[data-delete-token]').forEach((button) => {
        button.addEventListener('click', async () => {
          await fetch(`/api/tokens/${button.dataset.deleteToken}`, {method: 'DELETE'});
          await refreshOperations();
        });
      });
    }

    function updateSelectedCount() {
      document.querySelector('#selected-count').textContent = String(selectedIds.size);
    }

    function updateFilterSummary(query, status) {
      const parts = [];
      if (query) parts.push(`Suche: ${query}`);
      if (status !== 'active') parts.push(`Status: ${status === 'all' ? 'alle' : 'gemergte Dubletten'}`);
      if (document.querySelector('#filter-favorite').checked) parts.push('Favoriten');
      if (document.querySelector('#filter-pinned').checked) parts.push('Pins');
      for (const [label, selector] of [
        ['Domain', '#filter-domain'],
        ['Tag', '#filter-tag'],
        ['Collection', '#filter-collection']
      ]) {
        const value = document.querySelector(selector).value.trim();
        if (value) parts.push(`${label}: ${value}`);
      }
      filterSummary.textContent = parts.length ? parts.join(' · ') : 'Keine Zusatzfilter aktiv.';
    }

    function clonePreferences(preferences) {
      return JSON.parse(JSON.stringify(preferences));
    }

    function viewPreferencesKey() {
      const username = currentUser.textContent || 'anonymous';
      return `linkvault.viewPreferences.${username}`;
    }

    function loadViewPreferences() {
      try {
        const saved = localStorage.getItem(viewPreferencesKey());
        viewPreferences = saved ? mergeViewPreferences(JSON.parse(saved)) : clonePreferences(defaultViewPreferences);
      } catch {
        viewPreferences = clonePreferences(defaultViewPreferences);
      }
      applyViewControls();
    }

    function mergeViewPreferences(saved) {
      return {
        view: ['compact', 'detailed', 'grid'].includes(saved?.view) ? saved.view : defaultViewPreferences.view,
        fields: {...defaultViewPreferences.fields, ...(saved?.fields || {})}
      };
    }

    function collectViewPreferences() {
      const fields = {};
      document.querySelectorAll('[data-display-field]').forEach((checkbox) => {
        fields[checkbox.dataset.displayField] = checkbox.checked;
      });
      return {
        view: document.querySelector('#bookmark-view').value,
        fields
      };
    }

    function applyViewControls() {
      document.querySelector('#bookmark-view').value = viewPreferences.view;
      document.querySelectorAll('[data-display-field]').forEach((checkbox) => {
        checkbox.checked = Boolean(viewPreferences.fields[checkbox.dataset.displayField]);
      });
      if (bookmarksEl) bookmarksEl.className = `bookmark-list view-${viewPreferences.view}`;
    }

    function applyViewFieldPreset(view) {
      const preset = viewFieldPresets[view] || viewFieldPresets.compact;
      document.querySelectorAll('[data-display-field]').forEach((checkbox) => {
        checkbox.checked = Boolean(preset[checkbox.dataset.displayField]);
      });
    }

    function shouldShowField(field) {
      return Boolean(viewPreferences.fields[field]);
    }

    function saveViewPreferences() {
      viewPreferences = collectViewPreferences();
      localStorage.setItem(viewPreferencesKey(), JSON.stringify(viewPreferences));
      document.querySelector('#view-preference-status').textContent = 'Ansicht als Standard gespeichert.';
      refreshBookmarks();
    }

    function resetViewPreferences() {
      viewPreferences = clonePreferences(defaultViewPreferences);
      localStorage.removeItem(viewPreferencesKey());
      applyViewControls();
      document.querySelector('#view-preference-status').textContent = 'Standardansicht wiederhergestellt.';
      refreshBookmarks();
    }

    function updateViewPreview(event) {
      if (event?.target?.id === 'bookmark-view') {
        applyViewFieldPreset(event.target.value);
      }
      viewPreferences = collectViewPreferences();
      document.querySelector('#view-preference-status').textContent = 'Vorschau aktiv. Mit "Als Standard speichern" dauerhaft merken.';
      refreshBookmarks();
    }

    function shortDate(value) {
      if (!value) return '-';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleDateString(undefined, {year: 'numeric', month: '2-digit', day: '2-digit'});
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
      const preflight = await duplicatePreflightFor(data.url);
      if (preflight.has_matches && !event.submitter?.dataset?.forceSave) {
        renderDuplicatePreflight(preflight, data, event.target);
        return;
      }
      duplicatePreflight.hidden = true;
      await fetch('/api/bookmarks', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      }).then(async (response) => {
        if (response.status === 409) {
          const payload = await response.json();
          renderDuplicatePreflight(payload.preflight, data, event.target);
          throw new Error('duplicate preflight');
        }
      });
      event.target.reset();
      categorySuggestions.hidden = true;
      await refreshAll();
    });

    async function duplicatePreflightFor(url) {
      const response = await fetch('/api/bookmarks/preflight', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({url})
      });
      return response.json();
    }

    function renderDuplicatePreflight(preflight, formData, form) {
      duplicatePreflight.hidden = false;
      duplicatePreflight.innerHTML = `
        <h3>Moegliche Dublette gefunden</h3>
        <p class="muted">Normalisierte URL: ${escapeHtml(preflight.normalized_url)}</p>
        <p>Du kannst einen vorhandenen Bookmark oeffnen, den besten Treffer aktualisieren oder bewusst trotzdem neu speichern.</p>
      `;
      for (const match of preflight.matches) {
        const bookmark = match.bookmark;
        const row = document.createElement('div');
        row.className = 'duplicate-match';
        row.innerHTML = `
          <strong>${escapeHtml(bookmark.title)}</strong>
          <p><a href="${escapeAttr(bookmark.url)}">${escapeHtml(bookmark.url)}</a></p>
          <p class="muted">${escapeHtml(match.reason)} · Score ${match.score} · ${escapeHtml(match.match_type)}</p>
          <button type="button" data-action="open">Vorhandenen Bookmark oeffnen</button>
          <button type="button" data-action="update">Vorhandenen Bookmark aktualisieren</button>
        `;
        row.querySelector('[data-action="open"]').addEventListener('click', () => openBookmark(bookmark.id));
        row.querySelector('[data-action="update"]').addEventListener('click', async () => {
          await patchBookmark(bookmark.id, formData);
          form.reset();
          categorySuggestions.hidden = true;
          duplicatePreflight.hidden = true;
        });
        duplicatePreflight.appendChild(row);
      }
      const saveAnyway = document.createElement('button');
      saveAnyway.type = 'button';
      saveAnyway.textContent = 'Trotzdem neu speichern';
      saveAnyway.addEventListener('click', async () => {
        formData.allow_duplicate = true;
        await fetch('/api/bookmarks', {
          method: 'POST',
          headers: {'content-type': 'application/json'},
          body: JSON.stringify(formData)
        });
        form.reset();
        categorySuggestions.hidden = true;
        duplicatePreflight.hidden = true;
        await refreshAll();
      });
      duplicatePreflight.appendChild(saveAnyway);
    }

    function openBookmark(id) {
      setActiveTab('bookmarks');
      const row = document.querySelector(`[data-bookmark-id="${CSS.escape(id)}"]`);
      if (!row) {
        clearBookmarkFilters();
        document.querySelector('#filter-status').value = 'all';
        refreshBookmarks().then(() => {
          const refreshed = document.querySelector(`[data-bookmark-id="${CSS.escape(id)}"]`);
          refreshed?.scrollIntoView({behavior: 'smooth', block: 'center'});
          refreshed?.querySelector('details')?.setAttribute('open', 'open');
        });
        return;
      }
      row.scrollIntoView({behavior: 'smooth', block: 'center'});
      row.querySelector('details')?.setAttribute('open', 'open');
    }

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

    apiTokenForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const response = await fetch('/api/tokens', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(Object.fromEntries(new FormData(event.target)))
      });
      const payload = await response.json();
      apiTokenCreated.hidden = false;
      if (!response.ok) {
        apiTokenCreated.innerHTML = `<strong>Token konnte nicht erstellt werden.</strong><p>${escapeHtml(payload.error || 'Unbekannter Fehler')}</p>`;
        return;
      }
      apiTokenCreated.innerHTML = `
        <strong>Token erstellt. Jetzt kopieren.</strong>
        <p class="muted">LinkVault zeigt diesen Token nur einmal an.</p>
        <code>${escapeHtml(payload.token)}</code>
      `;
      event.target.reset();
      await refreshOperations();
    });

    document.querySelector('#logout').addEventListener('click', async () => {
      await fetch('/api/logout', {method: 'POST'});
      await loadAuth();
    });

    document.querySelector('#suggest-categories').addEventListener('click', async () => {
      await loadCategorySuggestions(document.querySelector('#bookmark-form'));
    });

    document.querySelector('#import-preview-button').addEventListener('click', async () => {
      const data = await importPayloadFromForm(document.querySelector('#import-form'));
      const response = await fetch(importEndpoint(data.format, true), {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      });
      renderImportPreview(await response.json());
    });

    document.querySelector('#import-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = await importPayloadFromForm(event.target);
      const response = await fetch(importEndpoint(data.format), {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      });
      renderImportResult(await response.json());
      event.target.reset();
      await refreshAll();
    });

    document.querySelector('#refresh').addEventListener('click', refreshBookmarks);
    document.querySelector('#dry-run').addEventListener('click', refreshDryRun);
    document.querySelector('#refresh-operations').addEventListener('click', refreshOperations);
    document.querySelector('#search').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-favorite').addEventListener('change', refreshBookmarks);
    document.querySelector('#filter-pinned').addEventListener('change', refreshBookmarks);
    document.querySelector('#filter-domain').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-tag').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-collection').addEventListener('input', refreshBookmarks);
    document.querySelector('#filter-status').addEventListener('change', refreshBookmarks);
    document.querySelector('#bookmark-view').addEventListener('change', updateViewPreview);
    document.querySelectorAll('[data-display-field]').forEach((checkbox) => {
      checkbox.addEventListener('change', updateViewPreview);
    });
    document.querySelector('#save-view-preferences').addEventListener('click', saveViewPreferences);
    document.querySelector('#reset-view-preferences').addEventListener('click', resetViewPreferences);
    document.querySelector('#show-inbox').addEventListener('click', showInbox);
    document.querySelector('#show-active').addEventListener('click', showActiveBookmarks);
    document.querySelectorAll('[data-inbox-trigger]').forEach((button) => {
      button.addEventListener('click', showInbox);
    });
    document.querySelectorAll('[data-tab-trigger]').forEach((button) => {
      button.addEventListener('click', () => setActiveTab(button.dataset.tabTrigger));
    });
    document.addEventListener('keydown', async (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setActiveTab('bookmarks');
        document.querySelector('#search').focus();
        return;
      }

      if (isTypingTarget(event.target)) return;
      if (event.ctrlKey || event.metaKey || event.altKey) return;

      if (event.key.toLowerCase() === 'n') {
        event.preventDefault();
        setActiveTab('save');
        document.querySelector('#bookmark-form input[name="url"]').focus();
      } else if (event.key.toLowerCase() === 'i') {
        event.preventDefault();
        setActiveTab('import');
      } else if (event.key.toLowerCase() === 'd') {
        event.preventDefault();
        setActiveTab('dedup');
        await refreshDryRun();
      } else if (event.key.toLowerCase() === 'b') {
        event.preventDefault();
        setActiveTab('bookmarks');
        await refreshBookmarks();
      }
    });

    function isTypingTarget(target) {
      const tagName = target?.tagName?.toLowerCase();
      return target?.isContentEditable || ['input', 'select', 'textarea'].includes(tagName);
    }
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
        status=get_query_param(params, "status") or "active",
    )


def to_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


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
