import unittest


class TestStatsSimilarityMath(unittest.TestCase):
    def test_cosine_similarity_identity_and_orthogonal(self):
        from app.services.stats_service import _cosine_similarity

        self.assertAlmostEqual(_cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0, places=6)
        self.assertAlmostEqual(_cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0, places=6)

    def test_jsd_identity_zero(self):
        from app.services.stats_service import _jensen_shannon_divergence

        self.assertAlmostEqual(
            _jensen_shannon_divergence([0.5, 0.5], [0.5, 0.5]),
            0.0,
            places=6,
        )

    def test_safe_share_handles_zero_total(self):
        from app.services.stats_service import _safe_share

        self.assertEqual(_safe_share(10, 0), 0.0)
        self.assertEqual(_safe_share(10, 20), 0.5)


if __name__ == "__main__":
    unittest.main()

