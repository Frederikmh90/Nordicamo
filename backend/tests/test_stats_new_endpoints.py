import unittest

from fastapi.testclient import TestClient


class DummyStatsService:
    def __init__(self, db):
        self.db = db

    def get_concentration_metrics(self, country=None, partisan=None, date_from=None, date_to=None, top_n=5):
        return {
            "top_n": top_n,
            "top_n_share": 0.4,
            "hhi": 0.11,
            "enp": 9.09,
            "n_outlets": 12,
            "coverage_share": 0.95,
        }

    def get_partisan_mix(self, country=None, date_from=None, date_to=None):
        return {
            "total_count": 100,
            "unknown_or_missing_count": 5,
            "data": [
                {"partisan": "Right", "count": 50, "share": 0.5},
                {"partisan": "Left", "count": 30, "share": 0.3},
                {"partisan": "Other", "count": 15, "share": 0.15},
                {"partisan": "Unclassified", "count": 5, "share": 0.05},
            ],
        }

    def get_topic_similarity(
        self,
        level="country",
        country=None,
        partisan=None,
        outlets=None,
        date_from=None,
        date_to=None,
        limit_topics=12,
    ):
        return {
            "topics": ["Politics", "Economy"],
            "entities": ["denmark", "sweden"],
            "cosine": [{"entity_a": "denmark", "entity_b": "sweden", "value": 0.72}],
            "jsd": [{"entity_a": "denmark", "entity_b": "sweden", "value": 0.18}],
        }

    def get_landing_bundle(self):
        return {
            "overview": {
                "total_articles": 100,
                "total_outlets": 10,
                "date_range": {"earliest": "2021-01-01", "latest": "2026-03-25"},
                "by_country": {"denmark": 40, "sweden": 60},
                "by_partisan": {"Right": 70, "Left": 30},
                "avg_articles_per_outlet": 10.0,
                "growth_rate_per_year": 3.5,
                "coverage_years": "2021-2026",
            },
            "freshness": {
                "last_article_date": "2026-03-25",
                "last_updated": "2026-03-25 12:00:00",
                "hours_ago": 3,
            },
            "latest_articles": [
                {
                    "id": 1,
                    "title": "Latest article",
                    "url": "https://example.com/a",
                    "date": "2026-03-25",
                    "domain": "example.com",
                }
            ],
            "articles_over_time": {
                "granularity": "month",
                "filters": {
                    "country": None,
                    "partisan": None,
                    "date_from": "2021-01-01",
                    "date_to": "2026-12-31",
                },
                "data": [{"country": "denmark", "date": "2026-03", "count": 10}],
            },
        }

    def get_analysis_bundle(self):
        return {
            "overview": self.get_landing_bundle()["overview"],
            "filters": {
                "date_from": "2016-01-01",
                "date_to": "2026-12-31",
                "year_from": 2016,
                "year_to": 2026,
                "granularity": "month",
                "partisan": None,
                "recent_years": [2023, 2024, 2025, 2026],
            },
            "articles_over_time": {
                "granularity": "month",
                "filters": {
                    "country": None,
                    "partisan": None,
                    "date_from": "2016-01-01",
                    "date_to": "2026-12-31",
                },
                "data": [{"country": "denmark", "date": "2026-03", "count": 10}],
            },
            "partisan_mix": [
                {"country": "denmark", "year": 2026, "partisan": "Right", "count": 10, "share": 1.0}
            ],
            "concentration": [
                {"country": "denmark", "year": 2026, "enp": 2.0, "hhi": 0.5, "n_outlets": 2}
            ],
            "categories_over_time": {"filters": {}, "data": []},
            "topic_similarity": {
                "filters": {},
                "topics": [],
                "entities": [],
                "cosine": [],
                "jsd": [],
            },
        }


class TestStatsNewEndpoints(unittest.TestCase):
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

    def test_concentration_endpoint(self):
        response = self.client.get("/api/stats/concentration", params={"country": "denmark", "top_n": 5})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["top_n"], 5)
        self.assertIn("hhi", payload)
        self.assertIn("enp", payload)

    def test_partisan_mix_endpoint(self):
        response = self.client.get("/api/stats/partisan-mix", params={"country": "sweden"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["unknown_or_missing_count"], 5)
        self.assertEqual(len(payload["data"]), 4)
        self.assertEqual(payload["data"][3]["partisan"], "Unclassified")

    def test_topic_similarity_endpoint(self):
        response = self.client.get("/api/stats/topic-similarity", params={"level": "country"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("cosine", payload)
        self.assertIn("jsd", payload)
        self.assertEqual(payload["topics"], ["Politics", "Economy"])

    def test_topic_similarity_endpoint_accepts_country_partisan_level(self):
        response = self.client.get("/api/stats/topic-similarity", params={"level": "country_partisan"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filters"]["level"], "country_partisan")

    def test_landing_endpoint_returns_compact_bundle(self):
        response = self.client.get("/api/stats/landing")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("overview", payload)
        self.assertIn("freshness", payload)
        self.assertIn("latest_articles", payload)
        self.assertIn("articles_over_time", payload)
        self.assertEqual(payload["latest_articles"][0]["title"], "Latest article")

    def test_analysis_endpoint_returns_default_bundle(self):
        response = self.client.get("/api/stats/analysis")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("overview", payload)
        self.assertIn("articles_over_time", payload)
        self.assertIn("partisan_mix", payload)
        self.assertIn("concentration", payload)
        self.assertEqual(payload["filters"]["granularity"], "month")


if __name__ == "__main__":
    unittest.main()
