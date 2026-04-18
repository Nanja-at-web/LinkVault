import tempfile
import unittest
from pathlib import Path

from linkvault.store import BookmarkStore


class StoreTest(unittest.TestCase):
    def test_dedup_groups_exact_normalized_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3")
            first = store.add({"url": "https://example.com/a?utm_source=news", "title": "A"})
            second = store.add({"url": "https://example.com/a", "title": "A again", "favorite": True})

            groups = store.dedup_groups()

            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["winner_id"], second.id)
            self.assertEqual({item["id"] for item in groups[0]["items"]}, {first.id, second.id})

    def test_update_and_delete_bookmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3")
            bookmark = store.add({"url": "https://example.com", "title": "Example"})

            updated = store.update(bookmark.id, {"favorite": True, "tags": "docs, test"})

            self.assertIsNotNone(updated)
            self.assertTrue(updated.favorite)
            self.assertEqual(updated.tags, ["docs", "test"])
            self.assertTrue(store.delete(bookmark.id))
            self.assertIsNone(store.get(bookmark.id))

    def test_import_browser_html_skips_duplicates_and_keeps_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3")
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
            bookmarks = store.list()
            self.assertEqual(len(bookmarks), 1)
            self.assertEqual(bookmarks[0].collections, ["Homelab"])
            self.assertEqual(bookmarks[0].tags, ["proxmox", "selfhost"])

    def test_dedup_dry_run_preserves_tags_collections_and_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "linkvault.sqlite3")
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


if __name__ == "__main__":
    unittest.main()
