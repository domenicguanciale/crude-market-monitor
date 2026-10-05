import datetime as dt
import unittest

import pandas as pd

import score


class TestPoints(unittest.TestCase):
    def test_stock_points(self):
        self.assertEqual(score.stock_points(0.10), 1)    # low stocks: tight
        self.assertEqual(score.stock_points(0.50), 0)
        self.assertEqual(score.stock_points(0.90), -1)   # high stocks: loose
        self.assertEqual(score.stock_points(-0.31), 1)   # below the range counts as low
        self.assertEqual(score.stock_points(0.25), 0)    # exactly on the line is not below it
        self.assertEqual(score.stock_points(0.75), 0)

    def test_utilization_points_run_the_other_way(self):
        self.assertEqual(score.utilization_points(0.90), 1)   # busy refineries: tight
        self.assertEqual(score.utilization_points(0.10), -1)
        self.assertEqual(score.utilization_points(1.27), 1)
        self.assertEqual(score.utilization_points(0.75), 0)


class TestScore(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(score.score_week(0.1, 0.1, 0.9), (3, "tight"))
        self.assertEqual(score.score_week(0.1, 0.1, 0.5), (2, "tight"))
        self.assertEqual(score.score_week(0.9, 0.1, 0.9), (1, "normal"))
        self.assertEqual(score.score_week(0.5, 0.5, 0.5), (0, "normal"))
        self.assertEqual(score.score_week(0.9, 0.9, 0.5), (-2, "loose"))
        self.assertEqual(score.score_week(0.9, 0.9, 0.1), (-3, "loose"))

    def test_missing_input_gives_no_score(self):
        self.assertEqual(score.score_week(0.1, None, 0.9), (None, None))
        self.assertEqual(score.score_week(0.1, float("nan"), 0.9), (None, None))


class TestSpread(unittest.TestCase):
    def test_week_ending_is_the_next_friday(self):
        self.assertEqual(score.week_ending_of(dt.date(2026, 9, 21)), dt.date(2026, 9, 25))  # Monday
        self.assertEqual(score.week_ending_of(dt.date(2026, 9, 25)), dt.date(2026, 9, 25))  # Friday
        self.assertEqual(score.week_ending_of(dt.date(2026, 9, 26)), dt.date(2026, 10, 2))  # Saturday

    def test_weekly_average_uses_only_days_with_both_prices(self):
        rows = [
            ("WTI", dt.date(2026, 9, 21), 90.0), ("Brent", dt.date(2026, 9, 21), 110.0),  # spread 20
            ("WTI", dt.date(2026, 9, 22), 90.0), ("Brent", dt.date(2026, 9, 22), 100.0),  # spread 10
            ("Brent", dt.date(2026, 9, 23), 500.0),                                        # no WTI: skipped
            ("WTI", dt.date(2026, 9, 29), 96.16), ("Brent", dt.date(2026, 9, 29), 113.96),  # next week
        ]
        prices = pd.DataFrame(rows, columns=["benchmark", "price_date", "price"])
        result = score.weekly_spread(prices).set_index("week_ending")["spread"]
        self.assertAlmostEqual(result[dt.date(2026, 9, 25)], 15.0)
        self.assertAlmostEqual(result[dt.date(2026, 10, 2)], 17.80)

    def test_other_series_ending_early_do_not_remove_days(self):
        rows = [
            ("WTI", dt.date(2026, 9, 21), 90.0), ("Brent", dt.date(2026, 9, 21), 110.0),
            ("WTI future 1", dt.date(2024, 4, 5), 86.9),  # a series that stopped in 2024
        ]
        prices = pd.DataFrame(rows, columns=["benchmark", "price_date", "price"])
        result = score.weekly_spread(prices).set_index("week_ending")["spread"]
        self.assertAlmostEqual(result[dt.date(2026, 9, 25)], 20.0)


if __name__ == "__main__":
    unittest.main()
