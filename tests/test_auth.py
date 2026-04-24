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

    def test_api_token_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = AuthStore(Path(tmp) / "linkvault.sqlite3")
            user = auth.create_initial_user("admin", "very-long-password", "", "")

            created = auth.create_api_token("Firefox")
            token = created["token"]
            listed = auth.list_api_tokens()

            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0].name, "Firefox")
            self.assertEqual(auth.user_for_api_token(token).id, user.id)
            self.assertEqual(auth.user_for_api_token("wrong"), None)
            self.assertTrue(auth.delete_api_token(listed[0].id))
            self.assertEqual(auth.user_for_api_token(token), None)


class AuthHttpTest(unittest.TestCase):
    def test_options_request_returns_cors_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous_data = os.environ.get("LINKVAULT_DATA")
            os.environ["LINKVAULT_DATA"] = str(Path(tmp) / "linkvault.sqlite3")
            server = ThreadingHTTPServer(("127.0.0.1", 0), LinkVaultHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"

            try:
                request = urllib.request.Request(
                    f"{base_url}/api/bookmarks",
                    method="OPTIONS",
                    headers={
                        "origin": "moz-extension://linkvault",
                        "access-control-request-method": "POST",
                        "access-control-request-headers": "authorization, content-type",
                    },
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    self.assertEqual(response.status, 204)
                    self.assertEqual(response.headers["access-control-allow-origin"], "*")
                    self.assertIn("authorization", response.headers["access-control-allow-headers"])
                    self.assertIn("OPTIONS", response.headers["access-control-allow-methods"])
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                restore_env("LINKVAULT_DATA", previous_data)

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

                suggestions = request_json(
                    opener,
                    f"{base_url}/api/bookmarks/suggestions",
                    {"url": "https://github.com/Nanja-at-web/LinkVault", "title": "Proxmox backup"},
                )
                self.assertIn("github", suggestions["suggested_tags"])
                self.assertIn("Development", suggestions["suggested_collections"])

                with self.assertRaises(urllib.error.HTTPError) as duplicate:
                    request_json(opener, f"{base_url}/api/bookmarks", {"url": "http://127.0.0.1:9/a"})
                self.assertEqual(duplicate.exception.code, 409)
                conflict = json.loads(duplicate.exception.read().decode("utf-8"))
                self.assertEqual(conflict["preflight"]["matches"][0]["bookmark"]["id"], bookmark["id"])

                duplicate_bookmark = request_json(
                    opener,
                    f"{base_url}/api/bookmarks",
                    {"url": "http://127.0.0.1:9/a", "allow_duplicate": True},
                )
                self.assertNotEqual(duplicate_bookmark["id"], bookmark["id"])

                merge = request_json(
                    opener,
                    f"{base_url}/api/dedup/merge",
                    {"winner_id": bookmark["id"], "loser_ids": [duplicate_bookmark["id"]]},
                )
                self.assertEqual(merge["merged_count"], 1)
                self.assertEqual(merge["deleted"], 0)
                self.assertEqual(merge["merged_losers"][0]["status"], "merged_duplicate")
                self.assertEqual(merge["merged_losers"][0]["merged_into"], bookmark["id"])
                merge_history = get_json(opener, f"{base_url}/api/dedup/merges")
                self.assertEqual(merge_history["events"][0]["id"], merge["merge_event_id"])
                self.assertEqual(merge_history["events"][0]["winner_id"], bookmark["id"])
                self.assertEqual(merge_history["events"][0]["loser_ids"], [duplicate_bookmark["id"]])
                undo = request_json(opener, f"{base_url}/api/dedup/merges/{merge['merge_event_id']}/undo", {})
                self.assertEqual(undo["merge_event_id"], merge["merge_event_id"])
                self.assertEqual(undo["restored_count"], 1)
                merge_history_after_undo = get_json(opener, f"{base_url}/api/dedup/merges")
                self.assertFalse(merge_history_after_undo["events"][0]["can_undo"])
                all_bookmarks_after_undo = get_json(opener, f"{base_url}/api/bookmarks?status=all")
                all_ids_after_undo = {item["id"] for item in all_bookmarks_after_undo["bookmarks"]}
                self.assertIn(bookmark["id"], all_ids_after_undo)
                self.assertIn(duplicate_bookmark["id"], all_ids_after_undo)

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

                token_payload = request_json(opener, f"{base_url}/api/tokens", {"name": "Firefox extension"})
                self.assertTrue(token_payload["token"].startswith("lv_pat_"))
                token_list = get_json(opener, f"{base_url}/api/tokens")
                self.assertEqual(token_list["tokens"][0]["name"], "Firefox extension")
                api_bookmark = request_json(
                    opener,
                    f"{base_url}/api/bookmarks",
                    {"url": "http://127.0.0.1:9/token"},
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertEqual(api_bookmark["url"], "http://127.0.0.1:9/token")
                browser_preview = request_json(
                    opener,
                    f"{base_url}/api/import/browser-bookmarks/preview",
                    {
                        "items": [
                            {
                                "url": "http://127.0.0.1:9/from-browser",
                                "title": "From Browser",
                                "source_root": "Bookmarks Toolbar",
                                "source_folder_path": "Bookmarks Toolbar / Dev",
                                "source_position": 0,
                            },
                            {
                                "url": "http://127.0.0.1:9/from-browser?utm_source=dup",
                                "title": "From Browser Duplicate",
                                "source_root": "Bookmarks Toolbar",
                                "source_folder_path": "Bookmarks Toolbar / Dev",
                                "source_position": 1,
                            },
                        ]
                    },
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertEqual(browser_preview["create"], 1)
                self.assertEqual(browser_preview["duplicate_in_import"], 1)
                browser_import = request_json(
                    opener,
                    f"{base_url}/api/import/browser-bookmarks",
                    {
                        "items": [
                            {
                                "url": "http://127.0.0.1:9/from-browser",
                                "title": "From Browser",
                                "source_root": "Bookmarks Toolbar",
                                "source_folder_path": "Bookmarks Toolbar / Dev",
                                "source_position": 0,
                            },
                            {
                                "url": "http://127.0.0.1:9/from-browser?utm_source=dup",
                                "title": "From Browser Duplicate",
                                "source_root": "Bookmarks Toolbar",
                                "source_folder_path": "Bookmarks Toolbar / Dev",
                                "source_position": 1,
                            },
                        ]
                    },
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertEqual(browser_import["created"], 1)
                self.assertEqual(browser_import["duplicates_skipped"], 1)
                self.assertTrue(browser_import["import_session_id"])
                browser_export = get_json(
                    opener,
                    f"{base_url}/api/export/browser-bookmarks",
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertGreaterEqual(browser_export["bookmark_count"], 1)
                self.assertEqual(browser_export["roots"][0]["title"], "Bookmarks Toolbar")
                import_sessions = get_json(opener, f"{base_url}/api/import/sessions")
                self.assertEqual(import_sessions["sessions"][0]["id"], browser_import["import_session_id"])
                activity = get_json(opener, f"{base_url}/api/activity")
                activity_kinds = {event["kind"] for event in activity["events"]}
                self.assertIn("import_session_created", activity_kinds)
                self.assertIn("merge_duplicates", activity_kinds)
                self.assertIn("merge_undo", activity_kinds)
                self.assertIn("bulk_update", activity_kinds)
                open_conflicts = get_json(opener, f"{base_url}/api/conflicts?state=open")
                self.assertTrue(open_conflicts["conflicts"])
                self.assertTrue(any(conflict["kind"] == "import_duplicate" for conflict in open_conflicts["conflicts"]))
                import_conflict = next(conflict for conflict in open_conflicts["conflicts"] if conflict["kind"] == "import_duplicate")
                all_conflicts = get_json(opener, f"{base_url}/api/conflicts?state=all")
                self.assertTrue(any(conflict["kind"] == "merge_conflict" for conflict in all_conflicts["conflicts"]))
                updated_conflict = request_json(
                    opener,
                    f"{base_url}/api/conflicts/{import_conflict['id']}/state",
                    {"state": "ignored"},
                )
                self.assertEqual(updated_conflict["state"], "ignored")
                ignored_conflicts = get_json(opener, f"{base_url}/api/conflicts?state=ignored")
                self.assertTrue(any(conflict["id"] == import_conflict["id"] for conflict in ignored_conflicts["conflicts"]))
                default_view = get_json(opener, f"{base_url}/api/settings/bookmark-view")
                self.assertEqual(default_view["preferences"]["view"], "compact")
                self.assertFalse(default_view["saved"])
                saved_view = request_json(
                    opener,
                    f"{base_url}/api/settings/bookmark-view",
                    {
                        "view": "grid",
                        "fields": {"title": True, "description": True, "notes": False},
                        "filters": {
                            "query": "restore",
                            "favorite": True,
                            "pinned": False,
                            "domain": "example.com",
                            "tag": "ops",
                            "collection": "Inbox",
                            "status": "all",
                        },
                    },
                )
                self.assertTrue(saved_view["saved"])
                self.assertEqual(saved_view["preferences"]["view"], "grid")
                loaded_view = get_json(opener, f"{base_url}/api/settings/bookmark-view")
                self.assertTrue(loaded_view["saved"])
                self.assertEqual(loaded_view["preferences"]["filters"]["query"], "restore")

                named_views_initial = get_json(opener, f"{base_url}/api/settings/bookmark-views")
                self.assertEqual(named_views_initial["views"][0]["name"], "Standard")
                self.assertEqual(named_views_initial["default_name"], "Standard")

                inbox_view = request_json(
                    opener,
                    f"{base_url}/api/settings/bookmark-views",
                    {
                        "name": "Inbox Review",
                        "preferences": {
                            "view": "detailed",
                            "fields": {"title": True, "description": True, "notes": True},
                            "filters": {
                                "query": "inbox",
                                "favorite": False,
                                "pinned": False,
                                "domain": "",
                                "tag": "",
                                "collection": "Inbox",
                                "status": "active",
                            },
                        },
                    },
                )
                self.assertEqual(inbox_view["view"]["name"], "Inbox Review")
                self.assertFalse(inbox_view["view"]["is_default"])

                research_view = request_json(
                    opener,
                    f"{base_url}/api/settings/bookmark-views",
                    {
                        "name": "Research Grid",
                        "preferences": {
                            "view": "grid",
                            "fields": {"title": True, "description": True, "notes": False},
                            "filters": {
                                "query": "research",
                                "favorite": True,
                                "pinned": False,
                                "domain": "example.com",
                                "tag": "ops",
                                "collection": "Research",
                                "status": "all",
                            },
                        },
                        "set_default": True,
                    },
                )
                self.assertEqual(research_view["default_name"], "Research Grid")

                named_views = get_json(opener, f"{base_url}/api/settings/bookmark-views")
                self.assertEqual(len(named_views["views"]), 2)
                self.assertEqual(named_views["default_name"], "Research Grid")
                self.assertEqual(named_views["preferences"]["view"], "grid")

                named_default = request_json(
                    opener,
                    f"{base_url}/api/settings/bookmark-views/default",
                    {"name": "Inbox Review"},
                )
                self.assertEqual(named_default["default_name"], "Inbox Review")
                self.assertEqual(named_default["preferences"]["filters"]["collection"], "Inbox")

                deleted_named_view = request_json(
                    opener,
                    f"{base_url}/api/settings/bookmark-views/Research%20Grid",
                    {},
                    method="DELETE",
                )
                self.assertTrue(deleted_named_view["deleted"])
                self.assertEqual(len(deleted_named_view["views"]), 1)
                self.assertEqual(deleted_named_view["views"][0]["name"], "Inbox Review")

                reset_view = request_json(opener, f"{base_url}/api/settings/bookmark-view", {}, method="DELETE")
                self.assertFalse(reset_view["saved"])
                self.assertEqual(reset_view["preferences"]["view"], "compact")

                request_json(opener, f"{base_url}/api/logout", {})
                with self.assertRaises(urllib.error.HTTPError) as logged_out:
                    request_json(opener, f"{base_url}/api/bookmarks", {"url": "http://127.0.0.1:9/b"})
                self.assertEqual(logged_out.exception.code, 401)
                token_bookmarks = get_json(
                    opener,
                    f"{base_url}/api/bookmarks",
                    headers={"x-linkvault-token": token_payload["token"]},
                )
                self.assertTrue(token_bookmarks["bookmarks"])
                with self.assertRaises(urllib.error.HTTPError) as token_management:
                    get_json(opener, f"{base_url}/api/tokens", headers={"authorization": f"Bearer {token_payload['token']}"})
                self.assertEqual(token_management.exception.code, 401)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                restore_env("LINKVAULT_DATA", previous_data)
                restore_env("LINKVAULT_SETUP_TOKEN", previous_token)


def request_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    payload: dict,
    method: str = "POST",
    headers: dict[str, str] | None = None,
) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", **(headers or {})},
        method=method,
    )
    with opener.open(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(opener: urllib.request.OpenerDirector, url: str, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, headers=headers or {})
    with opener.open(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def restore_env(key: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
