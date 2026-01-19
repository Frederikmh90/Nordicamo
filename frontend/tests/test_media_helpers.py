import unittest


class TestMediaHelpers(unittest.TestCase):
    def test_filter_outlets_by_name(self):
        from media_helpers import filter_outlets

        outlets = [
            {"outlet_name": "Nordic Watch", "domain": "nordicwatch.example"},
            {"outlet_name": "Alt News", "domain": "altnews.example"},
            {"domain": "unknown.example"},
        ]

        filtered = filter_outlets(outlets, "nordic")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["outlet_name"], "Nordic Watch")

    def test_filter_outlets_empty_query(self):
        from media_helpers import filter_outlets

        outlets = [{"outlet_name": "Alpha"}, {"outlet_name": "Beta"}]
        filtered = filter_outlets(outlets, "")
        self.assertEqual(filtered, outlets)


if __name__ == "__main__":
    unittest.main()
