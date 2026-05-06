import unittest

from app.services.stats_service import StatsService, _DOMAIN_PARTISAN_CACHE


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeSession:
    def __init__(self):
        self.calls = 0

    def execute(self, query, params=None):
        self.calls += 1
        sql = str(query)
        if "FROM clean_articles" in sql:
            return FakeResult([("", "steigan.no", 10)])
        if "FROM actors" in sql:
            return FakeResult([("steigan.no", "Left")])
        return FakeResult([])


class TestStatsServicePartisanMix(unittest.TestCase):
    def setUp(self):
        _DOMAIN_PARTISAN_CACHE.clear()

    def tearDown(self):
        _DOMAIN_PARTISAN_CACHE.clear()

    def test_missing_article_partisan_uses_startlist_actor_orientation(self):
        service = StatsService(FakeSession())

        result = service.get_partisan_mix(country="norway", date_from="2026-01-01", date_to="2026-12-31")

        by_label = {row["partisan"]: row for row in result["data"]}
        self.assertEqual(by_label["Left"]["count"], 10)
        self.assertEqual(by_label["Unclassified"]["count"], 0)
        self.assertEqual(result["unknown_or_missing_count"], 0)


if __name__ == "__main__":
    unittest.main()
