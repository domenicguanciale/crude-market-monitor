import datetime as dt
import unittest

import pandas as pd

import backtest

D = dt.date


def daily(pairs):
    return pd.Series({d: p for d, p in pairs}).sort_index()


class TestDates(unittest.TestCase):
    def test_release_is_the_wednesday_after_friday(self):
        self.assertEqual(backtest.release_date(D(2026, 9, 25)), D(2026, 9, 30))

    def test_price_on_or_after_skips_non_trading_days(self):
        prices = daily([(D(2026, 9, 25), 85.23), (D(2026, 9, 28), 99.37)])
        self.assertEqual(backtest.price_on_or_after(prices, D(2026, 9, 26)), (D(2026, 9, 28), 99.37))
        self.assertEqual(backtest.price_on_or_after(prices, D(2026, 9, 29)), (None, None))


class TestForwardReturns(unittest.TestCase):
    def test_return_runs_from_release_not_week_end(self):
        prices = daily([(D(2026, 9, 25), 50.0),   # Friday week end: must NOT be used
                        (D(2026, 9, 30), 100.0),  # Wednesday release
                        (D(2026, 10, 28), 110.0)])  # 28 days later
        weekly = pd.DataFrame({"week_ending": [D(2026, 9, 25)], "tightness_label": ["tight"]})
        r = backtest.forward_returns(weekly, prices).iloc[0]
        self.assertEqual((r.start_date, r.end_date), (D(2026, 9, 30), D(2026, 10, 28)))
        self.assertAlmostEqual(r.forward_return, 0.10)

    def test_window_past_the_data_is_dropped(self):
        prices = daily([(D(2026, 9, 30), 100.0)])
        weekly = pd.DataFrame({"week_ending": [D(2026, 9, 25)], "tightness_label": ["tight"]})
        self.assertTrue(backtest.forward_returns(weekly, prices).empty)

    def test_non_positive_price_is_dropped(self):
        prices = daily([(D(2020, 3, 25), 24.0), (D(2020, 4, 22), -36.98)])
        weekly = pd.DataFrame({"week_ending": [D(2020, 3, 20)], "tightness_label": ["loose"]})
        self.assertTrue(backtest.forward_returns(weekly, prices).empty)


class TestSummary(unittest.TestCase):
    def setUp(self):
        self.results = pd.DataFrame({
            "week_ending": [D(2020, 1, 3) + dt.timedelta(weeks=i) for i in range(8)],
            "label": ["tight", "tight", "loose", "normal", "tight", "normal", "loose", "normal"],
            "forward_return": [0.10, -0.02, -0.05, 0.01, 0.04, 0.00, 0.03, -0.01],
        })

    def test_groups(self):
        s = backtest.summarize(self.results)
        self.assertEqual(list(s["count"]), [3, 2, 8])
        self.assertAlmostEqual(s.loc["tight", "average"], 0.04)
        self.assertAlmostEqual(s.loc["tight", "median"], 0.04)
        self.assertAlmostEqual(s.loc["tight", "hit_rate"], 2 / 3)
        self.assertAlmostEqual(s.loc["all", "hit_rate"], 4 / 8)  # 0.00 is not a rise

    def test_every_fourth_week(self):
        self.assertEqual(list(backtest.every_fourth(self.results, 0).index), [0, 4])
        self.assertEqual(list(backtest.every_fourth(self.results, 3).index), [3, 7])

    def test_empty_group(self):
        s = backtest.summarize(self.results[self.results["label"] != "loose"])
        self.assertEqual(s.loc["loose", "count"], 0)
        self.assertTrue(pd.isna(s.loc["loose", "average"]))


if __name__ == "__main__":
    unittest.main()
