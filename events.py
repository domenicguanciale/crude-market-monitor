"""Load the event tables into DuckDB and report hand-checking progress. Expansion item 11.

Run: .venv/bin/python events.py            load both CSVs, then print the checking report
     .venv/bin/python events.py --report   print the report only

Sources of truth (edit these, then re-run):
  EVENTS_STARTER.csv        21 starter rows (E01 to E21)
  data/iran_war_2026.csv    the 2026 Iran war as one episode (W01 to W14), from the starter rows
                            E16 to E21 and the leads in EVENTS_NOTES.md, each with news or official sources

How to hand-check: open each row's source links and fill the hand_checked column with
  correct            the row matched its sources as drafted
  corrected          you fixed something; edit the row, then mark it corrected
  could not confirm  the sources do not support it
Only 'correct' and 'corrected' rows count as hand-checked. Every other row stays unchecked and
nothing downstream (unusual activity, the event study, the showcase) may use it.

Rows E16 to E21 are superseded by the W rows that cite them (starter_row), so the war is not
counted twice. Rows added by news_reader.py (R001, ...) are left alone.
"""

import argparse
import datetime as dt
import re
from pathlib import Path

import pandas as pd

import db
from score import week_ending_of

HERE = Path(__file__).parent
STARTER = HERE / "EVENTS_STARTER.csv"
WAR = HERE / "data" / "iran_war_2026.csv"
CHECKED = {"correct", "corrected"}
CHECK_VALUES = CHECKED | {"could not confirm", ""}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def text(value):
    return "" if pd.isna(value) else str(value).strip()


def as_date(value):
    v = text(value)
    return dt.date.fromisoformat(v) if v else None


def is_checked(value):
    v = text(value).lower()
    if v not in CHECK_VALUES:
        raise ValueError(f"hand_checked must be one of {sorted(CHECK_VALUES - {''})} or blank, not '{value}'")
    return v in CHECKED


def first_trading_day_on_or_after(day, trading_days):
    """Day zero for an event: the first Brent trading day on or after the event date."""
    if day is None:
        return None
    later = [d for d in trading_days if d >= day]
    return later[0] if later else None


def load_tables(starter_path=STARTER, war_path=WAR):
    starter = pd.read_csv(starter_path, dtype=str)
    war = pd.read_csv(war_path, dtype=str)
    for df in (starter, war):
        if "hand_checked" not in df:
            df["hand_checked"] = ""
    superseded = set(war["starter_row"].dropna()) - {""}
    return starter[~starter["event_id"].isin(superseded)], war


def build_rows(starter, war, trading_days):
    """Both tables -> (events, facilities, sources) lists of dicts, ready to insert."""
    events, facilities, sources = [], {}, []

    for r in starter.itertuples():
        event_date = as_date(r.event_date)
        facility_id = slug(r.facility_or_route) if text(r.facility_or_route) else None
        if facility_id:
            facilities.setdefault(facility_id, dict(facility_id=facility_id, name=text(r.facility_or_route),
                                                    type=text(r.facility_type), country=text(r.country),
                                                    latitude=None, longitude=None))
        events.append(dict(event_id=r.event_id, event_name=text(r.event_name), event_date=event_date,
                           day_zero=as_date(r.first_trading_day_after), cause=text(r.cause),
                           bpd_offline=float(r.capacity_offline_bpd) if text(r.capacity_offline_bpd) else None,
                           physical_loss={"yes": True, "no": False}.get(text(r.physical_supply_lost).lower()),
                           facility_id=facility_id, week_ending=week_ending_of(event_date) if event_date else None,
                           hand_checked=is_checked(r.hand_checked), episode=None))
        for i, (pub, url) in enumerate([(r.source_1_publisher, r.source_1_url), ("", r.source_2_url)], start=1):
            if text(url):
                sources.append(dict(source_id=f"{r.event_id}-S{i}", event_id=r.event_id, publisher=text(pub) or None,
                                    url=text(url), published_date=None))

    for r in war.itertuples():
        event_date = as_date(r.event_date)
        facilities.setdefault(r.facility_id, dict(facility_id=r.facility_id, name=text(r.facility_or_route),
                                                  type=text(r.facility_type), country=text(r.country),
                                                  latitude=float(r.latitude), longitude=float(r.longitude)))
        events.append(dict(event_id=r.event_id, event_name=text(r.event_name), event_date=event_date,
                           day_zero=first_trading_day_on_or_after(event_date, trading_days), cause=text(r.cause),
                           bpd_offline=float(r.capacity_offline_bpd) if text(r.capacity_offline_bpd) else None,
                           physical_loss={"yes": True, "no": False}.get(text(r.physical_supply_lost).lower()),
                           facility_id=r.facility_id, week_ending=week_ending_of(event_date),
                           hand_checked=is_checked(r.hand_checked), episode=text(r.episode) or None))
        for i, (pub, url) in enumerate([(r.source_1_publisher, r.source_1_url),
                                        (r.source_2_publisher, r.source_2_url)], start=1):
            if text(url):
                sources.append(dict(source_id=f"{r.event_id}-S{i}", event_id=r.event_id, publisher=text(pub) or None,
                                    url=text(url), published_date=None))
    return events, list(facilities.values()), sources


