import unittest

from linkvault.server import index_html, linkvault_identity


class ServerHtmlTest(unittest.TestCase):
    def test_linkvault_identity_supports_extension_discovery(self):
        identity = linkvault_identity()

        self.assertEqual(identity["app"], "LinkVault")
        self.assertEqual(identity["health"], "/healthz")
        self.assertIn("version", identity)

    def test_index_html_documents_keyboard_shortcuts(self):
        html = index_html()

        self.assertIn("Ctrl/Cmd+K Suche", html)
        self.assertIn("document.addEventListener('keydown'", html)
        self.assertIn("isTypingTarget", html)
        self.assertIn("setActiveTab('bookmarks')", html)


if __name__ == "__main__":
    unittest.main()
