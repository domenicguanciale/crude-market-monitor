"""Unusual prediction market activity and how often it came shortly before events. Item 4.

Run after fetch_markets.py: .venv/bin/python unusual_activity.py
Reads the database, changes nothing. Reports aggregate counts and rates only; no account is
identified, named or accused. Only hand-checked events are used.
"""

import datetime as dt

import pandas as pd

import activity
import db

WAR_EPISODE = "iran_war_2026"


def all_flags(con):
    markets = con.execute("SELECT market_key, platform, topic, closes FROM prediction_market").df()
    readings = con.execute(
        "SELECT market_key, reading_date, price, volume, total_volume FROM market_reading").df()
    readings["reading_date"] = pd.to_datetime(readings["reading_date"]).dt.date
    parts = []
    by_market = dict(tuple(readings.groupby("market_key")))
    for m in markets.itertuples():
        r = by_market.get(m.market_key)
        if r is None:
            continue
        closes = m.closes.date() if hasattr(m.closes, "date") else m.closes
        f = activity.flag_market(r, closes)
        if not f.empty:
            parts.append(f.assign(market_key=m.market_key, platform=m.platform, topic=m.topic))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def checked_events(con):
    return con.execute(
        "SELECT event_id, event_date, episode FROM disruption_event "
        "WHERE hand_checked AND event_date IS NOT NULL").df()


def main():
    con = db.connect()
    flags = all_flags(con)
    if flags.empty:
        print("No market readings with enough history yet. Run fetch_markets.py first.")
        return

    print("Market-days evaluated and flagged (aggregate):")
    summary = flags.groupby(["platform", "topic"]).agg(
        market_days=("reading_date", "size"),
        odds_flags=("odds_flag", "sum"),
        volume_days=("volume", lambda v: v.notna().sum()),
        volume_flags=("volume_flag", "sum"))
    print(summary.to_string())

    days = activity.topic_days(flags)
    for topic, t in days.groupby("topic"):
        u = t[t["unusual"]].sort_values("share", ascending=False)
        print(f"\n{topic}: {len(t)} days with at least {activity.MIN_ACTIVE_MARKETS} active markets, "
              f"{len(u)} unusual (share flagged >= {t['share'].quantile(activity.UNUSUAL_QUANTILE):.1%}), "
              f"{t['reading_date'].min()} to {t['reading_date'].max()}")
        print("  Most unusual days: " + ", ".join(
            f"{r.reading_date} ({r.flagged}/{r.active})" for r in u.head(10).itertuples()))

    events = checked_events(con)
    print(f"\nHand-checked events available: {len(events)}")
    if events.empty:
        print("No event comparison yet: nothing downstream may use unchecked events. "
              "It runs automatically once events are marked hand-checked.")
        return
    events["event_date"] = pd.to_datetime(events["event_date"]).dt.date
    samples = {
        "all checked events": events,
        "without the 2026 war episode": events[events["episode"] != WAR_EPISODE],
        "2026 war episode only": events[events["episode"] == WAR_EPISODE],
    }
    print(f"Window: unusual day from {activity.WINDOW[0]} to {activity.WINDOW[1]} days before the event date")
    for name, ev in samples.items():
        for topic in sorted(days["topic"].unique()):
            r = activity.event_comparison(days, list(ev["event_date"]), topic)
            rate = "n/a" if r["rate"] is None else f"{r['rate']:.0%}"
            base = "n/a" if r["base_rate"] is None else f"{r['base_rate']:.0%}"
            print(f"  {name:<30} {topic:<14} {r['preceded']} of {r['events']} events ({rate}); "
                  f"base rate for any day {base}")


if __name__ == "__main__":
    main()
