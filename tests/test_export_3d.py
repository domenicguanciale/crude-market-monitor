import datetime as dt
import gzip
import unittest

import pandas as pd

import db
import export_3d


class TestExport3D(unittest.TestCase):
    def test_restricted_series_are_refused(self):
        self.assertTrue(all(export_3d.PUBLISHABLE.values()))
        saved = dict(export_3d.PUBLISHABLE)
        try:
            export_3d.PUBLISHABLE["NASDAQ"] = False
            with self.assertRaises(RuntimeError):
                export_3d.check_publishable()
        finally:
            export_3d.PUBLISHABLE.clear(); export_3d.PUBLISHABLE.update(saved)

    def test_pins_only_for_hand_checked_events(self):
        con = db.connect(":memory:")
        con.execute("""INSERT INTO facility (facility_id, name, type, latitude, longitude) VALUES
                       ('checked-field', 'Checked field', 'field', 28.0, 49.0),
                       ('unchecked-field', 'Unchecked field', 'field', 29.0, 48.0)""")
        con.execute("""INSERT INTO disruption_event (event_id, event_name, facility_id, hand_checked) VALUES
                       ('W90', 'a', 'checked-field', TRUE), ('W91', 'b', 'unchecked-field', FALSE)""")
        ids = [f["id"] for f in export_3d.region_block(con)["facilities"]]
        self.assertEqual(ids, ["checked-field"])


    def test_spike_notes_only_when_hand_checked(self):
        con = db.connect(":memory:")
        con.execute("""INSERT INTO source (source_id, publisher, url) VALUES ('spk-S99-1', 'EIA', 'https://www.eia.gov/x')""")
        con.execute("""INSERT INTO spike (spike_id, benchmark, kind, rule, direction, start_date, extreme_date, end_date,
                       start_price, extreme_price, size_usd, size_pct, nonpositive, cause_note, source_ids, hand_checked) VALUES
                       ('A', 'Brent', 'surge', 'r', 'up', '2026-03-02', '2026-04-17', '2026-04-17', 70, 120, 50, 0.71, FALSE, 'checked note', 'spk-S99-1', TRUE),
                       ('B', 'Brent', 'crash', 'r', 'down', '2008-07-03', '2008-12-24', '2008-12-24', 140, 40, -100, -0.71, FALSE, 'draft note', 'spk-S99-1', FALSE)""")
        out = {r["id"]: r for r in export_3d.spike_block(con)}
        self.assertEqual(out["A"]["note"], "checked note")
        self.assertEqual(out["A"]["sources"], [["EIA", "https://www.eia.gov/x"]])
        self.assertNotIn("note", out["B"])                 # an unchecked explanation never leaves the machine
        self.assertNotIn("sources", out["B"])
        self.assertFalse(out["B"]["checked"])

    def test_spikes_on_an_unconfirmed_print_are_tagged(self):
        bench, day = next(iter(export_3d.spikes.UNCONFIRMED))     # ("Brent", the date of the unconfirmed print)
        con = db.connect(":memory:")
        con.execute("""INSERT INTO spike (spike_id, benchmark, kind, rule, direction, start_date, extreme_date, end_date, nonpositive) VALUES
                       ('S1', 'Brent-WTI', 'spread', 'r', 'up', ?, ?, ?, FALSE),
                       ('S2', 'WTI', 'daily', 'r', 'up', ?, ?, ?, FALSE)""", [day - dt.timedelta(days=3), day, day] * 2)
        out = {r["id"]: r for r in export_3d.spike_block(con)}
        self.assertTrue(out["S1"].get("unconfirmed"))      # a Brent minus WTI spike rests on the Brent print
        self.assertFalse(out["S2"].get("unconfirmed", False))

    def test_flows_export_measured_tiers_only(self):
        self.assertNotIn("C", export_3d.EXPORTED_TIERS)
        con = db.connect(":memory:")
        con.execute("""INSERT INTO country (iso3, name, region, label_lat, label_lon) VALUES
                       ('USA', 'United States', 'Americas', 39, -97), ('CAN', 'Canada', 'Americas', 60, -100), ('SAU', 'Saudi Arabia', 'Asia', 24, 45)""")
        con.execute("""INSERT INTO trade_flow (period, exporter, importer, product, tier, volume_kbd, source_id) VALUES
                       ('2025-01-01', 'CAN', 'USA', 'crude', 'A', 4000, 'ds-eia-impcus'),
                       ('2025-02-01', 'CAN', 'USA', 'crude', 'A', 3800, 'ds-eia-impcus'),
                       ('2025-01-01', 'SAU', 'USA', 'crude', 'C', 999, 'model')""")
        con.execute("""INSERT INTO production_by_country (period, country, volume_kbd, source_id) VALUES
                       ('2025-01-01', 'SAU', 9000, 'ds-eia-intl'), ('2025-02-01', 'SAU', 9200, 'ds-eia-intl'), ('2025-02-01', 'XXX', 5, 'ds-eia-intl')""")
        f = export_3d.flows_block(con)
        self.assertEqual(list(f["us_imports"]), ["CAN"])     # the modeled SAU row (tier C) is not exported
        self.assertEqual(f["us_imports"]["CAN"], {"s": 0, "v": [4000.0, 3800.0]})
        self.assertEqual(f["us_imports_base"]["CAN"], [3900.0, 2])
        self.assertEqual(f["production"]["SAU"]["v"], [9000.0, 9200.0])
        self.assertEqual(f["unmapped_producers"], ["XXX"])
        self.assertEqual(f["months"], ["2025-01", "2025-02"])

    def test_weekly_rows_average_trading_days(self):
        con = db.connect(":memory:")
        days = pd.bdate_range("2026-04-13", "2026-04-17")      # Monday to Friday, ISO week 16
        for d, p in zip(days, [90, 92, 94, 96, 98]):
            con.execute("INSERT INTO price_series (benchmark, price_date, price) VALUES ('Brent', ?, ?)", [d.date(), p])
        con.execute("INSERT INTO daily_indicator (indicator, obs_date, value) VALUES ('RV20_BRENT', '2026-04-16', 1.0), ('RV20_BRENT', '2026-04-17', 1.12)")
        idx = export_3d.day_index(pd.Timestamp("2026-04-20"))
        m = export_3d.market_block(con, idx)
        self.assertEqual(m["weekly"]["brent"], [[2026, 16, "2026-04-17", 94.0, 1.12]])
        rv = m["rv20"]["brent"]                                # trading days only, nothing carried over the weekend
        self.assertEqual(rv["v"], [1.0, 1.12])

    def test_dash_block_columns_and_positioning(self):
        con = db.connect(":memory:")
        con.execute("""INSERT INTO weekly_reading (week_ending, crude_stocks, crude_low, crude_avg, crude_high, crude_position, spr_stocks, futures_gap_pct, curve_state)
                       VALUES ('2024-04-05', 450000, 400000, 440000, 480000, 0.625, 365000, 0.021, 'backwardation')""")
        con.execute("""INSERT INTO trader_positioning (report_date, released, week_ending, contract_code, open_interest, commercial_long, commercial_short, mm_net_pct_oi)
                       VALUES ('2024-04-02', '2024-04-05', '2024-04-05', '067651', 1000, 300, 420, 0.15)""")
        con.execute("INSERT INTO retail_fuel_price (product, week_date, price) VALUES ('gasoline', '2024-04-01', 3.6)")
        idx = export_3d.day_index(pd.Timestamp("2024-04-10"))
        x = export_3d.dash_block(con, idx)
        self.assertEqual(x["weekly"]["d"], ["2024-04-05"])
        self.assertEqual(x["weekly"]["crude_stocks"], [450000.0])
        self.assertEqual(x["weekly"]["crude_position"], [0.625])
        self.assertEqual(x["weekly"]["curve"], ["backwardation"])
        self.assertEqual(x["cot"]["comm"], [-0.12])            # (300 - 420) / 1000
        self.assertEqual(x["cot"]["released"], ["2024-04-05"])   # timing uses the release date
        self.assertEqual(x["gasoline"], {"d": ["2024-04-01"], "v": [3.6]})
        self.assertEqual(x["diesel"], {"d": [], "v": []})
        self.assertIn("EIA", x["sources"]["weekly"].replace("U.S. Energy Information Administration", "EIA"))

    def test_size_budget(self):
        for name, limit_kb in export_3d.BUDGET_KB.items():
            path = export_3d.OUT.parent / name
            if not path.exists():
                self.skipTest(name + " not exported yet")
            kb = len(gzip.compress(path.read_bytes())) / 1024
            self.assertLess(kb, limit_kb, f"{name} is {kb:.0f} KB gzipped, over its {limit_kb} KB budget")


if __name__ == "__main__":
    unittest.main()
