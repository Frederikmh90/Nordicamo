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

    def test_compute_country_shares(self):
        from overview_helpers import compute_country_shares

        series = {
            "denmark": [
                {"date": "2020-01-01", "count": 10},
                {"date": "2020-02-01", "count": 30},
            ],
            "sweden": [
                {"date": "2020-01-01", "count": 10},
            ],
        }
        shares = compute_country_shares(series)

        denmark = {row["date"]: row for row in shares["denmark"]}
        sweden = {row["date"]: row for row in shares["sweden"]}

        self.assertAlmostEqual(denmark["2020-01-01"]["share"], 0.5)
        self.assertAlmostEqual(sweden["2020-01-01"]["share"], 0.5)
        self.assertAlmostEqual(denmark["2020-02-01"]["share"], 1.0)
        self.assertAlmostEqual(sweden["2020-02-01"]["share"], 0.0)
        self.assertEqual(denmark["2020-01-01"]["total"], 20)

    def test_compute_top_n_share(self):
        from overview_helpers import compute_top_n_share

        rows = [
            {"count": 10},
            {"count": 5},
            {"count": 1},
            {"count": 1},
        ]
        share = compute_top_n_share(rows, n=2)
        self.assertAlmostEqual(share, 0.75)

    def test_compute_partisan_shares(self):
        from overview_helpers import compute_partisan_shares

        rows = [
            {"partisan": "Right", "count": 5},
            {"partisan": "Left", "count": 3},
            {"partisan": None, "count": 2},
        ]
        shares = compute_partisan_shares(rows)
        self.assertAlmostEqual(shares["Right"], 0.5)
        self.assertAlmostEqual(shares["Left"], 0.3)
        self.assertAlmostEqual(shares["Other"], 0.2)

    def test_compute_lorenz_curve_uniform(self):
        from overview_helpers import compute_lorenz_curve

        x, y, gini = compute_lorenz_curve([10, 10, 10, 10])
        self.assertEqual(x[0], 0.0)
        self.assertEqual(y[0], 0.0)
        self.assertEqual(x[-1], 1.0)
        self.assertEqual(y[-1], 1.0)
        self.assertAlmostEqual(gini, 0.0, places=3)

    def test_compute_lorenz_curve_uneven(self):
        from overview_helpers import compute_lorenz_curve

        _, _, gini = compute_lorenz_curve([100, 0, 0, 0])
        self.assertGreater(gini, 0.7)


if __name__ == "__main__":
    unittest.main()
