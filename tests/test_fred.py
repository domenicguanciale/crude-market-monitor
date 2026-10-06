import datetime as dt
import unittest

import db
import fred


class TestFred(unittest.TestCase):
    def test_missing_days_are_dropped(self):
        df = fred.parse([{"date": "2026-10-01", "value": "51.69"}, {"date": "2026-10-02", "value": "."},
                         {"date": "2026-10-05", "value": "51.00"}])
        self.assertEqual(list(df.obs_date), [dt.date(2026, 10, 1), dt.date(2026, 10, 5)])
        self.assertEqual(list(df.value), [51.69, 51.00])

    def test_store_updates_revised_values(self):
        con = db.connect(":memory:")
        fred.store(con, "OVX", fred.parse([{"date": "2026-10-01", "value": "51.69"}]))
        fred.store(con, "OVX", fred.parse([{"date": "2026-10-01", "value": "51.70"}]))
        self.assertEqual(con.execute("SELECT count(*), max(value) FROM daily_indicator").fetchone(), (1, 51.70))

    def test_every_indicator_records_its_publishing_terms(self):
        for name, meta in fred.INDICATORS.items():
            self.assertIn("publishable", meta, name)
            self.assertIn("owner", meta, name)
        self.assertFalse(fred.INDICATORS["OVX"]["publishable"])   # CBOE copyright
        self.assertFalse(fred.INDICATORS["NASDAQ"]["publishable"])     # Nasdaq copyright
        self.assertFalse(fred.INDICATORS["HY_SPREAD"]["publishable"])  # ICE: reproduction prohibited
        self.assertTrue(fred.INDICATORS["UST10Y"]["publishable"])      # Federal Reserve, public domain


if __name__ == "__main__":
    unittest.main()
