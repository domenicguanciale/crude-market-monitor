import datetime as dt
import json
import unittest

import db
import fetch_markets
import prediction_markets as pm

D = dt.date


class TestSelection(unittest.TestCase):
    def test_topics(self):
        self.assertEqual(pm.topic_of("What will WTI Crude Oil (WTI) hit in April 2026?"), "oil_price")
        self.assertEqual(pm.topic_of("Brent Monthly"), "oil_price")
        self.assertEqual(pm.topic_of("US x Iran ceasefire extended by...?"), "gulf_conflict")
        self.assertEqual(pm.topic_of("Strait of Hormuz traffic returns to normal by December 31?"), "gulf_conflict")
        self.assertEqual(pm.topic_of("Iran military action against a Gulf State on...?"), "gulf_conflict")

    def test_out_of_scope(self):
        self.assertIsNone(pm.topic_of("Brentford FC vs. Chelsea FC"))       # 'brent' as a whole word only
        self.assertIsNone(pm.topic_of("Iran leader end of 2026?"))          # politics, not conflict
        self.assertIsNone(pm.topic_of("Israel x Hezbollah ceasefire by...?"))  # not the Gulf
        self.assertIsNone(pm.topic_of("Will Trump rename the Strait of Hormuz?"))
        self.assertIsNone(pm.topic_of("Saudi Arabia crude oil production"))
        self.assertIsNone(pm.topic_of("Alaska gas price"))

    def test_in_scope_rules(self):
        title = "US x Iran ceasefire by...?"
        self.assertTrue(pm.in_scope(title, 50_000, D(2026, 3, 1), D(2026, 4, 30)))
        self.assertFalse(pm.in_scope(title, 9_999, D(2026, 3, 1), D(2026, 4, 30)))      # volume floor
        self.assertFalse(pm.in_scope(title, 50_000, D(2025, 3, 1), D(2025, 12, 31)))    # closed before 2026
        self.assertFalse(pm.in_scope(title, 50_000, D(2026, 4, 1), D(2026, 4, 2)))      # one-day market
        self.assertFalse(pm.in_scope(title, None, D(2026, 3, 1), D(2026, 4, 30)))


class TestParsing(unittest.TestCase):
    def test_polymarket_market_keeps_only_allowed_fields(self):
        raw = {"id": "2176270", "question": "Strait of Hormuz traffic returns to normal by December 31?",
               "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(["0.185", "0.815"]),
               "clobTokenIds": json.dumps(["111", "222"]), "volumeNum": 14194129.95,
               "startDate": "2026-05-11T13:03:57Z", "endDate": "2027-01-01T04:59:00Z", "closed": False,
               "marketMakerAddress": "0xABC", "resolvedBy": "0xDEF", "submitted_by": "0x123"}
        row = pm.parse_poly_market(raw, "Strait of Hormuz traffic returns to normal by December 31?")
        self.assertEqual(row["market_key"], "polymarket:2176270")
        self.assertEqual((row["outcome"], row["_price_now"], row["_token"]), ("Yes", 0.185, "111"))
        self.assertEqual((row["opened"], row["closes"]), (D(2026, 5, 11), D(2027, 1, 1)))
        self.assertEqual(row["topic"], "gulf_conflict")
        stored = set(fetch_markets.MARKET_COLUMNS)
        self.assertFalse(any("0x" in str(row.get(c)) for c in stored))   # no address reaches a column

    def test_polymarket_closes_each_eastern_day(self):
        ts = lambda *a: int(dt.datetime(*a, tzinfo=dt.UTC).timestamp())
        history = pm.parse_poly_history([
            {"t": ts(2026, 10, 4, 3, 0), "p": 0.20},   # 11 p.m. Eastern, Oct 3: Oct 3's close
            {"t": ts(2026, 10, 4, 12, 0), "p": 0.19},
            {"t": ts(2026, 10, 5, 3, 0), "p": 0.185},  # 11 p.m. Eastern, Oct 4: Oct 4's close
            {"t": ts(2026, 10, 5, 4, 0), "p": 0.17},   # midnight Eastern: already Oct 5
        ])
        self.assertEqual(history, {D(2026, 10, 3): 0.20, D(2026, 10, 4): 0.185, D(2026, 10, 5): 0.17})

    def test_kalshi_candle_is_filed_under_the_day_it_covers(self):
        ts = lambda *a: int(dt.datetime(*a, tzinfo=dt.UTC).timestamp())
        candles = [
            # Summer: Eastern midnight is 04:00 UTC. Ending Oct 5 04:00 UTC covers Oct 4.
            {"end_period_ts": ts(2026, 10, 5, 4), "price": {"close_dollars": "0.7200"}, "volume_fp": "549.65"},
            # Winter: Eastern midnight is 05:00 UTC. Ending Jan 10 05:00 UTC covers Jan 9.
            {"end_period_ts": ts(2026, 1, 10, 5), "price": {}, "volume_fp": "0"},   # no trade: no price
        ]
        out = pm.parse_kalshi_candles(candles)
        self.assertEqual(out, {D(2026, 10, 4): (0.72, 549.65), D(2026, 1, 9): (None, 0.0)})

    def test_eastern_date(self):
        self.assertEqual(pm.eastern_date(dt.datetime(2026, 3, 1, 3, 0, tzinfo=dt.UTC)), D(2026, 2, 28))
        self.assertEqual(pm.eastern_date(dt.datetime(2026, 3, 1, 6, 0, tzinfo=dt.UTC)), D(2026, 3, 1))


