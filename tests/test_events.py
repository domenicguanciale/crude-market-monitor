import datetime as dt
import unittest

import pandas as pd

import db
import events

D = dt.date


def starter():
    return pd.DataFrame([
        dict(event_id="E05", event_date="2019-09-14", first_trading_day_after="2019-09-16", event_name="Abqaiq",
             country="Saudi Arabia", facility_or_route="Abqaiq", facility_type="processing plant", cause="attack",
             physical_supply_lost="yes", capacity_offline_bpd="5700000", source_1_publisher="EIA",
             source_1_url="https://www.eia.gov/a", source_2_url="", hand_checked="correct"),
        dict(event_id="E16", event_date="2026-02-28", first_trading_day_after="2026-03-02", event_name="Start",
             country="Iran", facility_or_route="Strait of Hormuz", facility_type="tanker or shipping lane", cause="attack",
             physical_supply_lost="yes", capacity_offline_bpd="7500000", source_1_publisher="EIA",
             source_1_url="https://www.eia.gov/b", source_2_url="", hand_checked=""),
    ])


def war():
    return pd.DataFrame([dict(event_id="W01", event_date="2026-02-28", alt_date="", date_flag="", event_name="Start",
                              country="Iran", facility_or_route="Strait of Hormuz", facility_id="strait-of-hormuz",
                              facility_type="tanker or shipping lane", latitude="26.3", longitude="56.9", cause="attack",
                              product="both", physical_supply_lost="yes", capacity_offline_bpd="7500000",
                              capacity_note="", source_1_publisher="EIA", source_1_url="https://www.eia.gov/b",
                              source_2_publisher="AP", source_2_url="https://ap.example/c", starter_row="E16",
                              episode="iran_war_2026", hand_checked="", notes="")])


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.s, self.w = starter(), war()
        self.s = self.s[~self.s.event_id.isin(set(self.w.starter_row))]    # what load_tables does

    def test_superseded_starter_rows_are_not_loaded_twice(self):
        ev, _, _ = events.build_rows(self.s, self.w, [D(2026, 3, 2)])
        self.assertEqual(sorted(e["event_id"] for e in ev), ["E05", "W01"])

    def test_only_correct_or_corrected_count_as_checked(self):
        ev, _, _ = events.build_rows(self.s, self.w, [D(2026, 3, 2)])
        checked = {e["event_id"]: e["hand_checked"] for e in ev}
        self.assertEqual(checked, {"E05": True, "W01": False})
        with self.assertRaises(ValueError):
            events.is_checked("looks fine")

    def test_day_zero_is_next_trading_day(self):
        ev, _, _ = events.build_rows(self.s, self.w, [D(2026, 2, 27), D(2026, 3, 2)])
        w01 = next(e for e in ev if e["event_id"] == "W01")
        self.assertEqual(w01["day_zero"], D(2026, 3, 2))          # Saturday Feb 28 -> Monday Mar 2
        self.assertEqual(w01["episode"], "iran_war_2026")

    def test_store_replaces_csv_rows_but_keeps_reader_rows(self):
        con = db.connect(":memory:")
        con.execute("INSERT INTO disruption_event (event_id, event_name) VALUES ('R001', 'from the news reader')")
        ev, fac, src = events.build_rows(self.s, self.w, [D(2026, 3, 2)])
        events.store(con, ev, fac, src)
        events.store(con, ev, fac, src)                           # re-run: no duplicates
        ids = [r[0] for r in con.execute("SELECT event_id FROM disruption_event ORDER BY 1").fetchall()]
        self.assertEqual(ids, ["E05", "R001", "W01"])
        self.assertEqual(con.execute("SELECT count(*) FROM source").fetchone()[0], 3)
        self.assertEqual(con.execute("SELECT latitude FROM facility WHERE facility_id='strait-of-hormuz'").fetchone()[0], 26.3)

    def test_report_accuracy(self):
        text = events.report(self.s, self.w)
        self.assertIn("Hand-checked so far: 1 of 2", text)
        self.assertIn("1 of 1 correct as drafted (100%)", text)


if __name__ == "__main__":
    unittest.main()
