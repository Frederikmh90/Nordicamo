import unittest
from fastapi.testclient import TestClient


class DummyArticlesService:
    def __init__(self, db):
        self.db = db

    def search_articles(self, **kwargs):
        return {
            "total": 2,
            "articles": [
                {
                    "id": 1,
                    "title": "Example A",
                    "url": "https://example.com/a",
                    "date": "2024-01-01",
                    "domain": "example.com",
                    "country": "denmark",
                    "partisan": "Right",
                    "sentiment": "neutral",
                    "sentiment_score": 0.1,
                    "description": "Desc A",
                    "content": "Content A",
                    "categories": ["Politics"],
                    "entities": {"persons": ["Alice"]},
                },
                {
                    "id": 2,
                    "title": "Example B",
                    "url": "https://example.com/b",
                    "date": "2024-01-02",
                    "domain": "example.com",
                    "country": "sweden",
                    "partisan": "Left",
                    "sentiment": "positive",
                    "sentiment_score": 0.9,
                    "description": "Desc B",
                    "content": "Content B",
                    "categories": ["Economy"],
                    "entities": {"organizations": ["Org"]},
                },
            ],
        }


class TestArticlesSearchEndpoint(unittest.TestCase):
    def setUp(self):
        from app.main import app
        from app.api import articles as articles_module
        from app.database import get_db

        self.app = app
        self.articles_module = articles_module
        self.original_service = articles_module.ArticlesService
        articles_module.ArticlesService = DummyArticlesService
        self.app.dependency_overrides[get_db] = lambda: None
        self.client = TestClient(self.app)

    def tearDown(self):
        self.articles_module.ArticlesService = self.original_service
        self.app.dependency_overrides = {}

    def test_articles_search(self):
        response = self.client.get("/api/articles/search", params={"limit": 2, "offset": 0})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual(len(payload["articles"]), 2)
        self.assertEqual(payload["articles"][0]["title"], "Example A")


if __name__ == "__main__":
    unittest.main()