def store(con, events, facilities, sources):
    """Replace the E and W rows (the CSVs are the source of truth). Reader rows (R...) are untouched.

    DuckDB checks foreign keys against committed data, so the old sources must be deleted (and
    committed) before the events they point to; the new rows then go in as one transaction.
    """
    con.execute("DELETE FROM source WHERE event_id LIKE 'E%' OR event_id LIKE 'W%'")
    con.execute("DELETE FROM disruption_event WHERE event_id LIKE 'E%' OR event_id LIKE 'W%'")
    con.execute("BEGIN TRANSACTION")
    for f in facilities:
        con.execute("""INSERT INTO facility (facility_id, name, type, country, latitude, longitude)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT (facility_id) DO UPDATE SET
                           latitude = COALESCE(EXCLUDED.latitude, latitude),
                           longitude = COALESCE(EXCLUDED.longitude, longitude)""",
                    [f["facility_id"], f["name"], f["type"] or None, f["country"] or None, f["latitude"], f["longitude"]])
    if events:
        ev = pd.DataFrame(events)
        con.execute("""INSERT INTO disruption_event (event_id, event_name, event_date, day_zero, cause, bpd_offline,
                           physical_loss, facility_id, week_ending, hand_checked, episode)
                       SELECT event_id, event_name, event_date, day_zero, cause, bpd_offline, physical_loss,
                              facility_id, week_ending, hand_checked, episode FROM ev""")
    if sources:
        src = pd.DataFrame(sources)
        con.execute("INSERT INTO source SELECT source_id, event_id, publisher, url, published_date FROM src")
    con.execute("COMMIT")


def report(starter, war):
    """How many rows are checked, and the accuracy rate of the AI-drafted rows (EVENTS_NOTES.md)."""
    rows = pd.concat([starter.assign(table="starter"), war.assign(table="war")], ignore_index=True)
    status = rows["hand_checked"].fillna("").str.strip().str.lower()
    done = status.isin(["correct", "corrected", "could not confirm"])
    lines = [f"Event rows loaded: {len(rows)} ({len(starter)} starter, {len(war)} war)",
             f"Hand-checked so far: {int(done.sum())} of {len(rows)}"]
    if done.any():
        right = int((status == "correct").sum())
        lines.append(f"Accuracy of the drafted rows: {right} of {int(done.sum())} correct as drafted "
                     f"({right / done.sum():.0%}); {int((status == 'corrected').sum())} corrected, "
                     f"{int((status == 'could not confirm').sum())} could not be confirmed")
    else:
        lines.append("No rows checked yet. Open each row's sources and fill hand_checked "
                     "(correct / corrected / could not confirm).")
    flagged = war[war["date_flag"].fillna("") != ""]
    lines.append(f"War rows with conflicting dates or prices to resolve: {', '.join(flagged.event_id)}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--report", action="store_true", help="print the checking report without loading")
    args = p.parse_args(argv)
    starter, war = load_tables()
    if not args.report:
        con = db.connect()
        trading_days = [r[0] for r in con.execute(
            "SELECT price_date FROM price_series WHERE benchmark = 'Brent' ORDER BY price_date").fetchall()]
        events, facilities, sources = build_rows(starter, war, trading_days)
        store(con, events, facilities, sources)
        checked = sum(e["hand_checked"] for e in events)
        print(f"Loaded {len(events)} events ({checked} hand-checked), {len(facilities)} facilities, "
              f"{len(sources)} sources.")
    print(report(starter, war))


if __name__ == "__main__":
    main()
