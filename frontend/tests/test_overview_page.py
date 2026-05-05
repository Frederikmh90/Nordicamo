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

    def test_data_trust_items_render_canonical_domain_note(self):
        from pages.overview import _data_trust_items

        html = _data_trust_items(
            {"date_range": {"latest": "2026-05-05"}},
            {"hours_ago": 3, "last_article_date": "2026-05-05"},
        )

        self.assertIn("Latest indexed article", html)
        self.assertIn("Canonical outlet identity", html)
        self.assertIn("www/non-www", html)


if __name__ == "__main__":
    unittest.main()
