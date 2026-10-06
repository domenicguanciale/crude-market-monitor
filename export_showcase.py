"""Write docs/data/showcase.json for the public showcase page (docs/index.html). Expansion item 12.

Run after the data scripts: .venv/bin/python export_showcase.py
The page is static (GitHub Pages): no server, no keys. It reads only this JSON file.

Rules enforced here:
- Only publishable series leave this machine. EIA, CFTC and Federal Reserve data are public domain;
  IMF PortWatch and the GPR index allow publishing with credit. NASDAQ (Nasdaq), the high-yield
  spread (ICE), OVX (CBOE) and prediction market data are never exported.
- Only hand-checked events are exported.
"""

import datetime as dt
import json
from pathlib import Path

import pandas as pd

import backtest
import chokepoints
import compare_2020
import db
import fred
import gpr
import seasonal

OUT = Path(__file__).parent / "docs" / "data" / "showcase.json"
START = dt.date(2025, 7, 1)              # context before the war; the replay defaults to Feb 2026
REPLAY_START = dt.date(2026, 2, 1)
REPO = "https://github.com/domenicguanciale/crude-market-monitor"

# Every daily series on the page, with where it comes from and whether it may be published
SERIES = {
    "brent":   {"label": "Brent", "unit": "$/bbl", "credit": "EIA", "publishable": True},
    "wti":     {"label": "WTI", "unit": "$/bbl", "credit": "EIA", "publishable": True},
    "spread":  {"label": "Brent minus WTI", "unit": "$/bbl", "credit": "EIA", "publishable": True},
    "ust10y":  {"label": "10-year Treasury yield", "unit": "%", "credit": "Federal Reserve via FRED",
                "publishable": fred.INDICATORS["UST10Y"]["publishable"]},
    "hormuz":  {"label": "Hormuz tanker transits, 7-day average", "unit": "ships/day", "credit": "IMF PortWatch",
                "publishable": chokepoints.PUBLISHABLE},
    "gpr":     {"label": "Geopolitical Risk Index, 7-day average", "unit": "1985-2019 = 100",
                "credit": "Caldara and Iacoviello (CC BY)", "publishable": gpr.PUBLISHABLE},
}
NEVER_EXPORT = {"NASDAQ", "HY_SPREAD", "OVX"}


def check_publishable(series):
    blocked = [k for k, v in series.items() if not v["publishable"]]
    if blocked:
        raise RuntimeError(f"Refusing to export series not cleared for publishing: {blocked}")


def to_points(df, date_col, value_col, digits=2):
    df = df.dropna(subset=[value_col]).sort_values(date_col)
    return [[d.isoformat(), round(float(v), digits)] for d, v in zip(df[date_col], df[value_col])]


def daily_series(con):
    px = con.execute("""PIVOT (SELECT price_date, benchmark, price FROM price_series
                               WHERE benchmark IN ('Brent', 'WTI') AND price_date >= ?)
                        ON benchmark IN ('Brent', 'WTI') USING first(price) ORDER BY price_date""", [START]).df()
    px["price_date"] = pd.to_datetime(px["price_date"]).dt.date
    px["spread"] = px["Brent"] - px["WTI"]
    ind = con.execute("SELECT indicator, obs_date, value FROM daily_indicator WHERE indicator IN ('UST10Y', 'GPR') "
                      "AND obs_date >= ? ORDER BY obs_date", [START - dt.timedelta(days=7)]).df()
    ind["obs_date"] = pd.to_datetime(ind["obs_date"]).dt.date
    ust = ind[ind.indicator == "UST10Y"]
    g = ind[ind.indicator == "GPR"].copy()
    g["avg7"] = g["value"].rolling(7).mean()
    h = con.execute("SELECT transit_date, tankers FROM chokepoint_transit WHERE facility_id = 'strait-of-hormuz' "
                    "AND transit_date >= ? ORDER BY transit_date", [START - dt.timedelta(days=7)]).df()
    h["transit_date"] = pd.to_datetime(h["transit_date"]).dt.date
    h["avg7"] = h["tankers"].astype(float).rolling(7).mean()
    keep = lambda df, col: df[df[col] >= START]
    return {
        "brent": to_points(px, "price_date", "Brent"),
        "wti": to_points(px, "price_date", "WTI"),
        "spread": to_points(px, "price_date", "spread"),
        "ust10y": to_points(keep(ust, "obs_date"), "obs_date", "value"),
        "hormuz": to_points(keep(h, "transit_date"), "transit_date", "avg7", 1),
        "gpr": to_points(keep(g, "obs_date"), "obs_date", "avg7", 0),
    }


