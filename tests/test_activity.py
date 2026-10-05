import datetime as dt
import unittest

import pandas as pd

import activity

D = dt.date


def readings(prices, volumes=None, start=D(2026, 3, 1), totals=None):
    n = len(prices)
    return pd.DataFrame({
        "reading_date": [start + dt.timedelta(days=i) for i in range(n)],
        "price": prices,
        "volume": volumes if volumes is not None else [None] * n,
        "total_volume": totals if totals is not None else [None] * n,
    })


class TestFlagMarket(unittest.TestCase):
    def test_big_move_after_quiet_month_is_flagged(self):
        prices = [0.50 + 0.01 * (i % 2) for i in range(20)] + [0.70]   # 1-point wiggles, then +19 points
        f = activity.flag_market(readings(prices), closes=D(2026, 12, 31))
        last = f.iloc[-1]
        self.assertEqual(last.reading_date, D(2026, 3, 21))
        self.assertTrue(last.odds_flag)
        self.assertFalse(f.iloc[:-1]["odds_flag"].any())

    def test_move_below_floor_is_not_flagged(self):
        prices = [0.50] * 20 + [0.58]        # typical move is 0, but 8 points is under the 10-point floor
        self.assertFalse(activity.flag_market(readings(prices), D(2026, 12, 31))["odds_flag"].any())

    def test_too_little_history_is_not_evaluated(self):
        f = activity.flag_market(readings([0.5] * 10 + [0.9]), D(2026, 12, 31))
        self.assertTrue(f.empty)

    def test_days_just_before_close_are_skipped(self):
        prices = [0.50] * 20 + [0.99]        # jump to near-certainty as the question resolves
        f = activity.flag_market(readings(prices), closes=D(2026, 3, 23))   # jump is 2 days before close
        self.assertNotIn(D(2026, 3, 21), set(f["reading_date"]))

    def test_volume_spike(self):
        vols = [200.0] * 20 + [5000.0]
        f = activity.flag_market(readings([0.5] * 21, volumes=vols), D(2026, 12, 31))
        self.assertTrue(f.iloc[-1].volume_flag)
        self.assertFalse(f.iloc[:-1]["volume_flag"].any())

    def test_volume_spike_below_floor_is_not_flagged(self):
        vols = [10.0] * 20 + [900.0]         # 90 times normal, but under 1,000
        self.assertFalse(activity.flag_market(readings([0.5] * 21, volumes=vols), D(2026, 12, 31))["volume_flag"].any())


class TestPolymarketVolume(unittest.TestCase):
    def test_daily_volume_from_consecutive_totals_only(self):
        r = pd.DataFrame({"reading_date": [D(2026, 10, 5), D(2026, 10, 6), D(2026, 10, 9)],
                          "total_volume": [1000.0, 1300.0, 2000.0]})
        v = activity.daily_volume_from_totals(r)
        self.assertEqual(dict(v), {D(2026, 10, 6): 300.0})   # Oct 9 has no Oct 8 total


class TestTopicDays(unittest.TestCase):
    def test_unusual_days_are_the_top_share(self):
        rows = []
        for day in range(1, 21):
            for m in range(25):
                flagged = day == 15 and m < 10      # 10 of 25 markets flagged on the 15th only
                rows.append({"topic": "gulf_conflict", "reading_date": D(2026, 4, day), "market_key": f"m{m}",
                             "odds_flag": flagged, "volume_flag": False})
        days = activity.topic_days(pd.DataFrame(rows))
        self.assertEqual(list(days.loc[days["unusual"], "reading_date"]), [D(2026, 4, 15)])

    def test_days_with_few_markets_are_not_counted(self):
        rows = [{"topic": "oil_price", "reading_date": D(2026, 4, 1), "market_key": f"m{m}",
                 "odds_flag": True, "volume_flag": False} for m in range(5)]
        self.assertTrue(activity.topic_days(pd.DataFrame(rows)).empty)


class TestEventWindow(unittest.TestCase):
    def test_window_is_day_minus_4_to_minus_2(self):
        event = D(2026, 4, 10)
        self.assertTrue(activity.window_has_unusual(event, {D(2026, 4, 6)}))    # day -4
        self.assertTrue(activity.window_has_unusual(event, {D(2026, 4, 8)}))    # day -2
        self.assertFalse(activity.window_has_unusual(event, {D(2026, 4, 9)}))   # day -1: time-zone buffer
        self.assertFalse(activity.window_has_unusual(event, {D(2026, 4, 10)}))  # the event day itself
        self.assertFalse(activity.window_has_unusual(event, {D(2026, 4, 5)}))   # day -5

    def test_event_comparison_against_base_rate(self):
        days = pd.DataFrame({"topic": "gulf_conflict",
                             "reading_date": [D(2026, 4, 1) + dt.timedelta(days=i) for i in range(30)],
                             "unusual": [i == 10 for i in range(30)]})   # April 11 unusual
        r = activity.event_comparison(days, [D(2026, 4, 14), D(2026, 4, 25)], "gulf_conflict")
        self.assertEqual((r["events"], r["preceded"]), (2, 1))    # April 14 has April 11 at day -3
        self.assertEqual(r["days"], 26)                           # April 5 to 30
        self.assertAlmostEqual(r["base_rate"], 3 / 26)            # April 13, 14, 15


if __name__ == "__main__":
    unittest.main()
