import os
import sys
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestExplorerHelpers(unittest.TestCase):
    def test_normalize_explorer_mode_defaults_to_compare(self):
        from pages.explorer import MODE_COMPARE, normalize_explorer_mode

        self.assertEqual(normalize_explorer_mode(None), MODE_COMPARE)
        self.assertEqual(normalize_explorer_mode("unknown"), MODE_COMPARE)

    def test_normalize_explorer_mode_accepts_valid_values(self):
        from pages.explorer import MODE_COMPARE, MODE_DEEP_DIVE, normalize_explorer_mode

        self.assertEqual(normalize_explorer_mode(MODE_COMPARE), MODE_COMPARE)
        self.assertEqual(normalize_explorer_mode(MODE_DEEP_DIVE), MODE_DEEP_DIVE)

    def test_normalize_country_defaults_to_denmark(self):
        from pages.explorer import normalize_country

        self.assertEqual(normalize_country(None), "denmark")
        self.assertEqual(normalize_country("x"), "denmark")

    def test_normalize_country_accepts_supported_country(self):
        from pages.explorer import normalize_country

        self.assertEqual(normalize_country("sweden"), "sweden")

    def test_deep_dive_view_options_includes_topics(self):
        from pages.explorer import deep_dive_view_options

        options = deep_dive_view_options()
        self.assertIn("Topics Over Time", options)
        self.assertEqual(options[0], "Total Count")

    def test_default_year_range_prefers_2016_2026(self):
        from pages.explorer import _default_year_range

        self.assertEqual(_default_year_range(2008, 2028), (2016, 2026))
        self.assertEqual(_default_year_range(2020, 2024), (2020, 2024))

    def test_topics_metric_transform_share_mode(self):
        from pages.explorer import topics_metric_transform

        df = pd.DataFrame(
            [
                {"outlet": "a.dk", "category": "Politics", "count": 30},
                {"outlet": "a.dk", "category": "Health", "count": 70},
                {"outlet": "b.dk", "category": "Politics", "count": 20},
                {"outlet": "b.dk", "category": "Health", "count": 20},
            ]
        )
        transformed, label = topics_metric_transform(df, "Share of Outlet Topics (%)")
        self.assertEqual(label, "Share (%)")
        self.assertAlmostEqual(
            float(transformed[(transformed["outlet"] == "a.dk") & (transformed["category"] == "Politics")]["value"].iloc[0]),
            30.0,
        )
        self.assertAlmostEqual(
            float(transformed[(transformed["outlet"] == "b.dk") & (transformed["category"] == "Politics")]["value"].iloc[0]),
            50.0,
        )

    def test_matrix_records_to_df_builds_symmetric_matrix(self):
        from pages.explorer import _matrix_records_to_df

        entities = ["denmark", "sweden", "norway"]
        records = [
            {"entity_a": "denmark", "entity_b": "sweden", "value": 0.8},
            {"entity_a": "denmark", "entity_b": "norway", "value": 0.6},
        ]
        matrix = _matrix_records_to_df(records, entities)
        self.assertEqual(matrix.loc["denmark", "denmark"], 1.0)
        self.assertEqual(matrix.loc["sweden", "denmark"], 0.8)
        self.assertEqual(matrix.loc["norway", "denmark"], 0.6)

    def test_wrap_two_line_label(self):
        from pages.explorer import _wrap_two_line_label

        self.assertEqual(_wrap_two_line_label("Short"), "Short")
        self.assertEqual(
            _wrap_two_line_label("Politics & Governance"),
            "Politics &<br>Governance",
        )

if __name__ == "__main__":
    unittest.main()
