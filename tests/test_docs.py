from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_browser_bookmark_ux_patterns_document_filter_boundaries(self):
        text = (ROOT / "docs" / "BROWSER_BOOKMARK_UX_PATTERNS.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Companion Extension Filter", text)
        self.assertIn("Adresse/Domain", text)
        self.assertIn("History-Enrichment", text)
        self.assertIn("Keine vollstaendige Browser-History", text)

    def test_companion_plan_mentions_optional_history_enrichment(self):
        text = (ROOT / "docs" / "COMPANION_EXTENSION.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Filtermodell", text)
        self.assertIn("history", text)
        self.assertIn("Passwoerter/Autofill/Cookies/History nein", text)


if __name__ == "__main__":
    unittest.main()
