import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestWorkshopHelpers(unittest.TestCase):
    def test_preview_records_exposes_metadata_not_article_content(self):
        from workshop_helpers import preview_records

        rows = preview_records(
            [
                {
                    "date": "2026-05-01",
                    "country": "denmark",
                    "domain": "example.dk",
                    "partisan": "Right",
                    "categories": ["Politics", "Media"],
                    "title": "Example title",
                    "url": "https://example.dk/article",
                    "content": "This must not appear in the public preview.",
                }
            ]
        )

        self.assertEqual(rows[0]["Country"], "Denmark")
        self.assertEqual(rows[0]["Categories"], "Politics, Media")
        self.assertNotIn("content", rows[0])
        self.assertNotIn("This must not appear", str(rows[0]))

    def test_preview_records_is_bounded(self):
        from workshop_helpers import preview_records

        articles = [{"title": str(index)} for index in range(120)]
        self.assertEqual(len(preview_records(articles)), 100)

    def test_preview_records_formats_missing_and_legacy_category_values(self):
        from workshop_helpers import preview_records

        rows = preview_records(
            [
                {"categories": None},
                {"categories": '["[Crime & justice]"]'},
            ]
        )

        self.assertEqual(rows[0]["Categories"], "Not yet categorized")
        self.assertEqual(rows[1]["Categories"], "Crime & Justice")

    def test_access_context_captures_selection_and_requested_rows(self):
        from workshop_helpers import build_access_request_context, project_by_key

        context = build_access_request_context(
            project_by_key("reporting_case"),
            countries=["denmark"],
            date_from="2024-01-01",
            date_to="2025-12-31",
            outlets=["example.dk"],
            categories=["Politics"],
            keyword="migration",
            requested_rows=500,
        )

        self.assertIn("Build a reporting case", context)
        self.assertIn("Denmark", context)
        self.assertIn("example.dk", context)
        self.assertIn("migration", context)
        self.assertIn("500 rows", context)
        self.assertIn("Purpose and affiliation", context)

    def test_safe_article_url_allows_only_http_urls(self):
        from workshop_helpers import safe_article_url

        self.assertEqual(safe_article_url("https://example.dk/article"), "https://example.dk/article")
        self.assertEqual(safe_article_url("javascript:alert(1)"), "")
        self.assertEqual(safe_article_url("/relative-article"), "")

    def test_unknown_project_uses_compare_project(self):
        from workshop_helpers import project_by_key

        self.assertEqual(project_by_key("not-a-project").key, "compare_agendas")


if __name__ == "__main__":
    unittest.main()
