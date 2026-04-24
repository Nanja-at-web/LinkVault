import base64
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from linkvault.metadata import PageMetadata
from linkvault.store import BookmarkFilters, BookmarkStore


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
            default_value = {"view": "compact", "filters": {"status": "active"}}

            missing = store.get_setting("bookmark_default_view", default_value)
            self.assertFalse(missing["saved"])
            self.assertEqual(missing["value"], default_value)

            saved = store.set_setting(
                "bookmark_default_view",
                {
                    "view": "grid",
                    "fields": {"title": True, "notes": False},
                    "filters": {"query": "gh", "status": "all"},
                },
            )
            self.assertTrue(saved["saved"])
            self.assertEqual(saved["value"]["view"], "grid")

            loaded = store.get_setting("bookmark_default_view", default_value)
            self.assertTrue(loaded["saved"])
            self.assertEqual(loaded["value"]["filters"]["query"], "gh")

            self.assertTrue(store.delete_setting("bookmark_default_view"))
            deleted = store.get_setting("bookmark_default_view", default_value)
            self.assertFalse(deleted["saved"])
            self.assertEqual(deleted["value"], default_value)

    def test_list_settings_filters_by_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3", metadata_fetcher=None)
            store.set_setting("bookmark_view.named.Inbox Review", {"name": "Inbox Review"})
            store.set_setting("bookmark_view.named.Research Grid", {"name": "Research Grid"})
            store.set_setting("bookmark_default_view", {"view": "compact"})

            named = store.list_settings("bookmark_view.named.")

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


if __name__ == "__main__":
    unittest.main()
