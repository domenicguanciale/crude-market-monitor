import unittest

import db


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.con = db.connect(":memory:")  # a throwaway database in memory

    def test_one_table_per_object_type(self):
        tables = {r[0] for r in self.con.execute(
            "SELECT table_name FROM information_schema.tables").fetchall()}
        self.assertEqual(tables, {"facility", "disruption_event", "source",
                                  "price_series", "weekly_reading",
                                  "prediction_market", "market_reading", "trader_positioning", "daily_indicator", "staged_event", "chokepoint_transit", "retail_fuel_price", "spike", "country", "trade_flow", "production_by_country"})

    def test_price_cannot_repeat_for_same_day(self):
        self.con.execute("INSERT INTO price_series VALUES ('WTI', '2026-09-29', 96.16)")
        with self.assertRaises(Exception):
            self.con.execute("INSERT INTO price_series VALUES ('WTI', '2026-09-29', 99.00)")

    def test_connect_twice_is_safe(self):
        # Running the schema again must not wipe or duplicate anything
        self.con.execute("INSERT INTO weekly_reading (week_ending, crude_stocks) VALUES ('2026-09-25', 427320)")
        self.con.execute(db.SCHEMA)
        self.assertEqual(self.con.execute("SELECT count(*) FROM weekly_reading").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
