import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestOverviewPageHelpers(unittest.TestCase):
    def test_observatory_scope_items_render_expected_sections(self):
        from pages.overview import _observatory_scope_items

        html = _observatory_scope_items()

        self.assertIn("Active observation", html)
        self.assertNotIn("Active monitoring", html)
        self.assertIn("Comparative analysis", html)
        self.assertIn("Research archive", html)

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
