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


if __name__ == "__main__":
    unittest.main()
