import datetime as dt
import unittest

import numpy as np
import pandas as pd

import db
import flows
import ipf

D = dt.date


class TestParsing(unittest.TestCase):
    def test_us_imports_keep_countries_and_kbd_only(self):
        rows = [{"period": "2026-07", "area-name": "SAU", "series": "MCRIMUSSA2", "value": "359"},
                {"period": "2026-07", "area-name": "SAU", "series": "MCRIMUSSA1", "value": "11129"},   # thousand barrels: dropped
                {"period": "2026-07", "area-name": "NA", "series": "MCRIMXX2", "value": "999"},         # regional total: dropped
                {"period": "2026-07", "area-name": "U.S.", "series": "MCRIMUS2", "value": "6224"}]     # US total: dropped
        df = flows.parse_us_imports(rows)
        self.assertEqual(df[["exporter", "importer", "volume_kbd", "tier"]].values.tolist(), [["SAU", "USA", 359.0, "A"]])
        self.assertEqual(df.iloc[0].period, D(2026, 7, 1))

    def test_production_countries_only(self):
        rows = [{"period": "2026-06", "countryRegionId": "IRQ", "countryRegionTypeId": "c", "value": "1945"},
                {"period": "2026-06", "countryRegionId": "WORL", "countryRegionTypeId": "r", "value": "80000"},
                {"period": "2026-06", "countryRegionId": "XYZ", "countryRegionTypeId": "c", "value": "--"}]
        df = flows.parse_production(rows)
        self.assertEqual(df.country.tolist(), ["IRQ"])

    def test_countries_use_iso_codes_and_add_small_countries(self):
        geo = {"features": [{"properties": {"ADM0_A3": "FRA", "ISO_A3": "-99", "NAME": "France", "REGION_UN": "Europe",
                                            "SUBREGION": "Western Europe", "LABEL_Y": 46.7, "LABEL_X": 2.6}},
                            {"properties": {"ADM0_A3": "SDS", "ISO_A3": "SSD", "NAME": "S. Sudan", "REGION_UN": "Africa",
                                            "SUBREGION": "Eastern Africa", "LABEL_Y": 7.2, "LABEL_X": 30.4}}]}
        extra = pd.DataFrame({"iso3": ["BHR", "FRA"], "label_lat": [26.05, 0.0], "label_lon": [50.54, 0.0]})
        df = flows.parse_countries(geo, extra).set_index("iso3")
        self.assertEqual(sorted(df.index), ["BHR", "FRA", "SSD"])     # ISO code, '-99' fallback, extra point added
        self.assertEqual(df.loc["FRA", "label_lat"], 46.7)             # the main file wins over extra points


class TestRevisions(unittest.TestCase):
    def test_revision_keeps_the_earlier_value(self):
        con = db.connect(":memory:")
        row = lambda v: pd.DataFrame([{"period": D(2026, 6, 1), "country": "IRQ", "volume_kbd": v, "source_id": "ds-eia-intl"}])
        flows.upsert_with_revisions(con, "production_by_country", row(1945.0), ["period", "country"])
        flows.upsert_with_revisions(con, "production_by_country", row(1945.0), ["period", "country"])   # unchanged
        self.assertEqual(con.execute("SELECT revised FROM production_by_country").fetchone()[0], False)
        flows.upsert_with_revisions(con, "production_by_country", row(1990.0), ["period", "country"])   # revised
        self.assertEqual(con.execute("SELECT volume_kbd, previous_volume, revised FROM production_by_country").fetchone(),
                         (1990.0, 1945.0, True))


class TestIPF(unittest.TestCase):
    def test_worked_example_from_methods(self):
        # METHODS.md section 12: two exporters, two importers, a prior from last year's shares
        prior = [[60, 40], [20, 80]]
        table, n = ipf.ipf(prior, row_totals=[120, 80], col_totals=[90, 110])
        np.testing.assert_allclose(table.sum(axis=1), [120, 80], rtol=1e-6)
        np.testing.assert_allclose(table.sum(axis=0), [90, 110], rtol=1e-6)
        np.testing.assert_allclose(table, [[73.38, 46.62], [16.62, 63.38]], atol=0.01)
        self.assertEqual(n, 6)

    def test_zero_cells_stay_zero(self):
        table, _ = ipf.ipf([[1, 0], [1, 1]], [10, 10], [15, 5])
        self.assertEqual(table[0, 1], 0)

    def test_inconsistent_totals_and_impossible_priors_are_refused(self):
        with self.assertRaises(ValueError):
            ipf.ipf([[1, 1], [1, 1]], [10, 10], [15, 6])               # 20 vs 21
        with self.assertRaises(ValueError):
            ipf.ipf([[0, 0], [1, 1]], [10, 10], [10, 10])              # a row with a total but no prior


if __name__ == "__main__":
    unittest.main()
