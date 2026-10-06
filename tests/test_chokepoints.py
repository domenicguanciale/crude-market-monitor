import datetime as dt
import unittest

import chokepoints as cp
import db


class TestChokepoints(unittest.TestCase):
    def test_parse_and_store(self):
        con = db.connect(":memory:")
        cp.store_locations(con, [{"portid": "chokepoint6", "portname": "Strait of Hormuz",
                                  "lat": 26.2968, "lon": 56.8598}])
        rows = [{"date": "2026-09-27", "portid": "chokepoint6", "n_tanker": 1, "n_total": 1,
                 "capacity_tanker": 8866, "capacity": 8866},
                {"date": "2026-09-27", "portid": "chokepoint6", "n_tanker": 1, "n_total": 1,
                 "capacity_tanker": 8866, "capacity": 8866}]          # duplicate day dropped
        df = cp.parse_daily(rows)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0].facility_id, "strait-of-hormuz")
        cp.store_daily(con, df)
        cp.store_daily(con, df)                                     # re-run does not duplicate
        self.assertEqual(con.execute("SELECT count(*) FROM chokepoint_transit").fetchone()[0], 1)
        self.assertEqual(con.execute("SELECT type, latitude FROM facility").fetchone(),
                         ("tanker or shipping lane", 26.2968))

    def test_every_chokepoint_has_a_facility_id(self):
        self.assertIn("chokepoint6", cp.CHOKEPOINTS)
        self.assertEqual(len(set(cp.CHOKEPOINTS.values())), len(cp.CHOKEPOINTS))
        self.assertTrue(cp.PUBLISHABLE)


if __name__ == "__main__":
    unittest.main()
