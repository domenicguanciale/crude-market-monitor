import datetime as dt
import unittest

import pandas as pd

import seasonal


def weeks(rows):
    """Build a small table from (year, week, value) tuples."""
    return pd.DataFrame(rows, columns=["week_year", "week_number", "stocks"])


class TestFiveYearCompare(unittest.TestCase):
    def test_methods_example(self):
        # METHODS.md: stocks 420, five-year low 400, high 480, average 445
        df = weeks([(2021, 10, 400), (2022, 10, 480), (2023, 10, 445),
                    (2024, 10, 445), (2025, 10, 455), (2026, 10, 420)])
        r = seasonal.five_year_compare(df, "stocks").iloc[-1]
        self.assertEqual((r.low, r.high, r.avg), (400, 480, 445))
        self.assertAlmostEqual(r.position, 0.25)
        self.assertAlmostEqual(r.pct_vs_avg, -0.0562, places=4)  # minus 5.6 percent

    def test_current_year_and_other_weeks_are_ignored(self):
        df = weeks([(2021, 10, 400), (2022, 10, 480), (2023, 10, 445),
                    (2024, 10, 445), (2025, 10, 455),
                    (2026, 9, 1), (2026, 10, 420), (2026, 11, 9999),  # same year, nearby weeks
                    (2025, 11, 9999), (2020, 10, 9999)])              # other week, sixth year back
        r = seasonal.five_year_compare(df, "stocks").iloc[6]
        self.assertEqual((r.low, r.high, r.avg), (400, 480, 445))

    def test_week_53_compares_to_week_52(self):
        df = weeks([(2015, 52, 100), (2016, 52, 200), (2017, 52, 300),
                    (2018, 52, 400), (2019, 52, 500),
                    (2015, 53, 9999),            # a past week 53 is never a comparison value
                    (2020, 53, 300)])
        r = seasonal.five_year_compare(df, "stocks").iloc[-1]
        self.assertEqual((r.low, r.high), (100, 500))
        self.assertAlmostEqual(r.position, 0.5)

    def test_missing_prior_year_gives_no_result(self):
        df = weeks([(2022, 10, 480), (2023, 10, 445), (2024, 10, 445),
                    (2025, 10, 455), (2026, 10, 420)])  # only four prior years
        self.assertTrue(seasonal.five_year_compare(df, "stocks").iloc[-1].isna().all())

    def test_flat_range_gives_no_position(self):
        df = weeks([(y, 10, 90.0) for y in range(2021, 2026)] + [(2026, 10, 92.0)])
        r = seasonal.five_year_compare(df, "stocks").iloc[-1]
        self.assertTrue(pd.isna(r.position))
        self.assertAlmostEqual(r.pct_vs_avg, 2 / 90)

    def test_value_outside_range(self):
        df = weeks([(2021, 10, 400), (2022, 10, 480), (2023, 10, 445),
                    (2024, 10, 445), (2025, 10, 455), (2026, 10, 380)])
        self.assertAlmostEqual(seasonal.five_year_compare(df, "stocks").iloc[-1].position, -0.25)


class TestDropYears(unittest.TestCase):
    def test_prior_years_reach_back_past_an_excluded_year(self):
        self.assertEqual(seasonal.prior_years(2023), [2022, 2021, 2020, 2019, 2018])
        self.assertEqual(seasonal.prior_years(2023, {2020}), [2022, 2021, 2019, 2018, 2017])
        self.assertEqual(seasonal.prior_years(2026, {2020}), [2025, 2024, 2023, 2022, 2021])  # unaffected

    def test_excluded_year_is_replaced_not_left_blank(self):
        df = weeks([(2017, 10, 100), (2018, 10, 200), (2019, 10, 300), (2020, 10, 9999),
                    (2021, 10, 400), (2022, 10, 500), (2023, 10, 300)])
        default = seasonal.five_year_compare(df, "stocks").iloc[-1]
        dropped = seasonal.five_year_compare(df, "stocks", exclude_years={2020}).iloc[-1]
        self.assertEqual((default.low, default.high), (200, 9999))   # 2018-2022, 2020 included
        self.assertEqual((dropped.low, dropped.high), (100, 500))    # 2017-2022 without 2020
        self.assertAlmostEqual(dropped.avg, 300)
        self.assertAlmostEqual(dropped.position, 0.5)


class TestWeekNumbers(unittest.TestCase):
    def test_iso_weeks_of_fridays(self):
        df = seasonal.add_week_numbers(pd.DataFrame({"week_ending": [
            dt.date(2026, 9, 25),  # ordinary week
            dt.date(2021, 1, 1),   # a Friday on Jan 1 belongs to week 53 of 2020
            dt.date(2021, 1, 8),   # first week of 2021
        ]}))
        self.assertEqual(list(zip(df.week_year, df.week_number)), [(2026, 39), (2020, 53), (2021, 1)])


if __name__ == "__main__":
    unittest.main()
