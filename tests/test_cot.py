import datetime as dt
import unittest

import cot
import db


def raw(date, long, short, oi="1000000"):
    return {"report_date_as_yyyy_mm_dd": f"{date}T00:00:00.000", "open_interest_all": oi,
            "noncomm_positions_long_all": long, "noncomm_positions_short_all": short,
            "noncomm_postions_spread_all": "500", "comm_positions_long_all": "1",
            "comm_positions_short_all": "2", "nonrept_positions_long_all": "3",
            "nonrept_positions_short_all": "4"}


class TestCot(unittest.TestCase):
    def test_net_position_and_dates(self):
        df = cot.parse([raw("2026-09-29", "361351", "251888", "1878576")])
        r = df.iloc[0]
        self.assertEqual(r.spec_net, 109463)                       # long minus short
        self.assertAlmostEqual(r.spec_net_pct_oi, 109463 / 1878576)
        self.assertEqual(r.report_date, dt.date(2026, 9, 29))      # Tuesday positions
        self.assertEqual(r.released, dt.date(2026, 10, 2))         # Friday release
        self.assertEqual(r.week_ending, dt.date(2026, 10, 2))      # EIA week ending that Friday

    def test_holiday_week_release_dates(self):
        self.assertEqual(cot.release_date(dt.date(2026, 9, 29)), dt.date(2026, 10, 2))   # Tuesday -> Friday
        self.assertEqual(cot.release_date(dt.date(2003, 12, 22)), dt.date(2003, 12, 26))  # Monday -> Friday
        self.assertEqual(cot.release_date(dt.date(2000, 7, 5)), dt.date(2000, 7, 7))      # Wednesday -> Friday
        self.assertEqual(cot.release_date(dt.date(2001, 12, 21)), dt.date(2001, 12, 28))  # Friday -> next Friday
        r = cot.parse([raw("2003-12-22", "10", "5")]).iloc[0]
        self.assertEqual(r.week_ending, dt.date(2003, 12, 26))

    def test_net_short_and_sorting(self):
        df = cot.parse([raw("2026-09-29", "100", "300"), raw("2026-09-22", "500", "100")])
        self.assertEqual(list(df.report_date), [dt.date(2026, 9, 22), dt.date(2026, 9, 29)])
        self.assertEqual(list(df.spec_net), [400, -200])

    def test_store_updates_instead_of_duplicating(self):
        con = db.connect(":memory:")
        cot.store(con, cot.parse([raw("2026-09-29", "100", "50")]))
        cot.store(con, cot.parse([raw("2026-09-29", "120", "50")]))   # CFTC correction
        self.assertEqual(con.execute("SELECT count(*), max(spec_net) FROM trader_positioning").fetchone(), (1, 70))


if __name__ == "__main__":
    unittest.main()
