import datetime as dt
import json
import unittest

import db
import news_reader as nr

D = dt.date


def fake_extraction(**over):
    base = dict(is_supply_event=True, event_name="Saudi Arabia cuts output by 20 percent", event_date="2026-03-13",
                event_date_note="Stated in the first paragraph.", country="Saudi Arabia",
                facility_or_route="Saudi Aramco fields", facility_type="field", cause="other", product="crude",
                physical_supply_lost="yes", capacity_offline_bpd=2_000_000,
                capacity_note="Crude production cut, as reported.",
                evidence=[nr.Evidence(field="capacity_offline_bpd", quote="cut output by about 2 million barrels a day")],
                uncertainties=[])
    base.update(over)
    return nr.Extraction(**base)


def extractor_returning(x):
    return lambda text: (x, "claude-opus-5-5")


class TestStaging(unittest.TestCase):
    def setUp(self):
        self.con = db.connect(":memory:")

    def stage(self, x=None):
        return nr.stage(self.con, "Article text.", "https://example.org/a", "EIA", "2026-03-14",
                        extractor=extractor_returning(x or fake_extraction()))

    def test_stage_writes_only_to_staging(self):
        sid = self.stage()
        row = nr.get(self.con, sid)
        self.assertEqual((row["status"], row["event_date"], row["capacity_offline_bpd"]),
                         ("pending", D(2026, 3, 13), 2_000_000))
        self.assertEqual(self.con.execute("SELECT count(*) FROM disruption_event").fetchone()[0], 0)

    def test_long_quotes_are_cut_to_25_words(self):
        long_quote = " ".join(f"w{i}" for i in range(60))
        sid = self.stage(fake_extraction(evidence=[nr.Evidence(field="x", quote=long_quote)]))
        quote = json.loads(nr.get(self.con, sid)["evidence"])[0]["quote"]
        self.assertEqual(len(quote.replace(" ...", "").split()), 25)

    def test_invalid_model_date_is_dropped_not_stored(self):
        sid = self.stage(fake_extraction(event_date="March 13"))
        row = nr.get(self.con, sid)
        self.assertIsNone(row["event_date"])
        self.assertIn("invalid date", row["event_date_note"])

    def test_refusal_stages_nothing(self):
        def refusing(text):
            raise RuntimeError("The model declined to process this article. Nothing was staged.")
        with self.assertRaises(RuntimeError):
            nr.stage(self.con, "text", "u", "p", extractor=refusing)
        self.assertEqual(self.con.execute("SELECT count(*) FROM staged_event").fetchone()[0], 0)

    def test_edit_validates(self):
        sid = self.stage()
        nr.edit(self.con, sid, "capacity_offline_bpd", "1500000")
        self.assertEqual(nr.get(self.con, sid)["capacity_offline_bpd"], 1_500_000)
        with self.assertRaises(Exception):
            nr.edit(self.con, sid, "cause", "sabotage by villains")     # not in the vocabulary
        with self.assertRaises(ValueError):
            nr.edit(self.con, sid, "status", "approved")                # not editable


class TestNoKeyPath(unittest.TestCase):
    def test_stage_from_session_json(self):
        import os, tempfile
        x = fake_extraction()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(x.model_dump_json())
        try:
            con = db.connect(":memory:")
            sid = nr.stage(con, "", "https://example.org/a", "EIA", extractor=nr.from_json_file(f.name))
            row = nr.get(con, sid)
            self.assertEqual((row["model"], row["capacity_offline_bpd"]), ("claude-code-session", 2_000_000))
        finally:
            os.unlink(f.name)

    def test_session_json_must_fit_the_schema(self):
        import os, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"event_name": "x", "cause": "not a cause"}, f)
        try:
            with self.assertRaises(Exception):
                nr.stage(db.connect(":memory:"), "", "u", "p", extractor=nr.from_json_file(f.name))
        finally:
            os.unlink(f.name)


class TestApproval(unittest.TestCase):
    def setUp(self):
        self.con = db.connect(":memory:")
        self.sid = nr.stage(self.con, "Article text.", "https://example.org/a", "EIA", "2026-03-14",
                            extractor=extractor_returning(fake_extraction()))

    def test_nothing_written_without_yes(self):
        result = nr.approve(self.con, self.sid, confirm=lambda *a: False)
        self.assertIsNone(result)
        self.assertEqual(self.con.execute("SELECT count(*) FROM disruption_event").fetchone()[0], 0)
        self.assertEqual(nr.get(self.con, self.sid)["status"], "pending")

    def test_yes_writes_event_facility_and_source_unchecked_by_default(self):
        event_id = nr.approve(self.con, self.sid, confirm=lambda *a: True, episode="iran_war_2026")
        self.assertEqual(event_id, "R001")
        ev = self.con.execute("SELECT event_date, bpd_offline, physical_loss, hand_checked, episode, week_ending, "
                              "facility_id FROM disruption_event").fetchone()
        self.assertEqual(ev, (D(2026, 3, 13), 2_000_000, True, False, "iran_war_2026", D(2026, 3, 13),
                              "saudi-aramco-fields"))
        self.assertEqual(self.con.execute("SELECT url, publisher FROM source").fetchone(),
                         ("https://example.org/a", "EIA"))
        self.assertEqual(nr.get(self.con, self.sid)["status"], "approved")
        # The user can mark it checked later; the parent row can be updated with a source pointing at it
        self.con.execute("UPDATE disruption_event SET hand_checked = TRUE WHERE event_id = 'R001'")

    def test_checked_flag_and_no_double_approval(self):
        nr.approve(self.con, self.sid, confirm=lambda *a: True, event_id="E22", checked=True)
        self.assertTrue(self.con.execute("SELECT hand_checked FROM disruption_event").fetchone()[0])
        with self.assertRaises(ValueError):
            nr.approve(self.con, self.sid, confirm=lambda *a: True)

    def test_row_without_date_cannot_be_approved(self):
        sid = nr.stage(self.con, "t", "u", "p", extractor=extractor_returning(fake_extraction(event_date=None)))
        with self.assertRaises(ValueError):
            nr.approve(self.con, sid, confirm=lambda *a: True)


if __name__ == "__main__":
    unittest.main()
