import unittest

from linkvault.metadata import MetadataParser


class MetadataParserTest(unittest.TestCase):
    def test_extracts_open_graph_metadata_and_favicon(self):
        parser = MetadataParser("https://github.com/Nanja-at-web/LinkVault")
        parser.feed(
            """
            <html>
              <head>
                <title>Fallback Title</title>
                <meta property="og:title" content="Nanja-at-web/LinkVault">
                <meta name="description" content="A selfhosted bookmark app">
                <link rel="icon" href="/favicon.svg">
              </head>
            </html>
            """
        )

        metadata = parser.metadata()

        self.assertEqual(metadata.title, "Nanja-at-web/LinkVault")
        self.assertEqual(metadata.description, "A selfhosted bookmark app")
        self.assertEqual(metadata.favicon_url, "https://github.com/favicon.svg")


if __name__ == "__main__":
    unittest.main()
