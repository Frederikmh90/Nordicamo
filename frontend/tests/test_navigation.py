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
                ("Overview", "Explorer"),
                ("Research Workshop", "Workshop"),
                ("Browse Media", "Media"),
                ("About", "About"),
                ("Request Access", "GetAccess"),
            ],
        )

    def test_legacy_page_aliases_include_old_access_label(self):
        from navigation import ALLOWED_PAGES, LEGACY_PAGE_ALIASES

        self.assertEqual(LEGACY_PAGE_ALIASES["Full Data Access"], "GetAccess")
        self.assertEqual(LEGACY_PAGE_ALIASES["Countries"], "Explorer")
        self.assertEqual(LEGACY_PAGE_ALIASES["Analysis"], "Explorer")
        self.assertEqual(LEGACY_PAGE_ALIASES["Overview"], "Explorer")
        self.assertIn("Workshop", ALLOWED_PAGES)

    def test_standard_navigation_uses_the_dark_blue_accent(self):
        from pathlib import Path

        app_source = Path(__file__).resolve().parents[1] / "app.py"
        text = app_source.read_text(encoding="utf-8")

        self.assertIn(".nav-link {", text)
        self.assertIn("color: #0f3855 !important;", text)


if __name__ == "__main__":
    unittest.main()
