import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestNavigation(unittest.TestCase):
    def test_topbar_navigation_is_intentionally_compact(self):
        from navigation import TOPBAR_NAV_ITEMS

        self.assertEqual(
            TOPBAR_NAV_ITEMS,
            [
                ("Platform", "Nordicamo"),
                ("Countries", "Explorer"),
                ("Request Access", "GetAccess"),
            ],
        )

    def test_legacy_page_aliases_include_old_access_label(self):
        from navigation import LEGACY_PAGE_ALIASES

        self.assertEqual(LEGACY_PAGE_ALIASES["Full Data Access"], "GetAccess")
        self.assertEqual(LEGACY_PAGE_ALIASES["Countries"], "Explorer")

    def test_platform_and_countries_share_dark_blue_nav_color(self):
        from pathlib import Path

        app_source = Path(__file__).resolve().parents[1] / "app.py"
        text = app_source.read_text(encoding="utf-8")

        self.assertIn(".nav-link {", text)
        self.assertIn("color: #0f3855;", text)
        self.assertNotIn("color: #1b3a53;", text)


if __name__ == "__main__":
    unittest.main()