class TestSaving(unittest.TestCase):
    def setUp(self):
        self.con = db.connect(":memory:")
        self.market = {"market_key": "kalshi:X", "platform": "kalshi", "market_id": "X", "event_title": "e",
                       "question": "q", "outcome": "Yes", "topic": "gulf_conflict", "opened": D(2026, 3, 1),
                       "closes": D(2026, 12, 31), "status": "open", "result": None, "total_volume": 20000.0,
                       "volume_unit": "contracts", "_price_now": 0.6}

    def test_rerun_never_deletes_history(self):
        now = dt.datetime(2026, 10, 5, 12)
        fetch_markets.save_markets(self.con, [self.market])
        fetch_markets.save_readings(self.con, fetch_markets.readings_for(
            self.market, {D(2026, 9, 1): (0.4, 100.0)}, now))
        # Second run: the platform no longer returns September (e.g. history trimmed) and the market closed
        closed = dict(self.market, status="closed", result="yes")
        fetch_markets.save_markets(self.con, [closed])
        fetch_markets.save_readings(self.con, fetch_markets.readings_for(closed, {}, now))
        rows = self.con.execute("SELECT reading_date, price, volume FROM market_reading ORDER BY 1").fetchall()
        self.assertEqual(rows[0], (D(2026, 9, 1), 0.4, 100.0))        # September survived
        self.assertEqual(self.con.execute("SELECT status, result FROM prediction_market").fetchone(),
                         ("closed", "yes"))

    def test_today_appears_once_with_snapshot_volume(self):
        now = dt.datetime(2026, 10, 5, 12)
        today = pm.today_eastern()
        rows = fetch_markets.readings_for(self.market, {today: (0.55, 40.0), D(2026, 9, 1): (0.4, 100.0)}, now)
        todays = [r for r in rows if r[1] == today]
        self.assertEqual(len(todays), 1)
        self.assertEqual(todays[0][2:5], [0.6, 40.0, 20000.0])   # snapshot price, candle volume, all-time total

    def test_rerun_fetches_only_recent_days(self):
        fetch_markets.save_markets(self.con, [self.market])
        fetch_markets.save_readings(self.con, [["kalshi:X", D(2026, 9, 30), 0.5, None, None, dt.datetime(2026, 9, 30)]])
        m = fetch_markets.resume_from(self.con, [dict(self.market)])[0]
        self.assertEqual(m["opened"], D(2026, 9, 27))
        self.assertEqual(self.con.execute("SELECT opened FROM prediction_market").fetchone()[0], D(2026, 3, 1))

    def test_update_fills_in_without_erasing(self):
        now = dt.datetime(2026, 10, 5, 12)
        fetch_markets.save_markets(self.con, [self.market])
        fetch_markets.save_readings(self.con, [["kalshi:X", D(2026, 10, 5), 0.6, 300.0, None, now]])
        fetch_markets.save_readings(self.con, [["kalshi:X", D(2026, 10, 5), None, None, 20000.0, now]])
        self.assertEqual(self.con.execute("SELECT price, volume, total_volume FROM market_reading").fetchone(),
                         (0.6, 300.0, 20000.0))


if __name__ == "__main__":
    unittest.main()
