import unittest
from fastapi.testclient import TestClient


class DummyStatsService:
    def __init__(self, db):
        self.db = db

    def get_outlet_profile(self, domain: str):
        if domain == "example.com":
            return {
                "domain": "example.com",
                "outlet_name": "Example Outlet",
                "country": "denmark",
                "total_articles": 123,
                "first_article_date": "2020-01-01",
                "last_article_date": "2024-12-31",
            }
        return None


class TestOutletProfileEndpoint(unittest.TestCase):
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

    def test_outlet_profile_found(self):
        response = self.client.get("/api/stats/outlet-profile", params={"domain": "example.com"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["domain"], "example.com")
        self.assertEqual(payload["total_articles"], 123)

    def test_outlet_profile_missing(self):
        response = self.client.get("/api/stats/outlet-profile", params={"domain": "missing.com"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
