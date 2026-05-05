import unittest

from app.services.stats_service import StatsService


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.last_query = None
        self.last_params = None

    def execute(self, query, params):
        self.last_query = str(query)
        self.last_params = params
        return DummyResult(self.rows)


class TestStatsCaseInsensitive(unittest.TestCase):
    def test_articles_over_time_filters_are_case_insensitive(self):
        db = DummyDB(rows=[("2026", 2)])
        service = StatsService(db)

        service.get_articles_over_time(
            country="denmark",
            partisan="Right",
            granularity="year",
            date_from="2026-01-01",
            date_to="2026-12-31",
        )

        self.assertIn("LOWER(country) = LOWER(:country)", db.last_query)
        self.assertIn("LOWER(partisan) = LOWER(:partisan)", db.last_query)
        self.assertEqual(db.last_params["country"], "denmark")
        self.assertEqual(db.last_params["partisan"], "Right")

    def test_top_outlets_filters_are_case_insensitive(self):
        db = DummyDB(rows=[("example.com", "Example", "Denmark", "Right", 10)])
        service = StatsService(db)

        service.get_top_outlets(country="denmark", partisan="Right", limit=5)

        self.assertIn("LOWER(country) = LOWER(:country)", db.last_query)
        self.assertIn("LOWER(partisan) = LOWER(:partisan)", db.last_query)
        self.assertEqual(db.last_params["country"], "denmark")
        self.assertEqual(db.last_params["partisan"], "Right")


if __name__ == "__main__":
    unittest.main()
