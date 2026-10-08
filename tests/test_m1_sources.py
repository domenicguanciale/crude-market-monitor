"""M1: retail fuel, CFTC disaggregated positions, the dollar index flag, and the dataset source registry."""
import datetime as dt
import unittest
from pathlib import Path

import pandas as pd

import check_routes
import cot
import db
import fred
import retail_fuel
import sources

D = dt.date
ROOT = Path(__file__).resolve().parent.parent


class TestRetailFuel(unittest.TestCase):
    def test_parse_and_store(self):
        raw = pd.DataFrame({"period": pd.to_datetime(["2026-09-28", "2026-10-05", "2026-10-05"]),
                            "value": [4.30, 4.354, 4.354]})
        rows = retail_fuel.parse(raw, "gasoline")
        self.assertEqual(len(rows), 2)                                   # duplicate week dropped
        con = db.connect(":memory:")
        retail_fuel.store(con, rows)
        retail_fuel.store(con, rows)                                     # re-run does not duplicate
        self.assertEqual(con.execute("SELECT count(*), max(price) FROM retail_fuel_price").fetchone(), (2, 4.354))

    def test_retail_route_is_queried_weekly(self):
        self.assertEqual(check_routes.SERIES_ROUTES["EMM_EPMR_PTE_NUS_DPG"], "petroleum/pri/gnd")
        self.assertNotIn("petroleum/pri/gnd", check_routes.DAILY_ROUTES)
        self.assertIn("petroleum/pri/spt", check_routes.DAILY_ROUTES)


def legacy_row(date, long, short, oi):
    return {"report_date_as_yyyy_mm_dd": f"{date}T00:00:00.000", "open_interest_all": oi,
            "noncomm_positions_long_all": long, "noncomm_positions_short_all": short,
            "noncomm_postions_spread_all": "0", "comm_positions_long_all": "1", "comm_positions_short_all": "2",
            "nonrept_positions_long_all": "3", "nonrept_positions_short_all": "4"}


class TestDisaggregated(unittest.TestCase):
    def test_managed_money_joins_on_report_date_and_is_empty_before_2006(self):
        legacy = cot.parse([legacy_row("2005-06-07", "100", "50", "1000"),
                            legacy_row("2026-09-29", "361351", "251888", "1878576")])
        disagg = cot.parse_disagg([{"report_date_as_yyyy_mm_dd": "2026-09-29T00:00:00.000",
                                    "m_money_positions_long_all": "209028", "m_money_positions_short_all": "129436",
                                    "prod_merc_positions_long": "615887", "prod_merc_positions_short": "296348",
                                    "swap_positions_long_all": "113558", "swap__positions_short_all": "575715"}])
        out = cot.combine(legacy, disagg).set_index("report_date")
        self.assertTrue(pd.isna(out.loc[D(2005, 6, 7), "mm_net"]))
        self.assertEqual(out.loc[D(2026, 9, 29), "mm_net"], 209028 - 129436)
        self.assertAlmostEqual(out.loc[D(2026, 9, 29), "mm_net_pct_oi"], 79592 / 1878576)
        con = db.connect(":memory:")
        cot.store(con, out.reset_index())
        self.assertEqual(con.execute("SELECT count(*), count(mm_net) FROM trader_positioning").fetchone(), (2, 1))


class TestSourceRegistry(unittest.TestCase):
    def test_every_dataset_is_documented_in_sources_md(self):
        text = (ROOT / "docs" / "SOURCES.md").read_text()
        for d in sources.DATASETS:
            self.assertIn(d["url"].rstrip("/"), text, d["source_id"])

    def test_flags_match_the_code(self):
        flags = {d["source_id"]: d["publishable"] for d in sources.DATASETS}
        self.assertTrue(flags["ds-fred-dtwexbgs"])
        self.assertTrue(fred.INDICATORS["USD_BROAD"]["publishable"])
        for restricted in ["ds-fred-ovxcls", "ds-fred-nasdaqcom", "ds-fred-hy", "ds-polymarket", "ds-kalshi"]:
            self.assertFalse(flags[restricted], restricted)

    def test_store_is_repeatable_and_keeps_citations_separate(self):
        con = db.connect(":memory:")
        sources.store(con)
        sources.store(con)
        self.assertEqual(con.execute("SELECT count(*) FROM source WHERE kind = 'dataset'").fetchone()[0], len(sources.DATASETS))
        self.assertEqual(con.execute("SELECT count(*) FROM source WHERE event_id IS NOT NULL").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
