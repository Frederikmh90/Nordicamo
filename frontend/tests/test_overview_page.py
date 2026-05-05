import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestOverviewPageHelpers(unittest.TestCase):
    def test_observatory_scope_items_render_expected_sections(self):
        from pages.overview import _observatory_scope_items

        html = _observatory_scope_items()

        self.assertIn("Active monitoring", html)
        self.assertIn("Comparative analysis", html)
        self.assertIn("Research archive", html)


if __name__ == "__main__":
    unittest.main()
