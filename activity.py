"""Unusual prediction market activity (expansion item 4). Aggregate counts and rates only.

All rules below were fixed before looking at any results.

1. Market-day flag. Compared with the market's own previous 30 days (at least 14 days needed):
     odds:   |price change| >= max(0.10, 4 x median daily |price change|)
     volume: volume >= max(1,000, 5 x median daily volume)
   The last 2 days before a market closes are skipped: odds jump to 0 or 1 as a question resolves.
2. Unusual topic-day. On days with at least 20 active markets in a topic, the share of them flagged.
   A day is unusual if that share is in the top 5% of days for the topic.
3. Event comparison, hand-checked events only. Was there an unusual day in the window from 4 to 2
   days before the event date? Day -1 is skipped because Gulf time runs 7 to 8 hours ahead of
   New York, so a reaction can land on New York's day -1. Compared with the base rate for any day.

Dates are US Eastern days throughout, matching market_reading.
This is market monitoring and research. It does not identify, name or accuse any account.
"""

import datetime as dt

import pandas as pd

BASELINE_DAYS = 30
MIN_BASELINE = 14
ODDS_FLOOR, ODDS_MULTIPLE = 0.10, 4
VOLUME_FLOOR, VOLUME_MULTIPLE = 1_000, 5
SKIP_BEFORE_CLOSE_DAYS = 2
MAX_GAP_DAYS = 3          # a price change is only measured against a price at most 3 days older
MIN_ACTIVE_MARKETS = 20
UNUSUAL_QUANTILE = 0.95
WINDOW = (4, 2)           # days before the event: from day -4 to day -2


def daily_volume_from_totals(readings):
    """Polymarket: volume on day D = all-time total on D minus the total on D-1 (consecutive days only)."""
    r = readings.dropna(subset=["total_volume"]).sort_values("reading_date")
    prev_day = r["reading_date"].shift()
    diff = r["total_volume"].diff()
    consecutive = (pd.to_datetime(r["reading_date"]) - pd.to_datetime(prev_day)).dt.days == 1
    return pd.Series(diff.where(consecutive).clip(lower=0).values, index=r["reading_date"].values).dropna()


def flag_market(readings, closes):
    """One market's readings -> one row per evaluable day: odds_move, volume, odds_flag, volume_flag.

    readings has reading_date, price, volume, total_volume. closes is the market's close date.
    """
    r = readings.sort_values("reading_date").copy()
    r["reading_date"] = pd.to_datetime(r["reading_date"])
    if closes is not None:
        r = r[r["reading_date"] < pd.Timestamp(closes) - pd.Timedelta(days=SKIP_BEFORE_CLOSE_DAYS)]

    # Daily odds move, against the previous price no more than MAX_GAP_DAYS earlier
    priced = r.dropna(subset=["price"])
    gap = priced["reading_date"].diff().dt.days
    move = priced["price"].diff().abs().where(gap <= MAX_GAP_DAYS)
    odds = pd.Series(move.values, index=priced["reading_date"].values)

    # Daily volume: Kalshi publishes it; Polymarket's comes from consecutive all-time totals
    vol = pd.Series(r["volume"].values, index=r["reading_date"].values).dropna()
    if vol.empty:
        totals = r.assign(reading_date=r["reading_date"].dt.date)
        vol = daily_volume_from_totals(totals)
        vol.index = pd.to_datetime(vol.index)

    out = []
    for day in sorted(set(odds.dropna().index) | set(vol.index)):
        window_start = day - pd.Timedelta(days=BASELINE_DAYS)
        o_base = odds[(odds.index >= window_start) & (odds.index < day)].dropna()
        v_base = vol[(vol.index >= window_start) & (vol.index < day)]
        o, v = odds.get(day), vol.get(day)
        odds_ok = len(o_base) >= MIN_BASELINE and pd.notna(o)
        vol_ok = len(v_base) >= MIN_BASELINE and pd.notna(v)
        if not (odds_ok or vol_ok):
            continue
        out.append({
            "reading_date": day.date(),
            "odds_move": o if odds_ok else None,
            "volume": v if vol_ok else None,
            "odds_flag": bool(odds_ok and o >= max(ODDS_FLOOR, ODDS_MULTIPLE * o_base.median())),
            "volume_flag": bool(vol_ok and v >= max(VOLUME_FLOOR, VOLUME_MULTIPLE * v_base.median())),
        })
    return pd.DataFrame(out, columns=["reading_date", "odds_move", "volume", "odds_flag", "volume_flag"])


def topic_days(flags):
    """Market-day flags (with topic) -> one row per topic and day: active, flagged, share, unusual."""
    f = flags.assign(flagged=flags["odds_flag"] | flags["volume_flag"])
    days = (f.groupby(["topic", "reading_date"])
             .agg(active=("market_key", "nunique"), flagged=("flagged", "sum")).reset_index())
    days = days[days["active"] >= MIN_ACTIVE_MARKETS].copy()
    days["share"] = days["flagged"] / days["active"]
    cutoff = days.groupby("topic")["share"].transform(lambda s: s.quantile(UNUSUAL_QUANTILE))
    days["unusual"] = (days["share"] >= cutoff) & (days["flagged"] > 0)
    return days


def window_has_unusual(day, unusual_dates, window=WINDOW):
    """True if any unusual date falls from window[0] to window[1] days before `day`."""
    far, near = window
    return any(day - dt.timedelta(days=k) in unusual_dates for k in range(near, far + 1))


def event_comparison(days, events, topic):
    """Share of hand-checked events with an unusual day 4 to 2 days before, against the base rate.

    days: output of topic_days. events: event_id, event_date, episode (only hand-checked rows).
    Only events whose whole window is covered by the study period count.
    """
    t = days[days["topic"] == topic]
    if t.empty:
        return {"topic": topic, "events": 0, "preceded": 0, "rate": None, "base_rate": None, "days": 0}
    covered = set(t["reading_date"])
    unusual = set(t.loc[t["unusual"], "reading_date"])
    first, last = min(covered), max(covered)

    def in_study(d):
        return first + dt.timedelta(days=WINDOW[0]) <= d <= last

    study_days = [d for d in sorted(covered) if in_study(d)]
    base = sum(window_has_unusual(d, unusual) for d in study_days)
    evs = [e for e in events if in_study(e)]
    hit = sum(window_has_unusual(e, unusual) for e in evs)
    return {"topic": topic, "events": len(evs), "preceded": hit,
            "rate": hit / len(evs) if evs else None,
            "base_rate": base / len(study_days) if study_days else None,
            "days": len(study_days)}
