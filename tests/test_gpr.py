import datetime as dt
import unittest

import pandas as pd

import db
import gpr


def sample():
    return pd.DataFrame({"date": pd.to_datetime(["2026-10-04", "2026-10-05"]),
                         "GPRD": [145.6, 141.5], "GPRD_ACT": [163.3, None], "GPRD_THREAT": [151.3, 166.1],
                         "GPRD_MA7": [186.8, 177.5], "event": ["", ""]})


class TestGpr(unittest.TestCase):
    def test_three_series_in_long_form(self):
        rows = gpr.parse(sample())
        self.assertEqual(sorted(rows.indicator.unique()), ["GPR", "GPR_ACTS", "GPR_THREATS"])
        gpr_rows = rows[rows.indicator == "GPR"]
        self.assertEqual(list(gpr_rows.obs_date), [dt.date(2026, 10, 4), dt.date(2026, 10, 5)])
        self.assertAlmostEqual(gpr_rows.value.iloc[-1], 141.5, places=3)

    def test_missing_values_are_dropped_and_extras_ignored(self):
        rows = gpr.parse(sample())
        self.assertEqual(len(rows[rows.indicator == "GPR_ACTS"]), 1)     # one blank day
        self.assertEqual(len(rows), 5)                                    # moving averages and notes not stored

    def test_store_is_repeatable(self):
        con = db.connect(":memory:")
        gpr.store(con, gpr.parse(sample()))
        gpr.store(con, gpr.parse(sample()))
        self.assertEqual(con.execute("SELECT count(*) FROM daily_indicator").fetchone()[0], 5)

    def test_publishing_terms(self):
        self.assertTrue(gpr.PUBLISHABLE)
        self.assertIn("Creative Commons BY", gpr.OWNER)


if __name__ == "__main__":
    unittest.main()
