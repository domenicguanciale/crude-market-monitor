import datetime as dt
import unittest

import pandas as pd

import db
import monday_summary as ms


class TestMondaySummary(unittest.TestCase):
    def test_change(self):
        self.assertEqual(ms.change(5.28, 5.10), "+0.18")
        self.assertEqual(ms.change(1.0, None), "n/a")
        self.assertEqual(ms.change(float("nan"), 1.0), "n/a")

    def test_daily_latest_finds_value_a_week_earlier(self):
        con = db.connect(":memory:")
        con.execute("""INSERT INTO daily_indicator VALUES ('UST10Y', '2026-09-25', 5.10),
                       ('UST10Y', '2026-09-30', 5.20), ('UST10Y', '2026-10-02', 5.28)""")
        r = ms.daily_latest(con, "UST10Y")
        self.assertEqual((r["value"], r["before"]), (5.28, 5.10))
        self.assertEqual(pd.Timestamp(r["date"]).date(), dt.date(2026, 10, 2))
        self.assertIsNone(ms.daily_latest(con, "NASDAQ"))


if __name__ == "__main__":
    unittest.main()
