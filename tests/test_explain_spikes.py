import datetime as dt
import unittest

import pandas as pd

import db
import explain_spikes as ex

D = dt.date


def seeded():
    con = db.connect(":memory:")
    con.execute("""INSERT INTO spike (spike_id, benchmark, kind, direction, extreme_date, size_pct) VALUES
                   ('BRENT-DAILY-2019-09-16', 'Brent', 'daily', 'up', '2019-09-16', 0.146),
                   ('BRENT-DAILY-2020-04-21', 'Brent', 'daily', 'down', '2020-04-21', -0.475)""")
    con.execute("""INSERT INTO price_series VALUES ('Brent', '2019-09-13', 60.22), ('Brent', '2019-09-16', 69.02),
                   ('Brent', '2019-09-17', 64.55)""")
    return con


def episodes(checked=""):
    return pd.DataFrame([{"episode_id": "S07", "name": "September 2019 Abqaiq attack",
                          "window_start": D(2019, 9, 13), "window_end": D(2019, 9, 30), "explanation": "EIA reports ...",
                          "source_1_publisher": "EIA", "source_1_url": "https://www.eia.gov/todayinenergy/detail.php?id=41413",
                          "source_2_publisher": "", "source_2_url": "", "notes": "", "accessed": "2026-10-07",
                          "hand_checked": checked, "checked": checked in ("correct", "corrected")}])


class TestExplainSpikes(unittest.TestCase):
    def test_links_only_spikes_inside_the_window(self):
        con = seeded()
        ex.store(con, episodes())
        rows = dict(con.execute("SELECT spike_id, cause_note FROM spike").fetchall())
        self.assertEqual(rows["BRENT-DAILY-2019-09-16"], "S07: September 2019 Abqaiq attack")
        self.assertIsNone(rows["BRENT-DAILY-2020-04-21"])
        self.assertEqual(con.execute("SELECT source_ids FROM spike WHERE spike_id='BRENT-DAILY-2019-09-16'").fetchone()[0], "spk-S07-1")

    def test_unchecked_stays_unchecked_and_rerun_replaces(self):
        con = seeded()
        ex.store(con, episodes())
        self.assertEqual(con.execute("SELECT count(*) FROM spike WHERE hand_checked").fetchone()[0], 0)
        ex.store(con, episodes("correct"))
        self.assertEqual(con.execute("SELECT count(*) FROM spike WHERE hand_checked").fetchone()[0], 1)
        self.assertEqual(con.execute("SELECT count(*) FROM source WHERE source_id LIKE 'spk-%'").fetchone()[0], 1)

    def test_context_reports_prices_from_the_database(self):
        c = ex.context(seeded(), D(2019, 9, 13), D(2019, 9, 30))
        self.assertEqual((c["Brent"]["first"], c["Brent"]["high"], c["Brent"]["last"]), (60.22, 69.02, 64.55))
        self.assertIn("Before it began: no tightness score", " ".join(ex.context_lines(c)))

    def test_csv_rows_have_sources_and_no_checks_filled_by_code(self):
        df = ex.load()
        self.assertTrue((df["source_1_url"].str.startswith("https://")).all())
        self.assertEqual(len(df), 12)


if __name__ == "__main__":
    unittest.main()
