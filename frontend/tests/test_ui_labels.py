import unittest


class TestUiLabels(unittest.TestCase):
    def test_avg_articles_per_outlet_label(self):
        from ui_labels import AVG_ARTICLES_PER_OUTLET_LABEL

        self.assertEqual(AVG_ARTICLES_PER_OUTLET_LABEL, "Average articles per outlet")


if __name__ == "__main__":
    unittest.main()
