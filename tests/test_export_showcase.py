import unittest

import db
import export_showcase as ex


class TestShowcaseRules(unittest.TestCase):
    def test_restricted_series_are_never_on_the_page(self):
        self.assertTrue(all(v["publishable"] for v in ex.SERIES.values()))
        exported = {k.upper() for k in ex.SERIES}
        self.assertFalse(exported & ex.NEVER_EXPORT)

    def test_refuses_unpublishable_series(self):
        with self.assertRaises(RuntimeError):
            ex.check_publishable({"nasdaq": {"publishable": False}})

    def test_only_hand_checked_events_are_exported(self):
        con = db.connect(":memory:")
        con.execute("INSERT INTO facility (facility_id, name, latitude, longitude) VALUES ('hz', 'Strait of Hormuz', 26.3, 56.9)")
        con.execute("""INSERT INTO disruption_event (event_id, event_name, event_date, facility_id, hand_checked)
                       VALUES ('W01', 'checked', '2026-02-28', 'hz', TRUE), ('W02', 'unchecked', '2026-03-02', 'hz', FALSE)""")
        con.execute("INSERT INTO source (source_id, event_id, publisher, url) VALUES ('W01-S1', 'W01', 'EIA', 'https://www.eia.gov/x')")
        events, unchecked = ex.checked_events(con)
        self.assertEqual([e["id"] for e in events], ["W01"])
        self.assertEqual(unchecked, 1)
        self.assertEqual((events[0]["lat"], events[0]["source_url"]), (26.3, "https://www.eia.gov/x"))


if __name__ == "__main__":
    unittest.main()