def headline(con):
    w = con.execute("""SELECT week_ending, tightness_score, tightness_label, crude_position, distillate_position,
                              utilization_position, spread
                       FROM weekly_reading WHERE tightness_score IS NOT NULL ORDER BY week_ending DESC LIMIT 1""").df().iloc[0]
    return {"week_ending": pd.Timestamp(w.week_ending).date().isoformat(), "score": int(w.tightness_score), "label": w.tightness_label,
            "crude_position": round(float(w.crude_position), 2),
            "distillate_position": round(float(w.distillate_position), 2),
            "utilization_position": round(float(w.utilization_position), 2),
            "spread": round(float(w.spread), 2)}


def score_toggle(con):
    """Tight/normal/loose weeks per year, with 2020 in the five-year range and with it left out (default)."""
    weekly = con.execute("SELECT * FROM weekly_reading ORDER BY week_ending").df()
    out = {}
    for name, exclude in [("with_2020", ()), ("without_2020", seasonal.ABNORMAL_YEARS)]:
        counts = compare_2020.yearly_counts(compare_2020.scores(weekly, exclude)).loc[2015:]
        out[name] = {str(y): {k: int(v) for k, v in row.items()} for y, row in counts.iterrows()}
    return out


def backtest_summary():
    weekly, series = backtest.load()
    out = {}
    for bench in ["WTI", "Brent"]:
        s = backtest.summarize(backtest.forward_returns(weekly, series[bench]))
        out[bench] = {g: {"count": int(r["count"]), "average": round(float(r["average"]), 4),
                          "hit_rate": round(float(r["hit_rate"]), 3)} for g, r in s.iterrows()}
    return out


def checked_events(con):
    df = con.execute("""SELECT e.event_id, e.event_name, e.event_date, e.day_zero, e.cause, e.bpd_offline,
                               e.episode, f.name AS place, f.latitude, f.longitude,
                               (SELECT url FROM source s WHERE s.event_id = e.event_id ORDER BY source_id LIMIT 1) AS source_url,
                               (SELECT publisher FROM source s WHERE s.event_id = e.event_id ORDER BY source_id LIMIT 1) AS source_name
                        FROM disruption_event e LEFT JOIN facility f USING (facility_id)
                        WHERE e.hand_checked AND e.event_date IS NOT NULL ORDER BY e.event_date""").df()
    events = []
    for r in df.itertuples():
        events.append({"id": r.event_id, "name": r.event_name, "date": pd.Timestamp(r.event_date).date().isoformat(),
                       "day_zero": pd.Timestamp(r.day_zero).date().isoformat() if pd.notna(r.day_zero) else None,
                       "cause": r.cause, "bpd_offline": None if pd.isna(r.bpd_offline) else int(r.bpd_offline),
                       "episode": r.episode, "place": r.place,
                       "lat": None if pd.isna(r.latitude) else float(r.latitude),
                       "lon": None if pd.isna(r.longitude) else float(r.longitude),
                       "source_url": r.source_url, "source_name": r.source_name})
    unchecked = con.execute("SELECT count(*) FROM disruption_event WHERE NOT hand_checked").fetchone()[0]
    return events, unchecked


def chokepoint_points(con):
    rows = con.execute("SELECT facility_id, name, latitude, longitude FROM facility "
                       "WHERE type = 'tanker or shipping lane' AND latitude IS NOT NULL ORDER BY name").fetchall()
    return [{"id": i, "name": n, "lat": la, "lon": lo} for i, n, la, lo in rows]


def build(con):
    check_publishable(SERIES)
    events, unchecked = checked_events(con)
    return {
        "generated": dt.date.today().isoformat(),
        "repo": REPO,
        "replay_start": REPLAY_START.isoformat(),
        "series_meta": SERIES,
        "series": daily_series(con),
        "headline": headline(con),
        "score_toggle": score_toggle(con),
        "backtest": backtest_summary(),
        "events": events,
        "unchecked_events": int(unchecked),
        "chokepoints": chokepoint_points(con),
        "omitted": "The NASDAQ Composite and the ICE BofA high-yield spread are part of the research but their owners "
                   "do not permit republishing; they are charted in the local app only.",
    }


def main():
    con = db.connect()
    data = build(con)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    sizes = {k: len(v) for k, v in data["series"].items()}
    print(f"Wrote {OUT.relative_to(Path(__file__).parent)} ({OUT.stat().st_size / 1024:.0f} KB): {sizes}; "
          f"{len(data['events'])} hand-checked events ({data['unchecked_events']} unchecked, not exported)")


if __name__ == "__main__":
    main()
