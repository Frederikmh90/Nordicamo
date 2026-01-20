import unittest

from fastapi.testclient import TestClient


class DummyStatsService:
    def __init__(self, db):
        self.db = db

    def get_categories_over_time(
        self,
        country=None,
        partisan=None,
        date_from=None,
        date_to=None,
        granularity="month",
        limit=6,
    ):
        self.last_args = (country, partisan, date_from, date_to, granularity, limit)
        return [
            {"date": "2020", "category": "Politics", "count": 10},
        ]


class TestCategoriesOverTime(unittest.TestCase):
    def setUp(self):
        from app.main import app
        from app.api import stats as stats_module
        from app.database import get_db

        self.app = app
        self.stats_module = stats_module
        self.original_stats_service = stats_module.StatsService
        stats_module.StatsService = DummyStatsService
        self.app.dependency_overrides[get_db] = lambda: None
        self.client = TestClient(self.app)

    def tearDown(self):
        self.stats_module.StatsService = self.original_stats_service
        self.app.dependency_overrides = {}

    def test_categories_over_time_filters(self):
        response = self.client.get(
            "/api/stats/categories/over-time",
            params={
                "country": "denmark",
                "partisan": "Right",
                "granularity": "year",
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
                "limit": 5,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filters"]["country"], "denmark")
        self.assertEqual(payload["filters"]["partisan"], "Right")
        self.assertEqual(payload["filters"]["granularity"], "year")
        self.assertEqual(payload["filters"]["date_from"], "2020-01-01")
        self.assertEqual(payload["filters"]["date_to"], "2020-12-31")
        self.assertEqual(payload["filters"]["limit"], 5)


if __name__ == "__main__":
    unittest.main()
