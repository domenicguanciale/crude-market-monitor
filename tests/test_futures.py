import datetime as dt
import unittest

import pandas as pd

import futures

D = dt.date


def prices(rows):
    return pd.DataFrame(rows, columns=["benchmark", "price_date", "price"])


class TestCurveState(unittest.TestCase):
    def test_states(self):
        self.assertEqual(futures.curve_state(0.05), "backwardation")
        self.assertEqual(futures.curve_state(-0.05), "contango")
        self.assertEqual(futures.curve_state(0.005), "flat")
        self.assertEqual(futures.curve_state(0.01), "flat")      # exactly on the band edge
        self.assertEqual(futures.curve_state(0.005, band=0), "backwardation")
        self.assertIsNone(futures.curve_state(float("nan")))


class TestWeeklyCurve(unittest.TestCase):
    def test_weekly_average_gap(self):
        p = prices([
            ("WTI future 1", D(2022, 3, 7), 110.0), ("WTI future 4", D(2022, 3, 7), 100.0),   # +10%
            ("WTI future 1", D(2022, 3, 8), 104.0), ("WTI future 4", D(2022, 3, 8), 100.0),   # +4%
            ("WTI future 1", D(2022, 3, 9), 999.0),                                           # no far price
            ("WTI", D(2022, 3, 7), 123.7),                                                    # other series ignored
        ])
        w = futures.weekly_curve(p).iloc[0]
        self.assertEqual(w.week_ending, D(2022, 3, 11))
        self.assertAlmostEqual(w.futures_gap, 7.0)
        self.assertAlmostEqual(w.futures_gap_pct, 0.07)
        self.assertEqual(w.curve_state, "backwardation")

    def test_contango(self):
        p = prices([("WTI future 1", D(2020, 4, 1), 20.0), ("WTI future 4", D(2020, 4, 1), 27.0)])
        self.assertEqual(futures.weekly_curve(p).iloc[0].curve_state, "contango")

    def test_no_futures_data_gives_empty_table(self):
        self.assertTrue(futures.weekly_curve(prices([("WTI", D(2026, 9, 29), 96.16)])).empty)


class TestAgreement(unittest.TestCase):
    def test_rates(self):
        weeks = pd.DataFrame({
            "tightness_label": ["tight", "tight", "tight", "loose", "loose", "normal", "normal", None],
            "curve_state": ["backwardation", "backwardation", "contango", "contango", "flat",
                            "backwardation", "contango", "backwardation"],
        })
        a = futures.agreement(weeks)
        self.assertEqual(a["weeks"], 7)                              # unscored week left out
        self.assertAlmostEqual(a["tight_in_backwardation"], 2 / 3)
        self.assertAlmostEqual(a["loose_in_contango"], 1 / 2)
        self.assertAlmostEqual(a["all_in_backwardation"], 3 / 7)    # base rate to compare against
        self.assertAlmostEqual(a["backwardation_scored_tight"], 2 / 3)
        self.assertAlmostEqual(a["contango_scored_loose"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
