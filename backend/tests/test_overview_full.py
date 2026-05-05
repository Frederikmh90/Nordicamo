import unittest

from fastapi.testclient import TestClient


class DummyStatsService:
    def __init__(self, db):
        self.db = db

    def get_enhanced_overview_full(self):
        return {
            "total_articles": 123,
            "total_outlets": 5,
            "date_range": {"earliest": "2008-01-01", "latest": "2026-01-21"},
            "avg_articles_per_outlet": 24.6,
            "growth_rate_per_year": 100.0,
            "coverage_years": "2008-2026",
            "by_country": {},
            "by_partisan": {},
        }


class TestOverviewFull(unittest.TestCase):
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

    def test_full_overview_endpoint(self):
        response = self.client.get("/api/stats/overview/full")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_articles"], 123)
        self.assertEqual(payload["total_outlets"], 5)
        self.assertEqual(payload["coverage_years"], "2008-2026")


if __name__ == "__main__":
    unittest.main()
