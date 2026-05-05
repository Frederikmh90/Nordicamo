import unittest

from fastapi.testclient import TestClient


class DummyStatsService:
    def __init__(self, db):
        self.db = db

    def get_articles_over_time_by_outlet(
        self,
        outlets,
        country=None,
        granularity="month",
        date_from=None,
        date_to=None,
    ):
        self.last_args = (outlets, country, granularity, date_from, date_to)
        return [
            {"date": "2020", "outlet": "example.com", "count": 12},
        ]


class TestArticlesOverTimeByOutlet(unittest.TestCase):
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

    def test_articles_over_time_by_outlet_filters(self):
        response = self.client.get(
            "/api/stats/articles-over-time-by-outlet",
            params={
                "outlets": "example.com,example2.com",
                "country": "sweden",
                "granularity": "year",
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filters"]["country"], "sweden")
        self.assertEqual(payload["filters"]["granularity"], "year")
        self.assertEqual(payload["filters"]["date_from"], "2020-01-01")
        self.assertEqual(payload["filters"]["date_to"], "2020-12-31")
        self.assertEqual(payload["filters"]["outlets"], "example.com,example2.com")


if __name__ == "__main__":
    unittest.main()
