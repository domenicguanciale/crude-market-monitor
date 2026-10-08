import unittest

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


if __name__ == "__main__":
    unittest.main()
