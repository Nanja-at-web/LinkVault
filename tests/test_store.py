import base64
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from linkvault.metadata import PageMetadata
from linkvault.store import BookmarkFilters, BookmarkStore, parse_browser_html


class StoreTest(unittest.TestCase):
    def test_dedup_groups_exact_normalized_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            first = store.add({"url": "https://example.com/a?utm_source=news", "title": "A"})
            second = store.add({"url": "https://example.com/a", "title": "A again", "favorite": True})

            groups = store.dedup_groups()

            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["winner_id"], second.id)
            self.assertEqual({item["id"] for item in groups[0]["items"]}, {first.id, second.id})

    def test_update_and_delete_bookmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            bookmark = store.add({"url": "https://example.com", "title": "Example"})

            self.assertEqual(bookmark.collections, ["Inbox"])

            updated = store.update(
                bookmark.id,
                {
                    "title": "Updated Example",
                    "description": "Updated description",
                    "favorite": True,
                    "tags": "docs, test",
                    "collections": "Inbox, Reading",
                    "notes": "Keep this one.",
                },
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated.title, "Updated Example")
            self.assertEqual(updated.description, "Updated description")
            self.assertTrue(updated.favorite)
            self.assertEqual(updated.tags, ["docs", "test"])
            self.assertEqual(updated.collections, ["Inbox", "Reading"])
            self.assertEqual(updated.notes, "Keep this one.")
            self.assertTrue(store.delete(bookmark.id))
            self.assertIsNone(store.get(bookmark.id))

    def test_category_suggestions_from_domain_and_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)

            suggestions = store.category_suggestions(
                {
                    "url": "https://github.com/Nanja-at-web/LinkVault",
                    "title": "LinkVault Proxmox backup guide",
                    "description": "Selfhost LXC restore documentation",
                }
            )

            self.assertIn("github", suggestions["suggested_tags"])
            self.assertIn("proxmox", suggestions["suggested_tags"])
            self.assertIn("backup", suggestions["suggested_tags"])
            self.assertIn("Development", suggestions["suggested_collections"])
            self.assertIn("Homelab/Proxmox", suggestions["suggested_collections"])
            self.assertTrue(suggestions["inbox_default"])

    def test_import_browser_html_skips_duplicates_and_keeps_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            html = """
            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <DL><p>
              <DT><H3>Homelab</H3>
              <DL><p>
                <DT><A HREF="https://example.com/a?utm_source=x" TAGS="proxmox,selfhost">Example A</A>
                <DT><A HREF="https://example.com/a">Example A duplicate</A>
              </DL><p>
            </DL><p>
            """

            result = store.import_browser_html(html)

            self.assertEqual(result["created"], 1)
            self.assertEqual(result["duplicates_skipped"], 1)
            self.assertEqual(result["invalid_skipped"], 0)
            bookmarks = store.list()
            self.assertEqual(len(bookmarks), 1)
            self.assertEqual(bookmarks[0].collections, ["Homelab"])
            self.assertEqual(bookmarks[0].tags, ["proxmox", "selfhost"])

    def test_import_browser_bookmarks_preserves_source_structure_for_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)

            result = store.import_browser_bookmarks(
                [
                    {
                        "url": "https://example.com/a",
                        "title": "A",
                        "collections": ["Bookmarks Toolbar", "Dev"],
                        "source_browser": "firefox-extension",
                        "source_root": "Bookmarks Toolbar",
                        "source_folder_path": "Bookmarks Toolbar / Dev",
                        "source_position": 1,
                        "source_bookmark_id": "abc",
                    },
                    {
                        "url": "https://example.com/b",
                        "title": "B",
                        "collections": ["Bookmarks Toolbar", "Dev"],
                        "source_browser": "firefox-extension",
                        "source_root": "Bookmarks Toolbar",
                        "source_folder_path": "Bookmarks Toolbar / Dev",
                        "source_position": 0,
                        "source_bookmark_id": "def",
                    },
                ]
            )

            self.assertEqual(result["created"], 2)
            bookmark_a = next(bookmark for bookmark in store.list() if bookmark.url == "https://example.com/a")
            self.assertEqual(bookmark_a.source_browser, "firefox-extension")
            self.assertEqual(bookmark_a.source_root, "Bookmarks Toolbar")
            self.assertEqual(bookmark_a.source_folder_path, "Bookmarks Toolbar / Dev")
            self.assertEqual(bookmark_a.source_bookmark_id, "abc")

            export = store.browser_export_tree()

            self.assertEqual(export["bookmark_count"], 2)
            self.assertEqual(export["filters"]["status"], "active")
            self.assertEqual(export["roots"][0]["title"], "Bookmarks Toolbar")
            folder = export["roots"][0]["children"][0]
            self.assertEqual(folder["title"], "Dev")
            self.assertEqual([item["title"] for item in folder["children"]], ["B", "A"])

            filtered = store.browser_export_tree(filters=BookmarkFilters(collection="Other", status="active"))

            self.assertEqual(filtered["bookmark_count"], 0)
            self.assertEqual(filtered["roots"], [])

    def test_import_browser_html_preview_shows_new_existing_and_import_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            existing = store.add({"url": "https://example.com/existing", "title": "Existing"})
            html = """
            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <DL><p>
              <DT><H3>Development</H3>
              <DL><p>
                <DT><A HREF="https://example.com/existing?utm_source=x">Already there</A>
                <DT><A HREF="https://github.com/Nanja-at-web/LinkVault" TAGS="selfhost">LinkVault</A>
                <DT><A HREF="https://github.com/Nanja-at-web/LinkVault?utm_medium=social">LinkVault duplicate</A>
              </DL><p>
            </DL><p>
            """

            preview = store.preview_browser_html_import(html)

            self.assertEqual(preview["total"], 3)
            self.assertEqual(preview["create"], 1)
            self.assertEqual(preview["duplicate_existing"], 1)
            self.assertEqual(preview["duplicate_in_import"], 1)
            self.assertEqual(preview["invalid_skipped"], 0)
            self.assertEqual(preview["records"][0]["duplicate_bookmark"]["id"], existing.id)
            self.assertEqual(preview["records"][1]["collections"], ["Development"])
            self.assertIn("github", preview["records"][1]["suggestions"]["suggested_tags"])
            self.assertEqual(preview["records"][2]["duplicate_of_index"], 2)

    def test_import_preview_and_import_skip_internal_browser_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            html = """
            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <DL><p>
              <DT><A HREF="about:preferences">Firefox Settings</A>
              <DT><A HREF="place:sort=8">Firefox Places</A>
              <DT><A HREF="https://example.com/a">Example A</A>
            </DL><p>
            """

            preview = store.preview_browser_html_import(html)
            result = store.import_browser_html(html)

            self.assertEqual(preview["total"], 3)
            self.assertEqual(preview["create"], 1)
            self.assertEqual(preview["invalid_skipped"], 2)
            self.assertEqual(preview["records"][0]["action"], "invalid_skipped")
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["invalid_skipped"], 2)
            self.assertEqual(store.list()[0].url, "https://example.com/a")

    def test_import_chromium_json_preview_and_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            data = """
            {
              "roots": {
                "bookmark_bar": {
                  "type": "folder",
                  "name": "Bookmarks Bar",
                  "children": [
                    {
                      "type": "folder",
                      "name": "Dev",
                      "children": [
                        {
                          "type": "url",
                          "name": "LinkVault",
                          "url": "https://github.com/Nanja-at-web/LinkVault"
                        },
                        {
                          "type": "url",
                          "name": "LinkVault duplicate",
                          "url": "https://github.com/Nanja-at-web/LinkVault?utm_source=x"
                        }
                      ]
                    }
                  ]
                },
                "other": {
                  "type": "folder",
                  "name": "Other Bookmarks",
                  "children": []
                }
              }
            }
            """

            preview = store.preview_chromium_json_import(data)
            result = store.import_chromium_json(data)

            self.assertEqual(preview["total"], 2)
            self.assertEqual(preview["create"], 1)
            self.assertEqual(preview["duplicate_in_import"], 1)
            self.assertEqual(preview["records"][0]["collections"], ["Bookmarks Bar", "Dev"])
            self.assertIn("github", preview["records"][0]["suggestions"]["suggested_tags"])
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["duplicates_skipped"], 1)
            self.assertEqual(store.list()[0].collections, ["Bookmarks Bar", "Dev"])

    def test_import_firefox_json_preview_and_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            data = """
            {
              "type": "text/x-moz-place-container",
              "title": "root",
              "children": [
                {
                  "type": "text/x-moz-place-container",
                  "title": "Bookmarks Menu",
                  "children": [
                    {
                      "type": "text/x-moz-place-container",
                      "title": "Dev",
                      "children": [
                        {
                          "type": "text/x-moz-place",
                          "title": "LinkVault",
                          "uri": "https://github.com/Nanja-at-web/LinkVault",
                          "tags": "selfhost,bookmarks"
                        },
                        {
                          "type": "text/x-moz-place",
                          "title": "LinkVault duplicate",
                          "uri": "https://github.com/Nanja-at-web/LinkVault?utm_source=firefox"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
            """

            preview = store.preview_firefox_json_import(data)
            result = store.import_firefox_json(data)

            self.assertEqual(preview["total"], 2)
            self.assertEqual(preview["create"], 1)
            self.assertEqual(preview["duplicate_in_import"], 1)
            self.assertEqual(preview["records"][0]["collections"], ["Bookmarks Menu", "Dev"])
            self.assertEqual(preview["records"][0]["tags"], ["bookmarks", "selfhost"])
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["duplicates_skipped"], 1)

    def test_import_safari_zip_preview_and_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            html = """
            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <DL><p>
              <DT><H3>Safari Favorites</H3>
              <DL><p>
                <DT><A HREF="https://example.com/safari">Safari Link</A>
              </DL><p>
            </DL><p>
            """
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w") as zip_archive:
                zip_archive.writestr("Safari Bookmarks/Bookmarks.html", html)
            data = base64.b64encode(archive.getvalue()).decode("ascii")

            preview = store.preview_safari_zip_import(data)
            result = store.import_safari_zip(data)

            self.assertEqual(preview["total"], 1)
            self.assertEqual(preview["create"], 1)
            self.assertEqual(preview["records"][0]["collections"], ["Safari Favorites"])
            self.assertEqual(result["created"], 1)
            self.assertEqual(store.list()[0].url, "https://example.com/safari")

    def test_import_creates_session_and_activity_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)

            result = store.import_browser_bookmarks(
                [
                    {
                        "url": "https://example.com/one",
                        "title": "One",
                        "source_browser": "firefox",
                        "source_folder_path": "Bookmarks Toolbar / Dev",
                        "source_bookmark_id": "abc",
                    },
                    {
                        "url": "https://example.com/one?utm_source=test",
                        "title": "Duplicate",
                        "source_browser": "firefox",
                        "source_folder_path": "Bookmarks Toolbar / Dev",
                        "source_bookmark_id": "def",
                    },
                ],
                session_meta={
                    "source_name": "Companion Extension",
                    "source_format": "browser-bookmarks",
                    "source_file_name": "live-browser-tree",
                    "source_file_checksum_sha256": "hash",
                    "source_profile": "default",
                    "sync_origin": "companion_extension",
                },
            )

            self.assertTrue(result["import_session_id"])
            sessions = store.import_sessions()
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["id"], result["import_session_id"])
            self.assertEqual(sessions[0]["created_count"], 1)
            self.assertEqual(sessions[0]["duplicate_count"], 1)
            self.assertEqual(sessions[0]["source_format"], "browser-bookmarks")
            activity = store.activity_events()
            self.assertEqual(activity[0]["kind"], "import_session_created")
            self.assertIn("Import 1 neu, 1 Dubletten", activity[0]["summary"])
            conflicts = store.conflicts()
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]["kind"], "import_duplicate")
            self.assertEqual(conflicts[0]["state"], "open")
            self.assertEqual(conflicts[0]["details"]["session_id"], result["import_session_id"])

    def test_invalid_import_creates_open_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)

            result = store.import_browser_html(
                """
                <!DOCTYPE NETSCAPE-Bookmark-file-1>
                <DL><p>
                  <DT><A HREF="about:config">Firefox internal</A>
                </DL><p>
                """,
                session_meta={
                    "source_name": "Browser Bookmark HTML",
                    "source_format": "browser-html",
                    "source_file_name": "bookmarks.html",
                },
            )

            self.assertEqual(result["invalid_skipped"], 1)
            conflicts = store.conflicts()
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]["kind"], "import_invalid")
            self.assertEqual(conflicts[0]["state"], "open")

    def test_user_settings_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            uid = "user-test-1"
            default_value = {"view": "compact", "filters": {"status": "active"}}

            missing = store.get_setting(uid, "bookmark_default_view", default_value)
            self.assertFalse(missing["saved"])
            self.assertEqual(missing["value"], default_value)

            saved = store.set_setting(
                uid,
                "bookmark_default_view",
                {
                    "view": "grid",
                    "fields": {"title": True, "notes": False},
                    "filters": {"query": "gh", "status": "all"},
                },
            )
            self.assertTrue(saved["saved"])
            self.assertEqual(saved["value"]["view"], "grid")

            loaded = store.get_setting(uid, "bookmark_default_view", default_value)
            self.assertTrue(loaded["saved"])
            self.assertEqual(loaded["value"]["filters"]["query"], "gh")

            self.assertTrue(store.delete_setting(uid, "bookmark_default_view"))
            deleted = store.get_setting(uid, "bookmark_default_view", default_value)
            self.assertFalse(deleted["saved"])
            self.assertEqual(deleted["value"], default_value)

    def test_user_settings_are_scoped_per_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.set_setting("user-a", "pref", {"view": "grid"})
            store.set_setting("user-b", "pref", {"view": "compact"})

            self.assertEqual(store.get_setting("user-a", "pref")["value"]["view"], "grid")
            self.assertEqual(store.get_setting("user-b", "pref")["value"]["view"], "compact")
            self.assertFalse(store.get_setting("user-c", "pref")["saved"])

    def test_list_settings_filters_by_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            uid = "user-test-1"
            store.set_setting(uid, "bookmark_view.named.Inbox Review", {"name": "Inbox Review"})
            store.set_setting(uid, "bookmark_view.named.Research Grid", {"name": "Research Grid"})
            store.set_setting(uid, "bookmark_default_view", {"view": "compact"})

            named = store.list_settings(uid, "bookmark_view.named.")

            self.assertEqual(len(named), 2)
            self.assertEqual({item["value"]["name"] for item in named}, {"Inbox Review", "Research Grid"})

    def test_dedup_dry_run_preserves_tags_collections_and_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add(
                {
                    "url": "https://example.com/a",
                    "title": "Pinned",
                    "pinned": True,
                    "tags": "keep",
                    "collections": "A",
                }
            )
            loser = store.add(
                {
                    "url": "https://example.com/a?utm_campaign=x",
                    "title": "Loser",
                    "favorite": True,
                    "tags": "merge",
                    "collections": "B",
                }
            )

            dry_run = store.dedup_dry_run()

            self.assertEqual(dry_run["group_count"], 1)
            plan = dry_run["groups"][0]["merge_plan"]
            self.assertEqual(plan["winner_id"], winner.id)
            self.assertEqual(plan["loser_ids"], [loser.id])
            self.assertEqual(plan["move_tags"], ["keep", "merge"])
            self.assertEqual(plan["move_collections"], ["A", "B"])
            self.assertTrue(plan["keep_favorite"])
            self.assertTrue(plan["keep_pinned"])
            self.assertFalse(plan["delete_losers"])
            self.assertEqual(dry_run["groups"][0]["winner"]["id"], winner.id)
            difference_fields = {difference["field"] for difference in dry_run["groups"][0]["differences"]}
            self.assertIn("tags", difference_fields)
            self.assertIn("collections", difference_fields)

    def test_merge_duplicates_updates_winner_and_marks_losers(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add(
                {
                    "url": "https://example.com/a",
                    "title": "Winner",
                    "tags": "keep",
                    "collections": "Inbox",
                    "notes": "Winner note",
                    "pinned": True,
                }
            )
            loser = store.add(
                {
                    "url": "https://example.com/a?utm_source=news",
                    "title": "Loser Unique Title",
                    "tags": "merge",
                    "collections": "Archive",
                    "notes": "Loser note",
                    "favorite": True,
                }
            )

            result = store.merge_duplicates({"winner_id": winner.id, "loser_ids": [loser.id]})

            self.assertEqual(result["deleted"], 0)
            self.assertEqual(result["merged_count"], 1)
            self.assertTrue(result["merge_event_id"])
            updated_winner = store.get(winner.id)
            merged_loser = store.get(loser.id)
            self.assertEqual(updated_winner.tags, ["keep", "merge"])
            self.assertEqual(updated_winner.collections, ["Archive", "Inbox"])
            self.assertTrue(updated_winner.favorite)
            self.assertTrue(updated_winner.pinned)
            self.assertIn("Winner note", updated_winner.notes)
            self.assertIn("Loser note", updated_winner.notes)
            self.assertEqual(merged_loser.status, "merged_duplicate")
            self.assertEqual(merged_loser.merged_into, winner.id)
            self.assertTrue(merged_loser.merged_at)
            self.assertEqual([bookmark.id for bookmark in store.list()], [winner.id])
            self.assertEqual(
                [bookmark.id for bookmark in store.list(filters=BookmarkFilters(status="merged_duplicate"))],
                [loser.id],
            )
            self.assertEqual(
                {bookmark.id for bookmark in store.list(filters=BookmarkFilters(status="all"))},
                {winner.id, loser.id},
            )
            self.assertEqual(store.search("Loser Unique Title"), [])
            self.assertEqual(
                {match["bookmark"]["id"] for match in store.duplicate_preflight(loser.url)["matches"]},
                {winner.id},
            )
            self.assertEqual(store.dedup_dry_run()["group_count"], 0)
            history = store.merge_history()
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["id"], result["merge_event_id"])
            self.assertEqual(history[0]["winner_id"], winner.id)
            self.assertEqual(history[0]["loser_ids"], [loser.id])
            self.assertEqual(history[0]["winner_before"]["notes"], "Winner note")
            self.assertEqual(history[0]["losers_before"][0]["title"], "Loser Unique Title")
            self.assertIn("Loser note", history[0]["winner_after"]["notes"])
            reopened_store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            self.assertEqual(reopened_store.search("Loser Unique Title"), [])
            self.assertEqual(reopened_store.merge_history()[0]["id"], result["merge_event_id"])

    def test_merge_undo_restores_winner_and_losers(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add(
                {
                    "url": "https://example.com/a",
                    "title": "Winner",
                    "tags": "keep",
                    "collections": "Inbox",
                    "notes": "Winner note",
                }
            )
            loser = store.add(
                {
                    "url": "https://example.com/a?utm_source=news",
                    "title": "Loser Unique Title",
                    "tags": "merge",
                    "collections": "Archive",
                    "notes": "Loser note",
                    "favorite": True,
                }
            )

            merge = store.merge_duplicates({"winner_id": winner.id, "loser_ids": [loser.id]})
            undone = store.undo_merge(merge["merge_event_id"])

            self.assertEqual(undone["merge_event_id"], merge["merge_event_id"])
            self.assertEqual(undone["restored_count"], 1)
            restored_winner = store.get(winner.id)
            restored_loser = store.get(loser.id)
            self.assertEqual(restored_winner.notes, "Winner note")
            self.assertEqual(restored_winner.tags, ["keep"])
            self.assertEqual(restored_winner.collections, ["Inbox"])
            self.assertFalse(restored_winner.favorite)
            self.assertEqual(restored_loser.status, "active")
            self.assertEqual(restored_loser.merged_into, "")
            self.assertEqual(restored_loser.title, "Loser Unique Title")
            self.assertEqual(
                {bookmark.id for bookmark in store.list(filters=BookmarkFilters(status="all"))},
                {winner.id, loser.id},
            )
            self.assertEqual([bookmark.id for bookmark in store.search("Loser Unique Title")], [loser.id])
            history = store.merge_history()
            self.assertFalse(history[0]["can_undo"])
            self.assertTrue(history[0]["undone_at"])
            self.assertEqual(store.activity_events()[0]["kind"], "merge_undo")
            with self.assertRaises(ValueError):
                store.undo_merge(merge["merge_event_id"])
            conflicts = store.conflicts(state="all")
            self.assertEqual(conflicts[0]["kind"], "merge_conflict")
            self.assertEqual(conflicts[0]["state"], "open")

    def test_merge_creates_resolved_conflict_and_can_change_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add({"url": "https://example.com/a", "title": "Winner"})
            loser = store.add({"url": "https://example.com/a?utm_source=news", "title": "Loser"})

            merge = store.merge_duplicates({"winner_id": winner.id, "loser_ids": [loser.id]})

            conflicts = store.conflicts(state="all")
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]["kind"], "merge_conflict")
            self.assertEqual(conflicts[0]["source_id"], merge["merge_event_id"])
            self.assertEqual(conflicts[0]["state"], "resolved")

            updated = store.update_conflict_state(conflicts[0]["id"], "ignored")
            self.assertEqual(updated["state"], "ignored")
            self.assertEqual(store.activity_events()[0]["kind"], "conflict_state_changed")

    def test_browser_restore_preview_creates_conflicts_and_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            bookmark = store.add(
                {
                    "url": "https://example.com/docs?a=1&utm_source=news",
                    "title": "Docs",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )

            preview = store.preview_browser_restore(
                [
                    {
                        "id": "browser-1",
                        "title": "Existing Docs",
                        "url": "https://example.com/docs?a=1",
                        "folder_path": "Bookmarks Toolbar / Existing",
                    }
                ],
                duplicate_action="skip",
                target_mode="new",
                target_title="LinkVault Restore",
            )

            self.assertEqual(preview["total"], 1)
            self.assertEqual(preview["conflict_count"], 1)
            self.assertEqual(preview["skip_existing"], 1)
            self.assertTrue(preview["session_id"])
            self.assertEqual(preview["records"][0]["id"], bookmark.id)
            self.assertTrue(preview["records"][0]["conflict_id"])
            self.assertTrue(preview["records"][0]["decision_required"])
            sessions = store.restore_sessions()
            self.assertEqual(sessions[0]["id"], preview["session_id"])
            self.assertEqual(sessions[0]["state"], "previewed")
            self.assertEqual(sessions[0]["conflict_count"], 1)
            self.assertEqual(sessions[0]["conflict_groups"][0]["group_key"], "existing_links")
            self.assertEqual(sessions[0]["conflict_groups"][0]["open_count"], 1)

            conflicts = store.conflicts(state="open")
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]["kind"], "browser_restore_conflict")
            self.assertEqual(conflicts[0]["source_id"], bookmark.id)
            self.assertEqual(conflicts[0]["details"]["selected_action"], "skip_existing")
            self.assertEqual(conflicts[0]["group_key"], "existing_links")

            decided = store.update_conflict_decision(conflicts[0]["id"], "merge")
            self.assertEqual(decided["state"], "resolved")
            self.assertEqual(decided["details"]["selected_action"], "merge_existing")
            self.assertEqual(store.activity_events()[0]["kind"], "conflict_decision_changed")
            self.assertEqual(store.restore_sessions()[0]["conflict_groups"][0]["resolved_count"], 1)

            completed = store.complete_restore_session(
                preview["session_id"],
                created=0,
                skipped_existing=0,
                merged_existing=1,
                updated_existing=0,
                root_title="LinkVault Restore",
            )
            self.assertEqual(completed["state"], "completed")
            self.assertEqual(completed["result"]["merged_existing"], 1)
            self.assertEqual(store.activity_events()[0]["kind"], "browser_restore_completed")

    def test_browser_restore_preview_tracks_folder_structure_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )

            preview = store.preview_browser_restore(
                [],
                existing_folders=[
                    {
                        "id": "folder-root",
                        "title": "LinkVault Restore",
                        "path": "LinkVault Restore",
                        "parent_path": "",
                    },
                    {
                        "id": "folder-child",
                        "title": "Bookmarks Toolbar",
                        "path": "LinkVault Restore / Bookmarks Toolbar",
                        "parent_path": "LinkVault Restore",
                    },
                ],
                duplicate_action="skip",
                target_mode="new",
                target_title="LinkVault Restore",
            )

            self.assertEqual(preview["structure_conflict_count"], 1)
            self.assertTrue(preview["folder_records"])
            self.assertEqual(preview["folder_records"][0]["action"], "folder_create_parallel")
            self.assertTrue(preview["folder_records"][0]["conflict_id"])
            self.assertEqual(preview["records"][0]["resolved_browser_path"][0], "LinkVault Restore (LinkVault)")
            session = store.restore_sessions()[0]
            self.assertEqual(session["structure_conflict_count"], 1)
            self.assertTrue(any(group["group_key"] == "target_root" for group in session["conflict_groups"]))

            all_conflicts = store.conflicts(state="all")
            kinds = {conflict["kind"] for conflict in all_conflicts}
            self.assertIn("browser_restore_structure_conflict", kinds)
            self.assertTrue(any(conflict["group_key"] == "target_root" for conflict in all_conflicts))

    def test_restore_conflict_group_decision_updates_matching_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )
            store.add(
                {
                    "url": "https://example.com/b",
                    "title": "B",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 1,
                }
            )

            preview = store.preview_browser_restore(
                [
                    {"id": "existing-a", "title": "Existing A", "url": "https://example.com/a", "folder_path": "Bookmarks Toolbar / Existing"},
                    {"id": "existing-b", "title": "Existing B", "url": "https://example.com/b", "folder_path": "Bookmarks Toolbar / Existing"},
                ],
                duplicate_action="skip",
                target_mode="new",
                target_title="LinkVault Restore",
            )

            result = store.apply_restore_conflict_group_decision(
                preview["session_id"],
                "existing_links",
                "update",
            )

            self.assertEqual(result["selected_action"], "update_existing")
            self.assertEqual(result["updated_count"], 2)
            self.assertEqual(result["group"]["resolved_count"], 2)
            self.assertEqual(result["group"]["selected_actions"]["update_existing"], 2)
            self.assertEqual(store.activity_events()[0]["kind"], "conflict_group_decision_changed")

    def test_restore_conflict_groups_include_action_previews(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )
            store.add(
                {
                    "url": "https://example.com/b",
                    "title": "B",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 1,
                }
            )

            preview = store.preview_browser_restore(
                [
                    {
                        "id": "existing-a",
                        "title": "Existing A",
                        "url": "https://example.com/a",
                        "folder_path": "Bookmarks Toolbar / Existing",
                    },
                    {
                        "id": "existing-b",
                        "title": "Existing B",
                        "url": "https://example.com/b",
                        "folder_path": "Bookmarks Toolbar / Existing",
                    },
                ],
                existing_folders=[
                    {
                        "id": "folder-root",
                        "title": "LinkVault Restore",
                        "path": "LinkVault Restore",
                        "parent_path": "",
                    },
                    {
                        "id": "folder-child",
                        "title": "Bookmarks Toolbar",
                        "path": "LinkVault Restore / Bookmarks Toolbar",
                        "parent_path": "LinkVault Restore",
                    },
                ],
                duplicate_action="skip",
                target_mode="new",
                target_title="LinkVault Restore",
            )

            groups = {
                group["group_key"]: group
                for group in store.restore_session_conflict_groups(preview["session_id"])
            }

            self.assertIn("existing_links", groups)
            self.assertIn("target_root", groups)

            link_preview = groups["existing_links"]["action_previews"]["update_existing"]
            self.assertEqual(link_preview["count"], 2)
            self.assertEqual(link_preview["effects"]["update_existing_link"], 2)
            self.assertIn("Bookmarks Toolbar / Existing", link_preview["path_examples"])

            structure_preview = groups["target_root"]["action_previews"]["folder_create_parallel"]
            self.assertEqual(structure_preview["count"], 1)
            self.assertEqual(structure_preview["effects"]["create_parallel_root"], 1)
            self.assertTrue(
                any("LinkVault Restore (LinkVault)" in path for path in structure_preview["path_examples"])
            )

    def test_inactive_bookmarks_are_not_reindexed_by_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add({"url": "https://example.com/a", "title": "Winner"})
            loser = store.add({"url": "https://example.com/a?utm_source=news", "title": "Loser Unique Title"})

            store.merge_duplicates({"winner_id": winner.id, "loser_ids": [loser.id]})
            updated_loser = store.update(loser.id, {"title": "Still Hidden"}, enrich_metadata=False)

            self.assertEqual(updated_loser.status, "merged_duplicate")
            self.assertEqual(store.search("Still Hidden"), [])
            self.assertEqual(
                [bookmark.id for bookmark in store.search("Still Hidden", filters=BookmarkFilters(status="merged_duplicate"))],
                [loser.id],
            )
            self.assertEqual(
                [bookmark.id for bookmark in store.list(filters=BookmarkFilters(status="merged_duplicate"))],
                [loser.id],
            )

    def test_duplicate_preflight_finds_exact_normalized_and_similar_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            exact = store.add({"url": "https://example.com/a", "title": "Exact"})
            normalized = store.add({"url": "https://example.com/b?utm_source=news", "title": "Normalized"})
            similar = store.add({"url": "https://example.com/docs/linkvault-install", "title": "Similar"})
            store.add({"url": "https://other.test/docs/linkvault-install", "title": "Other domain"})

            exact_preflight = store.duplicate_preflight("https://example.com/a")
            self.assertEqual(exact_preflight["matches"][0]["bookmark"]["id"], exact.id)
            self.assertEqual(exact_preflight["matches"][0]["match_type"], "exact_url")

            normalized_preflight = store.duplicate_preflight("https://example.com/b")
            self.assertEqual(normalized_preflight["matches"][0]["bookmark"]["id"], normalized.id)
            self.assertEqual(normalized_preflight["matches"][0]["match_type"], "normalized_url")

            similar_preflight = store.duplicate_preflight("https://example.com/docs/linkvault-installation")
            self.assertTrue(similar_preflight["has_matches"])
            self.assertEqual(similar_preflight["matches"][0]["bookmark"]["id"], similar.id)
            self.assertEqual(similar_preflight["matches"][0]["match_type"], "similar_url")

    def test_metadata_fills_missing_title_description_and_favicon(self):
        def fake_fetcher(url: str) -> PageMetadata:
            return PageMetadata(
                title="Fetched Title",
                description="Fetched description",
                favicon_url="https://example.com/favicon.ico",
                final_url=url,
            )

        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=fake_fetcher)

            bookmark = store.add({"url": "https://example.com/page"})

            self.assertEqual(bookmark.title, "Fetched Title")
            self.assertEqual(bookmark.description, "Fetched description")
            self.assertEqual(bookmark.favicon_url, "https://example.com/favicon.ico")

    def test_search_matches_title_description_domain_tags_and_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            first = store.add(
                {
                    "url": "https://github.com/Nanja-at-web/LinkVault",
                    "title": "LinkVault",
                    "description": "Selfhosted bookmark manager",
                    "tags": "github,selfhost",
                    "collections": "Development",
                }
            )
            store.add({"url": "https://example.com", "title": "Other"})

            results = store.search("github selfhost")

            self.assertEqual([bookmark.id for bookmark in results], [first.id])

    def test_list_tags_returns_counts_sorted_by_frequency(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://a.example.com", "title": "A", "tags": "python,selfhost"})
            store.add({"url": "https://b.example.com", "title": "B", "tags": "python,devops"})
            store.add({"url": "https://c.example.com", "title": "C", "tags": "selfhost"})

            tags = store.list_tags()

            tag_names = [t["tag"] for t in tags]
            self.assertIn("python", tag_names)
            self.assertIn("selfhost", tag_names)
            self.assertIn("devops", tag_names)
            python_entry = next(t for t in tags if t["tag"] == "python")
            selfhost_entry = next(t for t in tags if t["tag"] == "selfhost")
            devops_entry = next(t for t in tags if t["tag"] == "devops")
            self.assertEqual(python_entry["count"], 2)
            self.assertEqual(selfhost_entry["count"], 2)
            self.assertEqual(devops_entry["count"], 1)
            # Higher counts come first; ties broken alphabetically
            self.assertLess(tag_names.index("devops"), len(tag_names))
            self.assertGreater(tag_names.index("devops"), tag_names.index("python"))

    def test_list_tags_counts_active_bookmarks_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add({"url": "https://example.com/a", "title": "Winner", "tags": "shared"})
            loser = store.add({"url": "https://example.com/a?x=1", "title": "Loser", "tags": "shared"})

            # Before merge: shared appears on 2 active bookmarks
            tags_before = store.list_tags()
            shared_before = next(t for t in tags_before if t["tag"] == "shared")
            self.assertEqual(shared_before["count"], 2)

            store.merge_duplicates({"winner_id": winner.id, "loser_ids": [loser.id]})

            # After merge: loser is inactive, shared only counted once (on the winner)
            tags_after = store.list_tags()
            shared_after = next(t for t in tags_after if t["tag"] == "shared")
            self.assertEqual(shared_after["count"], 1)

    def test_list_collections_returns_counts_sorted_by_frequency(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://a.example.com", "title": "A", "collections": "Dev,Research"})
            store.add({"url": "https://b.example.com", "title": "B", "collections": "Dev,Tools"})
            store.add({"url": "https://c.example.com", "title": "C", "collections": "Research"})

            colls = store.list_collections()

            coll_names = [c["collection"] for c in colls]
            self.assertIn("Dev", coll_names)
            self.assertIn("Research", coll_names)
            self.assertIn("Tools", coll_names)
            dev_entry = next(c for c in colls if c["collection"] == "Dev")
            research_entry = next(c for c in colls if c["collection"] == "Research")
            tools_entry = next(c for c in colls if c["collection"] == "Tools")
            self.assertEqual(dev_entry["count"], 2)
            self.assertEqual(research_entry["count"], 2)
            self.assertEqual(tools_entry["count"], 1)
            self.assertGreater(coll_names.index("Tools"), coll_names.index("Dev"))

    def test_list_collections_counts_active_bookmarks_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            winner = store.add({"url": "https://example.com/a", "title": "Winner", "collections": "Shared"})
            loser = store.add({"url": "https://example.com/a?x=1", "title": "Loser", "collections": "Shared"})

            # Before merge: Shared appears on 2 active bookmarks
            colls_before = store.list_collections()
            shared_before = next(c for c in colls_before if c["collection"] == "Shared")
            self.assertEqual(shared_before["count"], 2)

            store.merge_duplicates({"winner_id": winner.id, "loser_ids": [loser.id]})

            # After merge: loser is inactive, Shared only counted once (on the winner)
            colls_after = store.list_collections()
            shared_after = next(c for c in colls_after if c["collection"] == "Shared")
            self.assertEqual(shared_after["count"], 1)

    def test_search_filters_by_flags_domain_tag_and_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            match = store.add(
                {
                    "url": "https://github.com/Nanja-at-web/LinkVault",
                    "title": "LinkVault",
                    "description": "Selfhosted bookmark vault",
                    "tags": "selfhost,github",
                    "collections": "Development",
                    "favorite": True,
                    "pinned": True,
                }
            )
            store.add(
                {
                    "url": "https://github.com/other/project",
                    "title": "Other vault",
                    "description": "Selfhosted bookmark vault",
                    "tags": "selfhost",
                    "collections": "Archive",
                    "favorite": True,
                    "pinned": False,
                }
            )

            results = store.search(
                "bookmark",
                filters=BookmarkFilters(
                    favorite=True,
                    pinned=True,
                    domain="github.com",
                    tag="github",
                    collection="Development",
                ),
            )

            self.assertEqual([bookmark.id for bookmark in results], [match.id])

    def test_filters_work_without_search_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            match = store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "tags": "docs",
                    "collections": "Inbox",
                    "favorite": True,
                }
            )
            store.add({"url": "https://example.com/b", "title": "B", "tags": "docs", "collections": "Archive"})

            results = store.list(filters=BookmarkFilters(favorite=True, tag="docs", collection="Inbox"))

            self.assertEqual([bookmark.id for bookmark in results], [match.id])

    def test_search_index_updates_after_update_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            bookmark = store.add({"url": "https://example.com/a", "title": "Before"})

            self.assertEqual(store.search("after"), [])
            store.update(bookmark.id, {"title": "After"})
            self.assertEqual([item.id for item in store.search("after")], [bookmark.id])

            self.assertTrue(store.delete(bookmark.id))
            self.assertEqual(store.search("after"), [])

    def test_bulk_update_tags_collections_and_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            first = store.add({"url": "https://example.com/a", "title": "A", "tags": "old, keep"})
            second = store.add({"url": "https://example.com/b", "title": "B", "tags": "old"})

            result = store.bulk_update(
                {
                    "ids": [first.id, second.id, "missing"],
                    "add_tags": "new",
                    "remove_tags": "old",
                    "set_collections": "Inbox, Reading",
                    "favorite": True,
                    "pinned": True,
                }
            )

            self.assertEqual(result["updated"], 2)
            self.assertEqual(result["not_found"], 1)
            updated_first = store.get(first.id)
            updated_second = store.get(second.id)
            self.assertEqual(updated_first.tags, ["keep", "new"])
            self.assertEqual(updated_second.tags, ["new"])
            self.assertEqual(updated_first.collections, ["Inbox", "Reading"])
            self.assertTrue(updated_first.favorite)
            self.assertTrue(updated_second.pinned)
            self.assertEqual({item.id for item in store.search("new")}, {first.id, second.id})

    def test_bulk_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            first = store.add({"url": "https://example.com/a", "title": "A"})
            second = store.add({"url": "https://example.com/b", "title": "B"})

            result = store.bulk_update({"ids": [first.id, second.id, "missing"], "delete": True})

            self.assertEqual(result["deleted"], 2)
            self.assertEqual(result["not_found"], 1)
            self.assertEqual(store.list(), [])
            self.assertEqual(store.activity_events()[0]["kind"], "bulk_delete")

    def test_get_restore_session_returns_session_with_conflict_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )
            preview = store.preview_browser_restore(
                [{"id": "ext-a", "title": "A", "url": "https://example.com/a", "folder_path": "Research"}],
                duplicate_action="skip",
                target_mode="new",
                target_title="Restore",
            )
            session_id = preview["session_id"]

            session = store.get_restore_session(session_id)

            self.assertIsNotNone(session)
            self.assertEqual(session["id"], session_id)
            self.assertIn("conflict_groups", session)
            self.assertTrue(len(session["conflict_groups"]) > 0)
            self.assertIsNone(store.get_restore_session("nonexistent"))

    def test_apply_session_defaults_resolves_open_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )
            store.add(
                {
                    "url": "https://example.com/b",
                    "title": "B",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 1,
                }
            )
            preview = store.preview_browser_restore(
                [
                    {"id": "ext-a", "title": "A", "url": "https://example.com/a", "folder_path": "Research"},
                    {"id": "ext-b", "title": "B", "url": "https://example.com/b", "folder_path": "Research"},
                ],
                duplicate_action="skip",
                target_mode="new",
                target_title="Restore",
            )
            session_id = preview["session_id"]
            # Before: 2 open conflicts
            groups_before = store.restore_session_conflict_groups(session_id)
            open_before = sum(g["open_count"] for g in groups_before)
            self.assertEqual(open_before, 2)

            result = store.apply_session_defaults(session_id)

            self.assertEqual(result["session_id"], session_id)
            self.assertEqual(result["resolved_count"], 2)
            self.assertEqual(result["skipped_count"], 0)
            # After: all resolved
            groups_after = store.restore_session_conflict_groups(session_id)
            open_after = sum(g["open_count"] for g in groups_after)
            self.assertEqual(open_after, 0)
            resolved_after = sum(g["resolved_count"] for g in groups_after)
            self.assertEqual(resolved_after, 2)
            self.assertEqual(store.activity_events()[0]["kind"], "session_defaults_applied")

    def test_apply_session_defaults_uses_suggested_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add(
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "source_root": "Bookmarks Toolbar",
                    "source_folder_path": "Bookmarks Toolbar / Research",
                    "source_position": 0,
                }
            )
            preview = store.preview_browser_restore(
                [{"id": "ext-a", "title": "A", "url": "https://example.com/a", "folder_path": "Research"}],
                duplicate_action="merge",  # suggested = merge_existing
                target_mode="new",
                target_title="Restore",
            )
            session_id = preview["session_id"]

            result = store.apply_session_defaults(session_id)

            self.assertEqual(result["resolved_count"], 1)
            # The resolved conflict should use the suggested action (merge_existing)
            groups = store.restore_session_conflict_groups(session_id)
            link_group = next(g for g in groups if g["group_key"] == "existing_links")
            self.assertIn("merge_existing", link_group["selected_actions"])


    def test_record_sync_snapshot_stores_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            items = [
                {"url": "https://example.com/a", "title": "A", "folder_path": "Research"},
                {"url": "https://example.com/b", "title": "B", "folder_path": "Work"},
            ]

            result = store.record_sync_snapshot(items, source_session_id="sess-123")

            self.assertIn("id", result)
            self.assertEqual(result["item_count"], 2)
            self.assertIn("created_at", result)
            snapshot = store.get_latest_sync_snapshot()
            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot["item_count"], 2)
            self.assertEqual(snapshot["source_session_id"], "sess-123")
            self.assertIsNone(store.get_latest_sync_snapshot()  # second call returns same
                              if False else None)
            self.assertEqual(store.activity_events()[0]["kind"], "sync_snapshot_recorded")

    def test_compute_sync_drift_detects_all_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            # Add active bookmarks in LinkVault
            store.add({"url": "https://example.com/lv-only", "title": "LV Only"})
            store.add({"url": "https://example.com/shared", "title": "Shared"})

            # Snapshot: shared + deleted
            snapshot_items = [
                {"url": "https://example.com/shared", "title": "Shared", "folder_path": "Work"},
                {"url": "https://example.com/deleted", "title": "Deleted", "folder_path": "Work"},
            ]
            store.record_sync_snapshot(snapshot_items)

            # Current browser: shared (title changed) + new item
            current_items = [
                {"url": "https://example.com/shared", "title": "Shared Updated", "folder_path": "Work"},
                {"url": "https://example.com/new-in-browser", "title": "New In Browser", "folder_path": "Work"},
            ]

            drift = store.compute_sync_drift(current_items)

            # deleted_from_browser: "deleted" was in snapshot, not in current
            self.assertEqual(drift["deleted_from_browser"]["count"], 1)
            self.assertEqual(drift["deleted_from_browser"]["items"][0]["url"], "https://example.com/deleted")
            # added_to_browser: "new-in-browser" in current, not in snapshot
            self.assertEqual(drift["added_to_browser"]["count"], 1)
            self.assertEqual(drift["added_to_browser"]["items"][0]["url"], "https://example.com/new-in-browser")
            # diverged: "shared" title changed
            self.assertEqual(drift["diverged"]["count"], 1)
            self.assertEqual(drift["diverged"]["items"][0]["changes"][0]["field"], "title")
            # linkvault_only: "lv-only" not in current browser at all
            self.assertEqual(drift["linkvault_only"]["count"], 1)
            self.assertEqual(drift["linkvault_only"]["items"][0]["url"], "https://example.com/lv-only")
            self.assertTrue(drift["has_drift"])

    def test_compute_sync_drift_no_drift_when_states_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            items = [
                {"url": "https://example.com/a", "title": "A", "folder_path": "Work"},
            ]
            store.record_sync_snapshot(items)

            drift = store.compute_sync_drift(items)

            self.assertFalse(drift["has_drift"])
            self.assertEqual(drift["deleted_from_browser"]["count"], 0)
            self.assertEqual(drift["added_to_browser"]["count"], 0)
            self.assertEqual(drift["diverged"]["count"], 0)

    def test_compute_sync_drift_raises_without_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)

            with self.assertRaises(ValueError):
                store.compute_sync_drift([])

    def test_list_sorts_by_title_ascending(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://z-last.com", "title": "Zeppelin"})
            store.add({"url": "https://a-first.com", "title": "Alpha"})
            store.add({"url": "https://m-middle.com", "title": "Middle"})

            filters = BookmarkFilters(sort_by="title", sort_order="asc")
            results = store.list(filters=filters)

            titles = [b.title for b in results]
            self.assertEqual(titles, ["Alpha", "Middle", "Zeppelin"])

    def test_list_sorts_by_title_descending(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://z-last.com", "title": "Zeppelin"})
            store.add({"url": "https://a-first.com", "title": "Alpha"})
            store.add({"url": "https://m-middle.com", "title": "Middle"})

            filters = BookmarkFilters(sort_by="title", sort_order="desc")
            results = store.list(filters=filters)

            titles = [b.title for b in results]
            self.assertEqual(titles, ["Zeppelin", "Middle", "Alpha"])

    def test_list_sorts_by_domain_ascending(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://z-example.com/page", "title": "Z"})
            store.add({"url": "https://a-example.com/page", "title": "A"})

            filters = BookmarkFilters(sort_by="domain", sort_order="asc")
            results = store.list(filters=filters)

            domains = [b.domain for b in results]
            self.assertEqual(domains[0], "a-example.com")
            self.assertEqual(domains[-1], "z-example.com")

    def test_list_default_sort_is_created_at_desc(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            first = store.add({"url": "https://first.com", "title": "First"})
            second = store.add({"url": "https://second.com", "title": "Second"})

            results = store.list()

            # newest first by default
            self.assertEqual(results[0].id, second.id)
            self.assertEqual(results[1].id, first.id)

    def test_invalid_sort_field_falls_back_to_created_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://example.com", "title": "Test"})

            # Should not raise; falls back to created_at
            filters = BookmarkFilters(sort_by="invalid_column", sort_order="asc")
            results = store.list(filters=filters)

            self.assertEqual(len(results), 1)

    # ------------------------------------------------------------------
    # favorites_report tests
    # ------------------------------------------------------------------

    def test_favorites_report_empty_when_no_favorites(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://example.com", "title": "Not a favorite"})

            report = store.favorites_report()

            self.assertEqual(report["uncategorized"], [])
            self.assertEqual(report["duplicated"], [])
            self.assertEqual(report["dead"], [])
            self.assertEqual(report["check_summary"]["total_favorites"], 0)

    def test_favorites_report_uncategorized_inbox_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            # Favorite with only Inbox (default for new bookmarks)
            store.add({"url": "https://example.com", "title": "In Inbox", "favorite": True})
            # Favorite with a real collection — should NOT be uncategorized
            store.add({"url": "https://other.com", "title": "Categorized", "favorite": True,
                        "collections": ["Homelab"]})

            report = store.favorites_report()

            uncategorized_urls = [b["url"] for b in report["uncategorized"]]
            self.assertIn("https://example.com", uncategorized_urls)
            self.assertNotIn("https://other.com", uncategorized_urls)

    def test_favorites_report_duplicated_same_normalized_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://example.com/a?utm_source=x", "title": "A1", "favorite": True})
            store.add({"url": "https://example.com/a", "title": "A2", "favorite": True})
            # Non-favorite — should not appear in duplicated
            store.add({"url": "https://example.com/a?ref=y", "title": "A3", "favorite": False})

            report = store.favorites_report()

            self.assertEqual(len(report["duplicated"]), 1)
            group = report["duplicated"][0]
            self.assertEqual(len(group["bookmarks"]), 2)

    def test_favorites_report_not_duplicated_when_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://alpha.com", "title": "Alpha", "favorite": True})
            store.add({"url": "https://beta.com", "title": "Beta", "favorite": True})

            report = store.favorites_report()

            self.assertEqual(report["duplicated"], [])

    def test_favorites_report_dead_requires_link_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://example.com", "title": "Example", "favorite": True})

            # No link check run yet — dead list must be empty
            report = store.favorites_report()

            self.assertEqual(report["dead"], [])
            self.assertEqual(report["check_summary"]["total_checked"], 0)

    def test_favorites_report_check_summary_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://a.com", "title": "A", "favorite": True})
            store.add({"url": "https://b.com", "title": "B", "favorite": True})

            report = store.favorites_report()

            self.assertEqual(report["check_summary"]["total_favorites"], 2)

    # ------------------------------------------------------------------
    # collection_care_scores tests
    # ------------------------------------------------------------------

    def test_collection_care_scores_empty_when_no_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            # All in Inbox — should produce no scores
            store.add({"url": "https://example.com", "title": "X"})

            scores = store.collection_care_scores()

            self.assertEqual(scores, [])

    def test_collection_care_scores_returns_score_per_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://a.com", "title": "A", "description": "desc",
                        "tags": ["x"], "collections": ["Homelab"]})
            store.add({"url": "https://b.com", "title": "B", "description": "desc",
                        "tags": ["y"], "collections": ["Research"]})

            scores = store.collection_care_scores()

            collections = [s["collection"] for s in scores]
            self.assertIn("Homelab", collections)
            self.assertIn("Research", collections)
            for s in scores:
                self.assertIn("score", s)
                self.assertIn("factors", s)
                self.assertGreaterEqual(s["score"], 0)
                self.assertLessEqual(s["score"], 100)

    def test_collection_care_scores_penalizes_missing_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            # Full metadata
            store.add({"url": "https://full.com", "title": "Full", "description": "Has description",
                        "tags": ["x"], "collections": ["Good"]})
            # No description
            store.add({"url": "https://empty.com", "title": "No desc",
                        "tags": ["x"], "collections": ["Poor"]})

            scores = store.collection_care_scores()
            score_map = {s["collection"]: s for s in scores}

            self.assertGreater(score_map["Good"]["score"], score_map["Poor"]["score"])

    def test_collection_care_scores_penalizes_dedup_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            # Two bookmarks with same normalized URL in same collection = dedup penalty
            # utm_source is stripped by normalize_url, so both become the same normalized URL
            store.add({"url": "https://dup.com/page?utm_source=newsletter", "title": "Dup1", "description": "d",
                        "tags": ["t"], "collections": ["Duped"]})
            store.add({"url": "https://dup.com/page", "title": "Dup2", "description": "d",
                        "tags": ["t"], "collections": ["Duped"]})
            # Clean collection
            store.add({"url": "https://clean.com", "title": "Clean", "description": "d",
                        "tags": ["t"], "collections": ["Clean"]})

            scores = store.collection_care_scores()
            score_map = {s["collection"]: s for s in scores}

            self.assertLess(score_map["Duped"]["factors"]["dedup"], 100)
            self.assertEqual(score_map["Clean"]["factors"]["dedup"], 100)

    def test_collection_care_scores_sorted_ascending(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.add({"url": "https://a.com", "title": "A", "description": "d",
                        "tags": ["t"], "collections": ["Good"]})
            store.add({"url": "https://b.com", "title": "", "collections": ["Poor"]})

            scores = store.collection_care_scores()

            # Worst first
            score_values = [s["score"] for s in scores]
            self.assertEqual(score_values, sorted(score_values))


from linkvault.store import (
    _lz4_block_decompress,
    decompress_mozlz4,
    parse_firefox_jsonlz4,
    infer_generic_columns,
    parse_generic_csv,
    parse_generic_json,
    parse_browser_html,
    MOZLZ4_MAGIC,
)


class MozLz4Test(unittest.TestCase):
    def _compress_lz4_block(self, data: bytes) -> bytes:
        """Minimal LZ4 block: emit all bytes as a single literal sequence (no matches)."""
        out = bytearray()
        n = len(data)
        # Token: high nibble = min(n, 15), low nibble = 0 (no match)
        if n < 15:
            out.append(n << 4)
        else:
            out.append(0xF0)  # 15 in high nibble
            remainder = n - 15
            while remainder >= 255:
                out.append(255)
                remainder -= 255
            out.append(remainder)
        out.extend(data)
        # No match offset — this is the last (and only) sequence
        return bytes(out)

    def test_lz4_block_decompress_roundtrip(self):
        original = b"Hello, LinkVault! " * 10
        compressed = self._compress_lz4_block(original)
        result = _lz4_block_decompress(compressed)
        self.assertEqual(result, original)

    def test_decompress_mozlz4_rejects_bad_magic(self):
        with self.assertRaises(ValueError):
            decompress_mozlz4(b"badmagic" + b"\x00" * 8)

    def test_decompress_mozlz4_roundtrip(self):
        payload = b"Firefox bookmark data"
        compressed = self._compress_lz4_block(payload)
        mozlz4 = MOZLZ4_MAGIC + compressed
        result = decompress_mozlz4(mozlz4)
        self.assertEqual(result, payload)

    def test_parse_firefox_jsonlz4_roundtrip(self):
        """Full parse: compress a minimal Firefox bookmarks JSON as MozLZ4."""
        import json, struct

        firefox_json = json.dumps({
            "guid": "root",
            "title": "Root",
            "type": "text/x-moz-place-container",
            "children": [
                {
                    "guid": "abc123",
                    "title": "Bookmarks Toolbar",
                    "type": "text/x-moz-place-container",
                    "children": [
                        {
                            "guid": "bm1",
                            "title": "LinkVault",
                            "type": "text/x-moz-place",
                            "uri": "https://linkvault.example.com",
                        }
                    ],
                }
            ],
        }).encode()
        compressed = self._compress_lz4_block(firefox_json)
        mozlz4 = MOZLZ4_MAGIC + compressed
        b64 = base64.b64encode(mozlz4).decode()

        items = parse_firefox_jsonlz4(b64)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://linkvault.example.com")
        self.assertEqual(items[0]["title"], "LinkVault")

    def test_parse_firefox_jsonlz4_rejects_invalid_base64(self):
        with self.assertRaises(ValueError):
            parse_firefox_jsonlz4("not-base64!!!")

    def test_parse_firefox_jsonlz4_rejects_bad_magic(self):
        bad = base64.b64encode(b"not-a-mozlz4-file").decode()
        with self.assertRaises(ValueError):
            parse_firefox_jsonlz4(bad)


class GenericImportTest(unittest.TestCase):
    def test_infer_generic_columns_url(self):
        headers = ["url", "title", "tags", "notes"]
        inferred = infer_generic_columns(headers)
        self.assertEqual(inferred["url"], "url")
        self.assertEqual(inferred["title"], "title")
        self.assertEqual(inferred["notes"], "notes")

    def test_infer_generic_columns_aliases(self):
        headers = ["href", "name", "keywords", "folder"]
        inferred = infer_generic_columns(headers)
        self.assertEqual(inferred["url"], "href")
        self.assertEqual(inferred["title"], "name")
        self.assertEqual(inferred["tags"], "keywords")
        self.assertEqual(inferred["collections"], "folder")

    def test_infer_generic_columns_missing_returns_none(self):
        headers = ["url"]
        inferred = infer_generic_columns(headers)
        self.assertIsNone(inferred["title"])
        self.assertIsNone(inferred["tags"])

    def test_parse_generic_csv_basic(self):
        csv_data = "url,title,tags\nhttps://a.com,Alpha,news;tech\nhttps://b.com,Beta,\n"
        mapping = {"url": "url", "title": "title", "tags": "tags"}
        items = parse_generic_csv(csv_data, mapping)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["url"], "https://a.com")
        self.assertEqual(items[0]["title"], "Alpha")
        self.assertIn("news", items[0]["tags"])
        self.assertIn("tech", items[0]["tags"])

    def test_parse_generic_csv_requires_url_field(self):
        with self.assertRaises(ValueError):
            parse_generic_csv("url,title\nhttps://a.com,A\n", {})

    def test_parse_generic_csv_skips_empty_urls(self):
        csv_data = "url,title\nhttps://a.com,A\n,No URL\n"
        items = parse_generic_csv(csv_data, {"url": "url"})
        self.assertEqual(len(items), 1)

    def test_parse_generic_json_list(self):
        import json
        data = json.dumps([
            {"url": "https://a.com", "title": "A", "tags": ["news", "tech"]},
            {"url": "https://b.com", "title": "B"},
        ])
        mapping = {"url": "url", "title": "title", "tags": "tags"}
        items = parse_generic_json(data, mapping)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["url"], "https://a.com")
        self.assertIn("news", items[0]["tags"])

    def test_parse_generic_json_dict_with_list_value(self):
        import json
        data = json.dumps({"bookmarks": [{"url": "https://a.com", "title": "A"}]})
        mapping = {"url": "url", "title": "title"}
        items = parse_generic_json(data, mapping)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://a.com")

    def test_parse_generic_json_requires_url_field(self):
        with self.assertRaises(ValueError):
            parse_generic_json("[]", {})

    def test_parse_generic_json_string_tags(self):
        import json
        data = json.dumps([{"url": "https://a.com", "tags": "news,tech"}])
        mapping = {"url": "url", "tags": "tags"}
        items = parse_generic_json(data, mapping)
        self.assertIn("news", items[0]["tags"])
        self.assertIn("tech", items[0]["tags"])


class SafariReadingListTest(unittest.TestCase):
    def test_reading_list_folder_tagged(self):
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
  <DT><H3 READING_LIST="true">Reading List</H3>
  <DL><p>
    <DT><A HREF="https://a.com" TOREADLIST="true">Article A</A>
    <DT><A HREF="https://b.com">Article B</A>
  </DL>
</DL>"""
        items = parse_browser_html(html)
        urls = {item["url"]: item for item in items}
        self.assertIn("reading-list", urls["https://a.com"]["tags"])
        self.assertIn("reading-list", urls["https://b.com"]["tags"])

    def test_non_reading_list_not_tagged(self):
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
  <DT><H3>Bookmarks Bar</H3>
  <DL><p>
    <DT><A HREF="https://a.com">Normal</A>
  </DL>
</DL>"""
        items = parse_browser_html(html)
        self.assertNotIn("reading-list", items[0]["tags"])

    def test_toreadlist_attr_on_a_tag(self):
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
  <DT><H3>Misc</H3>
  <DL><p>
    <DT><A HREF="https://c.com" TOREADLIST="true">Want to read</A>
    <DT><A HREF="https://d.com">Normal</A>
  </DL>
</DL>"""
        items = parse_browser_html(html)
        urls = {item["url"]: item for item in items}
        self.assertIn("reading-list", urls["https://c.com"]["tags"])
        self.assertNotIn("reading-list", urls["https://d.com"]["tags"])


if __name__ == "__main__":
    unittest.main()
