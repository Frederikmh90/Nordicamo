import unittest

from fastapi.testclient import TestClient


class DummyStatsService:
    def __init__(self, db):
        self.db = db

    def get_top_outlets(self, country=None, partisan=None, date_from=None, date_to=None, limit=10):
        self.last_args = (country, partisan, date_from, date_to, limit)
        return [
            {
                "domain": "example.com",
                "outlet_name": "Example Outlet",
                "country": country,
                "partisan": partisan,
                "count": 42,
            }
        ]


class TestTopOutletsFilters(unittest.TestCase):
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

    def test_top_outlets_date_filters(self):
        response = self.client.get(
            "/api/stats/top-outlets",
            params={
                "country": "denmark",
                "partisan": "Right",
                "date_from": "2025-01-01",
                "date_to": "2026-12-31",
                "limit": 1000,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filters"]["date_from"], "2025-01-01")
        self.assertEqual(payload["filters"]["date_to"], "2026-12-31")


if __name__ == "__main__":
    unittest.main()
