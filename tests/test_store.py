import tempfile
import unittest
from pathlib import Path

from linkvault.store import BookmarkStore


class StoreTest(unittest.TestCase):
    def test_dedup_groups_exact_normalized_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = BookmarkStore(Path(tmp) / "bookmarks.json")
            first = store.add({"url": "https://example.com/a?utm_source=news", "title": "A"})
            second = store.add({"url": "https://example.com/a", "title": "A again", "favorite": True})

            groups = store.dedup_groups()

            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["winner_id"], second.id)
            self.assertEqual({item["id"] for item in groups[0]["items"]}, {first.id, second.id})


if __name__ == "__main__":
    unittest.main()
