import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


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

    def test_consolidate_outlets_by_domain(self):
        from media_helpers import consolidate_outlets

        outlets = [
            {"domain": "newsvoice.se", "outlet_name": "NewsVoice", "partisan": None, "count": 10},
            {"domain": "newsvoice.se", "outlet_name": None, "partisan": "Right", "count": 5},
            {"domain": "example.com", "outlet_name": "Example", "partisan": "Left", "count": 3},
            {"domain": "document.no", "outlet_name": "Document", "partisan": "Right", "count": 2},
            {"domain": "www.document.no", "outlet_name": None, "partisan": None, "count": 4},
        ]
        consolidated = consolidate_outlets(outlets)
        by_domain = {o["domain"]: o for o in consolidated}
        self.assertEqual(by_domain["newsvoice.se"]["count"], 15)
        self.assertEqual(by_domain["newsvoice.se"]["outlet_name"], "NewsVoice")
        self.assertEqual(by_domain["newsvoice.se"]["partisan"], "Right")
        self.assertEqual(by_domain["www.document.no"]["count"], 6)

    def test_select_latest_articles(self):
        from media_helpers import select_latest_articles

        response = {
            "total": 3,
            "articles": [
                {"title": "A"},
                {"title": "B"},
                {"title": "C"},
            ],
        }
        latest = select_latest_articles(response, limit=2)
        self.assertEqual([item["title"] for item in latest], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
