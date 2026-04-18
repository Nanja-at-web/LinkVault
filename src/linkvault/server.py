from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import __version__
from .store import BookmarkStore


def make_store() -> BookmarkStore:
    data_path = Path(os.environ.get("LINKVAULT_DATA", "data/bookmarks.json"))
    return BookmarkStore(data_path)


class LinkVaultHandler(BaseHTTPRequestHandler):
    server_version = f"LinkVault/{__version__}"

    def do_GET(self) -> None:
        store = make_store()
        if self.path == "/healthz":
            self.send_json({"ok": True, "version": __version__})
        elif self.path == "/api/bookmarks":
            self.send_json({"bookmarks": [bookmark.__dict__ for bookmark in store.list()]})
        elif self.path == "/api/dedup":
            self.send_json({"groups": store.dedup_groups()})
        elif self.path == "/":
            self.send_html(index_html())
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/api/bookmarks":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self.read_json()
            bookmark = make_store().add(payload)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except json.JSONDecodeError:
            self.send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return

        self.send_json(bookmark.__dict__, HTTPStatus.CREATED)

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
    body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 860px; }
    input, textarea, button { font: inherit; padding: .55rem; }
    input, textarea { width: 100%; box-sizing: border-box; margin: .25rem 0 .75rem; }
    button { border: 1px solid #222; background: #fff; border-radius: 6px; cursor: pointer; }
    pre { background: #f2f2f2; padding: 1rem; overflow: auto; }
  </style>
</head>
<body>
  <h1>LinkVault MVP</h1>
  <p>Links speichern, normalisieren und Dubletten finden.</p>
  <form id="bookmark-form">
    <label>URL <input name="url" required placeholder="https://example.com?utm_source=test"></label>
    <label>Titel <input name="title" placeholder="Optional"></label>
    <label>Tags <input name="tags" placeholder="proxmox, homelab"></label>
    <label>Collections <input name="collections" placeholder="Homelab/Proxmox"></label>
    <label><input name="favorite" type="checkbox" style="width:auto"> Favorit</label>
    <button>Speichern</button>
  </form>
  <h2>Dubletten</h2>
  <button id="refresh">Aktualisieren</button>
  <pre id="output">Noch keine Daten geladen.</pre>
  <script>
    const output = document.querySelector('#output');
    async function refresh() {
      const response = await fetch('/api/dedup');
      output.textContent = JSON.stringify(await response.json(), null, 2);
    }
    document.querySelector('#bookmark-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.target));
      data.favorite = data.favorite === 'on';
      await fetch('/api/bookmarks', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(data)
      });
      event.target.reset();
      refresh();
    });
    document.querySelector('#refresh').addEventListener('click', refresh);
    refresh();
  </script>
</body>
</html>"""


def main() -> None:
    host = os.environ.get("LINKVAULT_HOST", "127.0.0.1")
    port = int(os.environ.get("LINKVAULT_PORT", "3080"))
    server = ThreadingHTTPServer((host, port), LinkVaultHandler)
    print(f"LinkVault listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
