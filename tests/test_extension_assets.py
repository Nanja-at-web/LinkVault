import json
import unittest
from pathlib import Path


EXTENSION_DIR = Path(__file__).resolve().parents[1] / "extensions" / "linkvault-companion"


class ExtensionAssetsTest(unittest.TestCase):
    def test_manifest_and_core_assets_exist(self):
        expected_files = [
            "manifest.json",
            "shared.js",
            "popup.html",
            "popup.js",
            "options.html",
            "options.js",
            "styles.css",
            "README.md",
        ]
        for filename in expected_files:
            self.assertTrue((EXTENSION_DIR / filename).exists(), filename)

        manifest = json.loads((EXTENSION_DIR / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["manifest_version"], 3)
        self.assertIn("bookmarks", manifest["permissions"])
        self.assertIn("storage", manifest["permissions"])
        self.assertIn("http://*/*", manifest["host_permissions"])
        self.assertIn("http://*/*", manifest["optional_host_permissions"])
        extension_csp = manifest["content_security_policy"]["extension_pages"]
        self.assertIn("connect-src http: https:", extension_csp)
        self.assertEqual(manifest["action"]["default_popup"], "popup.html")

    def test_extension_uses_linkvault_api_and_bookmarks_api(self):
        shared = (EXTENSION_DIR / "shared.js").read_text(encoding="utf-8")
        popup = (EXTENSION_DIR / "popup.js").read_text(encoding="utf-8")
        options = (EXTENSION_DIR / "options.js").read_text(encoding="utf-8")

        self.assertIn("/api/import/browser-html/preview", shared)
        self.assertIn("/api/import/browser-html", shared)
        self.assertIn("/api/bookmarks", shared)
        self.assertIn("bookmarks.getTree", shared)
        self.assertIn("bookmarks.getSubTree", shared)
        self.assertIn("browserBookmarkFolders", shared)
        self.assertIn("requestLinkVaultHostPermission", shared)
        self.assertIn("hostPermissionPattern", shared)
        self.assertIn("isRegularWebUrl", shared)
        self.assertIn("saveCurrentTab", popup)
        self.assertIn("selectedBookmarkSource", popup)
        self.assertIn("renderPreviewDetails", popup)
        self.assertIn("PREVIEW_DETAIL_LIMIT", popup)
        self.assertIn("testLinkVaultConnection", options)


if __name__ == "__main__":
    unittest.main()
