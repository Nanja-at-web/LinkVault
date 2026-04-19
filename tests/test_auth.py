import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from http.server import ThreadingHTTPServer
from pathlib import Path

from linkvault.auth import AuthStore
from linkvault.server import LinkVaultHandler


class AuthStoreTest(unittest.TestCase):
    def test_initial_setup_requires_configured_token_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = AuthStore(Path(tmp) / "linkvault.sqlite3")

            with self.assertRaises(ValueError):
                auth.create_initial_user("admin", "very-long-password", "wrong", "secret")

            user = auth.create_initial_user("admin", "very-long-password", "secret", "secret")

            self.assertEqual(user.username, "admin")
            self.assertFalse(auth.setup_required())

    def test_authenticate_and_session_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = AuthStore(Path(tmp) / "linkvault.sqlite3")
            user = auth.create_initial_user("admin", "very-long-password", "", "")

            self.assertIsNone(auth.authenticate("admin", "wrong-password"))
            authenticated = auth.authenticate("admin", "very-long-password")
            self.assertIsNotNone(authenticated)

            session_id = auth.create_session(user.id)
            self.assertEqual(auth.user_for_session(session_id).username, "admin")
            auth.delete_session(session_id)
            self.assertIsNone(auth.user_for_session(session_id))


class AuthHttpTest(unittest.TestCase):
    def test_bookmark_api_requires_login(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous_data = os.environ.get("LINKVAULT_DATA")
            previous_token = os.environ.get("LINKVAULT_SETUP_TOKEN")
            os.environ["LINKVAULT_DATA"] = str(Path(tmp) / "linkvault.sqlite3")
            os.environ["LINKVAULT_SETUP_TOKEN"] = "secret"
            server = ThreadingHTTPServer(("127.0.0.1", 0), LinkVaultHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

            try:
                with self.assertRaises(urllib.error.HTTPError) as unauthorized:
                    request_json(opener, f"{base_url}/api/bookmarks", {"url": "http://127.0.0.1:9/a"})
                self.assertEqual(unauthorized.exception.code, 401)

                setup = request_json(
                    opener,
                    f"{base_url}/api/setup",
                    {"username": "admin", "password": "very-long-password", "setup_token": "secret"},
                )
                self.assertEqual(setup["user"]["username"], "admin")

                bookmark = request_json(opener, f"{base_url}/api/bookmarks", {"url": "http://127.0.0.1:9/a"})
                self.assertEqual(bookmark["url"], "http://127.0.0.1:9/a")

                preflight = request_json(
                    opener,
                    f"{base_url}/api/bookmarks/preflight",
                    {"url": "http://127.0.0.1:9/a?utm_source=test"},
                )
                self.assertTrue(preflight["has_matches"])
                self.assertEqual(preflight["matches"][0]["bookmark"]["id"], bookmark["id"])

                updated = request_json(
                    opener,
                    f"{base_url}/api/bookmarks/{bookmark['id']}",
                    {"title": "Updated", "notes": "Edited in UI"},
                    method="PATCH",
                )
                self.assertEqual(updated["title"], "Updated")
                self.assertEqual(updated["notes"], "Edited in UI")

                bulk = request_json(
                    opener,
                    f"{base_url}/api/bookmarks/bulk",
                    {"ids": [bookmark["id"]], "add_tags": "bulk", "set_collections": "Inbox", "favorite": True},
                )
                self.assertEqual(bulk["updated"], 1)
                self.assertEqual(bulk["bookmarks"][0]["tags"], ["bulk"])
                self.assertEqual(bulk["bookmarks"][0]["collections"], ["Inbox"])
                self.assertTrue(bulk["bookmarks"][0]["favorite"])

                request_json(opener, f"{base_url}/api/logout", {})
                with self.assertRaises(urllib.error.HTTPError) as logged_out:
                    request_json(opener, f"{base_url}/api/bookmarks", {"url": "http://127.0.0.1:9/b"})
                self.assertEqual(logged_out.exception.code, 401)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                restore_env("LINKVAULT_DATA", previous_data)
                restore_env("LINKVAULT_SETUP_TOKEN", previous_token)


def request_json(opener: urllib.request.OpenerDirector, url: str, payload: dict, method: str = "POST") -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method=method,
    )
    with opener.open(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def restore_env(key: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
