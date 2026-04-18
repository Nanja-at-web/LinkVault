import unittest

from linkvault.url_tools import normalize_url


class UrlToolsTest(unittest.TestCase):
    def test_normalize_adds_scheme_and_removes_tracking_params(self):
        self.assertEqual(normalize_url("Example.com/a/?utm_source=x&b=2"), "https://example.com/a?b=2")

    def test_normalize_removes_default_port_and_fragment(self):
        self.assertEqual(normalize_url("HTTPS://Example.com:443/docs/#section"), "https://example.com/docs")


if __name__ == "__main__":
    unittest.main()
