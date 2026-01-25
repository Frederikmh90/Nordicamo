import unittest


class TestStatsDomainVariants(unittest.TestCase):
    def test_domain_variants(self):
        from app.services.stats_service import domain_variants

        self.assertEqual(set(domain_variants("document.no")), {"document.no", "www.document.no"})
        self.assertEqual(
            set(domain_variants("www.nyadagbladet.se")),
            {"nyadagbladet.se", "www.nyadagbladet.se"},
        )


if __name__ == "__main__":
    unittest.main()
