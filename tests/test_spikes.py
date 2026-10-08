"""Spike rules on synthetic prices with known answers (M2)."""
import datetime as dt
import unittest

import numpy as np
import pandas as pd

import db
import spikes


def series(values, start="2020-01-01"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)), dtype=float)


class TestReturns(unittest.TestCase):
    def test_negative_price_guards(self):
        r = spikes.returns(series([18.31, -36.98, 8.91, 13.64]))
        self.assertAlmostEqual(r["dollar"].iloc[1], -55.29)
        self.assertAlmostEqual(r["pct"].iloc[1], -36.98 / 18.31 - 1)   # previous price positive: defined
        self.assertTrue(np.isnan(r["pct"].iloc[2]))                     # after a negative price: undefined
        self.assertTrue(np.isnan(r["log"].iloc[1]) and np.isnan(r["log"].iloc[2]))   # never log of a non-positive price
        self.assertAlmostEqual(r["log"].iloc[3], np.log(13.64 / 8.91))
        self.assertEqual(list(r["nonpositive"]), [False, True, True, False])

    def test_daily_shocks_thresholds_and_negative_case(self):
        p = series([100, 101, 110, 96, 96.5, -1, 5])                   # +8.9%, -12.7%, then a negative print
        rules = spikes.daily_shocks(p, thresholds=(0.08, 0.12), z_threshold=99)["rule"].tolist()
        self.assertEqual(rules[:2], ["daily >= 8%", "daily >= 12%"])
        self.assertEqual(rules[2:], ["non-positive price", "non-positive price"])

    def test_zscore_uses_only_past_days(self):
        rng = np.random.default_rng(1)
        p = series(list(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300)))) + [0])
        p.iloc[-1] = p.iloc[-2] * 1.10                                   # a 10% jump after quiet days (sd about 1%)
        z = spikes.zscores(spikes.returns(p)["log"])
        self.assertGreater(z.iloc[-1], 8)


class TestEpisodes(unittest.TestCase):
    def test_surge_found_with_known_size(self):
        p = series([50] * 10 + list(np.linspace(50, 80, 21)) + [80] * 10)   # +60% over 20 days
        e = spikes.window_episodes(p, "up", pct=0.40, window=60)
        self.assertEqual(len(e), 1)
        self.assertAlmostEqual(e.iloc[0].size_pct, 0.60)
        self.assertEqual(e.iloc[0].start_price, 50)

    def test_slow_rise_beyond_window_is_not_a_surge(self):
        p = series(list(np.linspace(50, 80, 300)))                    # +60% but over 300 days
        self.assertTrue(spikes.window_episodes(p, "up", pct=0.40, window=60).empty)

    def test_crash_to_negative_is_flagged_below_zero(self):
        p = series([60] * 5 + [40, 20, -5, 10] + [12] * 5)
        e = spikes.window_episodes(p, "down", pct=0.35, window=60)
        self.assertEqual(len(e), 1)
        self.assertTrue(e.iloc[0].nonpositive)
        self.assertEqual(e.iloc[0].extreme_price, -5)

    def test_surge_from_a_negative_low_uses_the_lowest_positive_price(self):
        p = series([20, -10, 8, 14, 16])
        e = spikes.window_episodes(p, "up", pct=0.40, window=60)
        self.assertEqual(e.iloc[0].start_price, 8)                      # never measured from -10
        self.assertAlmostEqual(e.iloc[0].size_pct, 1.0)

    def test_drawdown_peak_trough_and_recovery(self):
        p = series([50, 100, 90, 60, 65, 70, 100, 110])                 # 100 -> 60 is -40%, back to 100 later
        d = spikes.drawdowns(p, 0.30)
        self.assertEqual(len(d), 1)
        r = d.iloc[0]
        self.assertEqual((r.start_price, r.extreme_price), (100, 60))
        self.assertAlmostEqual(r.size_pct, -0.40)
        self.assertEqual(r.recovery_date, p.index[6].date())

    def test_drawdown_with_negative_trough_is_confirmed_from_lowest_positive(self):
        p = series([60, 63, 30, 18, -37, 9, 13, 16])
        d = spikes.drawdowns(p, 0.30)
        self.assertEqual(d.iloc[0].extreme_price, -37)
        self.assertTrue(d.iloc[0].nonpositive)


class TestVolAndSpread(unittest.TestCase):
    def test_realized_vol_is_annualized(self):
        p = series(list(100 * np.exp(np.cumsum([0.01, -0.01] * 50))))  # daily log returns of +-1%
        v = spikes.realized_vol(p, 20).dropna()
        self.assertAlmostEqual(v.iloc[-1], 0.01 * np.sqrt(252) * np.sqrt(20 / 19), places=3)

    def test_percentile_rank(self):
        self.assertAlmostEqual(spikes.percentile_rank(pd.Series([1, 2, 3, 4]), 3.5), 0.75)

    def test_spread_blowouts_and_negative_wti_excluded(self):
        idx = pd.bdate_range("2020-04-15", periods=6)
        prices = {"Brent": pd.Series([28, 28, 28, 17.36, 9.12, 30], index=idx),
                  "WTI": pd.Series([20, 12, 12, -36.98, 8.91, 12], index=idx)}
        spread = spikes.positive_spread(prices)
        self.assertNotIn(idx[3], spread.index)                          # the $54.34 day is excluded
        b = spikes.spread_blowouts(spread, threshold=15)
        self.assertEqual(len(b), 1)                                     # flagged days 2 trading days apart join one episode
        self.assertEqual(b.iloc[0].extreme_price, 18)
        self.assertEqual(len(spikes.spread_blowouts(spread, threshold=15, gap=1)), 2)   # a tighter gap splits them


class TestStore(unittest.TestCase):
    def test_catalog_stores_and_is_rebuilt(self):
        p = series([50] * 10 + list(np.linspace(50, 80, 21)) + [80] * 10 + list(np.linspace(80, 40, 10)))
        prices = {"Brent": p, "WTI": p * 0.9}
        cat = spikes.catalog(prices)
        con = db.connect(":memory:")
        spikes.store(con, cat, pd.DataFrame(columns=["indicator", "obs_date", "value"]))
        spikes.store(con, cat, pd.DataFrame(columns=["indicator", "obs_date", "value"]))
        n = con.execute("SELECT count(*) FROM spike").fetchone()[0]
        self.assertEqual(n, len(cat))
        self.assertGreater(con.execute("SELECT count(*) FROM spike WHERE kind = 'surge'").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM spike WHERE hand_checked").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
