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
            self.assertEqual(user.role, "admin")
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

            created = auth.create_api_token(user.id, "Firefox")
            token = created["token"]
            listed = auth.list_api_tokens(user.id)

            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0].name, "Firefox")
            self.assertEqual(auth.user_for_api_token(token).id, user.id)
            self.assertEqual(auth.user_for_api_token("wrong"), None)
            self.assertTrue(auth.delete_api_token(listed[0].id, user.id))
            self.assertEqual(auth.user_for_api_token(token), None)

    def test_user_management_and_password_flows(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = AuthStore(Path(tmp) / "linkvault.sqlite3")
            admin = auth.create_initial_user("admin", "very-long-password", "", "")
            user = auth.create_user("alice", "another-long-password", "user")

            self.assertEqual([item.username for item in auth.list_users()], ["admin", "alice"])
            self.assertEqual(user.role, "user")

            updated = auth.update_user(user.id, role="admin")
            self.assertEqual(updated.role, "admin")

            auth.change_password(user.id, "another-long-password", "changed-long-password")
            self.assertIsNotNone(auth.authenticate("alice", "changed-long-password"))

            reset_user = auth.admin_reset_password(user.id, "reset-long-password")
            self.assertEqual(reset_user.id, user.id)
            self.assertIsNotNone(auth.authenticate("alice", "reset-long-password"))

    def test_last_admin_cannot_be_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = AuthStore(Path(tmp) / "linkvault.sqlite3")
            admin = auth.create_initial_user("admin", "very-long-password", "", "")

            with self.assertRaises(ValueError):
                auth.update_user(admin.id, role="user")

            with self.assertRaises(ValueError):
                auth.delete_user(admin.id)


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
                self.assertEqual(setup["user"]["role"], "admin")
                me = get_json(opener, f"{base_url}/api/me")
                self.assertEqual(me["user"]["role"], "admin")

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

                created_user = request_json(
                    opener,
                    f"{base_url}/api/users",
                    {"username": "alice", "password": "another-long-password", "role": "user"},
                )
                self.assertEqual(created_user["user"]["username"], "alice")
                viewer_user = request_json(
                    opener,
                    f"{base_url}/api/users",
                    {"username": "bob", "password": "viewer-long-password", "role": "user"},
                )
                user_list = get_json(opener, f"{base_url}/api/users")
                self.assertEqual(len(user_list["users"]), 3)

                viewer_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
                request_json(
                    viewer_opener,
                    f"{base_url}/api/login",
                    {"username": "bob", "password": "viewer-long-password"},
                )
                with self.assertRaises(urllib.error.HTTPError) as non_admin_users:
                    get_json(viewer_opener, f"{base_url}/api/users")
                self.assertEqual(non_admin_users.exception.code, 403)

                updated_user = request_json(
                    opener,
                    f"{base_url}/api/users/{created_user['user']['id']}",
                    {"username": "alice", "role": "admin"},
                    method="PATCH",
                )
                self.assertEqual(updated_user["user"]["role"], "admin")

                password_change = request_json(
                    opener,
                    f"{base_url}/api/account/password",
                    {"current_password": "very-long-password", "new_password": "replacement-password"},
                )
                self.assertTrue(password_change["changed"])

                request_json(opener, f"{base_url}/api/logout", {})
                relogin = request_json(
                    opener,
                    f"{base_url}/api/login",
                    {"username": "admin", "password": "replacement-password"},
                )
                self.assertEqual(relogin["user"]["username"], "admin")

                password_reset = request_json(
                    opener,
                    f"{base_url}/api/users/{created_user['user']['id']}/reset-password",
                    {"new_password": "alice-reset-password"},
                )
                self.assertTrue(password_reset["password_reset"])

                user_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
                login_user = request_json(
                    user_opener,
                    f"{base_url}/api/login",
                    {"username": "alice", "password": "alice-reset-password"},
                )
                self.assertEqual(login_user["user"]["username"], "alice")
                self.assertEqual(login_user["user"]["role"], "admin")

                user_password_change = request_json(
                    user_opener,
                    f"{base_url}/api/account/password",
                    {"current_password": "alice-reset-password", "new_password": "alice-new-password"},
                )
                self.assertTrue(user_password_change["changed"])

                request_json(user_opener, f"{base_url}/api/logout", {})
                request_json(
                    user_opener,
                    f"{base_url}/api/login",
                    {"username": "alice", "password": "alice-new-password"},
                )
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
                restore_preview = request_json(
                    opener,
                    f"{base_url}/api/export/browser-bookmarks/restore-preview",
                    {
                        "existing_items": [
                            {
                                "id": "browser-1",
                                "title": "Existing Browser Bookmark",
                                "url": "http://127.0.0.1:9/from-browser",
                                "folder_path": "Bookmarks Toolbar / Existing",
                            }
                        ],
                        "existing_folders": [
                            {
                                "id": "folder-root",
                                "title": "LinkVault Restore",
                                "path": "LinkVault Restore",
                                "parent_path": "",
                            }
                        ],
                        "duplicate_action": "skip",
                        "target_mode": "new",
                        "target_title": "LinkVault Restore",
                        "filters": {"status": "active"},
                    },
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertEqual(restore_preview["conflict_count"], 2)
                self.assertEqual(restore_preview["structure_conflict_count"], 1)
                self.assertTrue(restore_preview["session_id"])
                self.assertEqual(restore_preview["records"][0]["action"], "skip_existing")
                self.assertTrue(restore_preview["records"][0]["conflict_id"])
                self.assertTrue(restore_preview["folder_records"][0]["conflict_id"])
                import_sessions = get_json(opener, f"{base_url}/api/import/sessions")
                self.assertEqual(import_sessions["sessions"][0]["id"], browser_import["import_session_id"])
                restore_sessions = get_json(opener, f"{base_url}/api/restore/sessions")
                self.assertEqual(restore_sessions["sessions"][0]["id"], restore_preview["session_id"])
                self.assertEqual(restore_sessions["sessions"][0]["state"], "previewed")
                group_keys = {group["group_key"] for group in restore_sessions["sessions"][0]["conflict_groups"]}
                self.assertIn("target_root", group_keys)
                self.assertIn("existing_links", group_keys)
                group_decision = request_json(
                    opener,
                    f"{base_url}/api/restore/sessions/{restore_preview['session_id']}/conflict-groups/existing_links/decision",
                    {"decision": "merge"},
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertEqual(group_decision["selected_action"], "merge_existing")
                self.assertEqual(group_decision["updated_count"], 1)
                self.assertEqual(group_decision["group"]["resolved_count"], 1)
                activity = get_json(opener, f"{base_url}/api/activity")
                activity_kinds = {event["kind"] for event in activity["events"]}
                self.assertIn("import_session_created", activity_kinds)
                self.assertIn("merge_duplicates", activity_kinds)
                self.assertIn("merge_undo", activity_kinds)
                self.assertIn("bulk_update", activity_kinds)
                self.assertIn("conflict_group_decision_changed", activity_kinds)
                open_conflicts = get_json(opener, f"{base_url}/api/conflicts?state=open")
                self.assertTrue(open_conflicts["conflicts"])
                self.assertTrue(any(conflict["kind"] == "import_duplicate" for conflict in open_conflicts["conflicts"]))
                import_conflict = next(conflict for conflict in open_conflicts["conflicts"] if conflict["kind"] == "import_duplicate")
                all_conflicts = get_json(opener, f"{base_url}/api/conflicts?state=all")
                self.assertTrue(any(conflict["kind"] == "merge_conflict" for conflict in all_conflicts["conflicts"]))
                restore_conflict = next(conflict for conflict in all_conflicts["conflicts"] if conflict["kind"] == "browser_restore_conflict")
                structure_conflict = next(conflict for conflict in all_conflicts["conflicts"] if conflict["kind"] == "browser_restore_structure_conflict")
                self.assertEqual(restore_conflict["group_key"], "existing_links")
                self.assertEqual(structure_conflict["group_key"], "target_root")
                decided_conflict = request_json(
                    opener,
                    f"{base_url}/api/conflicts/{restore_conflict['id']}/decision",
                    {"decision": "update"},
                )
                self.assertEqual(decided_conflict["state"], "resolved")
                self.assertEqual(decided_conflict["details"]["selected_action"], "update_existing")
                decided_structure_conflict = request_json(
                    opener,
                    f"{base_url}/api/conflicts/{structure_conflict['id']}/decision",
                    {"decision": "reuse"},
                )
                self.assertEqual(decided_structure_conflict["state"], "resolved")
                self.assertEqual(decided_structure_conflict["details"]["selected_action"], "reuse_existing_folder")
                updated_conflict = request_json(
                    opener,
                    f"{base_url}/api/conflicts/{import_conflict['id']}/state",
                    {"state": "ignored"},
                )
                self.assertEqual(updated_conflict["state"], "ignored")
                completed_restore = request_json(
                    opener,
                    f"{base_url}/api/export/browser-bookmarks/restore-complete",
                    {
                        "session_id": restore_preview["session_id"],
                        "created": 1,
                        "skipped_existing": 0,
                        "merged_existing": 1,
                        "updated_existing": 0,
                        "root_title": "LinkVault Restore",
                    },
                    headers={"authorization": f"Bearer {token_payload['token']}"},
                )
                self.assertEqual(completed_restore["state"], "completed")
                self.assertEqual(completed_restore["result"]["created"], 1)
                restore_sessions = get_json(opener, f"{base_url}/api/restore/sessions")
                self.assertEqual(restore_sessions["sessions"][0]["state"], "completed")
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

                request_json(user_opener, f"{base_url}/api/tokens", {"name": "Alice token"})
                alice_tokens = get_json(user_opener, f"{base_url}/api/tokens")
                self.assertEqual(len(alice_tokens["tokens"]), 1)
                self.assertEqual(alice_tokens["tokens"][0]["name"], "Alice token")

                deleted_bob = request_json(user_opener, f"{base_url}/api/users/{viewer_user['user']['id']}", {}, method="DELETE")
                self.assertTrue(deleted_bob["deleted"])
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
