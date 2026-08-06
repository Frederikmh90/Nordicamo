import os
import sys
import unittest

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestOverviewPageHelpers(unittest.TestCase):
    def test_landing_page_has_three_research_actions(self):
        from pages.overview import _research_action_items

        html = _research_action_items()

        self.assertIn("Compare", html)
        self.assertIn("Investigate", html)
        self.assertIn("Build a research case", html)
        self.assertIn("Start with a question", html)
        self.assertIn("?page=Workshop", html)
        self.assertNotIn("research-action-number", html)

    def test_landing_page_places_kpis_before_research_actions(self):
        from pathlib import Path

        overview_source = Path(__file__).resolve().parents[1] / "pages" / "overview.py"
        text = overview_source.read_text(encoding="utf-8")

        self.assertIn("def render_kpis()", text)
        self.assertLess(text.index("render_kpis()"), text.index("research-actions"))
        self.assertNotIn("Observatory scope", text)

    def test_landing_page_uses_a_dedicated_about_label(self):
        from pathlib import Path

        overview_source = Path(__file__).resolve().parents[1] / "pages" / "overview.py"
        text = overview_source.read_text(encoding="utf-8")

        self.assertIn("section-title landing-about-title", text)

    def test_research_actions_use_the_expected_destinations(self):
        from pages.overview import _research_action_items

        html = _research_action_items()

        self.assertIn("?page=Explorer", html)
        self.assertIn("?page=Media", html)
        self.assertIn("?page=Workshop", html)

    def test_monthly_chart_hides_only_current_calendar_month(self):
        from pages.overview import _exclude_incomplete_current_month

        frame = pd.DataFrame(
            {
                "date": ["2026-07-01", "2026-08-01", "2026-09-01"],
                "count": [10, 2, 12],
            }
        )
        filtered, hidden = _exclude_incomplete_current_month(
            frame,
            "Month",
            today=pd.Timestamp("2026-08-06"),
        )

        self.assertTrue(hidden)
        self.assertEqual(filtered["date"].dt.month.tolist(), [7, 9])

    def test_non_monthly_chart_keeps_current_period(self):
        from pages.overview import _exclude_incomplete_current_month

        frame = pd.DataFrame({"date": ["2026-08-01"], "count": [2]})
        filtered, hidden = _exclude_incomplete_current_month(
            frame,
            "Year",
            today=pd.Timestamp("2026-08-06"),
        )

        self.assertFalse(hidden)
        self.assertEqual(len(filtered), 1)

    def test_landing_page_does_not_render_data_trust_panel(self):
        from pathlib import Path

        overview_source = Path(__file__).resolve().parents[1] / "pages" / "overview.py"
        text = overview_source.read_text(encoding="utf-8")

        self.assertNotIn("<div class='signal-panel-title'>Data trust</div>", text)
        self.assertNotIn("build_data_trust_items", text)

    def test_ticker_sample_interleaves_outlets(self):
        from pages.overview import _build_ticker_sample

        articles = [
            {"domain": "a.example", "title": "A1"},
            {"domain": "a.example", "title": "A2"},
            {"domain": "b.example", "title": "B1"},
            {"domain": "b.example", "title": "B2"},
            {"domain": "c.example", "title": "C1"},
            {"domain": "c.example", "title": "C2"},
        ]

        sample = _build_ticker_sample(articles)
        domains = [row["domain"] for row in sample]

        self.assertEqual(len(sample), 6)
        self.assertTrue(all(a != b for a, b in zip(domains, domains[1:])))


if __name__ == "__main__":
    unittest.main()
