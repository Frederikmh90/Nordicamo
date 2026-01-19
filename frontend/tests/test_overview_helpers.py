import unittest


class TestOverviewHelpers(unittest.TestCase):
    def test_format_freshness_hours(self):
        from overview_helpers import format_freshness

        freshness_text, last_article = format_freshness(
            {"hours_ago": 5, "last_article_date": "2025-01-10T12:34:56"}
        )
        self.assertEqual(freshness_text, "Last updated: 5 hours ago")
        self.assertEqual(last_article, "2025-01-10")

    def test_format_freshness_days(self):
        from overview_helpers import format_freshness

        freshness_text, last_article = format_freshness(
            {"hours_ago": 48, "last_article_date": "2024-12-31"}
        )
        self.assertEqual(freshness_text, "Last updated: 2 days ago")
        self.assertEqual(last_article, "2024-12-31")

    def test_format_freshness_missing(self):
        from overview_helpers import format_freshness

        freshness_text, last_article = format_freshness({})
        self.assertEqual(freshness_text, "Freshness data unavailable")
        self.assertEqual(last_article, "N/A")


if __name__ == "__main__":
    unittest.main()
