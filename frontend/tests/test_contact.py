import unittest
from urllib.parse import urlparse, parse_qs


class TestContactMailto(unittest.TestCase):
    def test_build_access_mailto_includes_fields(self):
        from contact import build_access_mailto

        mailto = build_access_mailto(
            name="Ada Lovelace",
            email="ada@example.org",
            request="Denmark + Sweden, 2020-2024.",
        )
        parsed = urlparse(mailto)
        self.assertEqual(parsed.scheme, "mailto")
        self.assertEqual(parsed.path, "frmohe@ruc.dk")

        query = parse_qs(parsed.query)
        self.assertIn("subject", query)
        self.assertIn("body", query)
        self.assertIn("Ada Lovelace", query["body"][0])
        self.assertIn("ada@example.org", query["body"][0])
        self.assertIn("Denmark + Sweden, 2020-2024.", query["body"][0])


if __name__ == "__main__":
    unittest.main()
