"""Explanations for the spike catalog: sourced notes linked to the spikes, with context from the database (M3).

Run after spikes.py: .venv/bin/python explain_spikes.py
Reads data/spikes_explained.csv (the source of truth for the explanations; edit it, then re-run), links each
episode to the spikes the rules found inside its window, adds context from the database, and writes
docs/SPIKE_EXPLANATIONS.md. Each linked spike gets the episode's note and source ids in the spike table.

Hand-checking works like the event tables: fill hand_checked in the CSV with correct, corrected or
could not confirm. Only correct and corrected count. Unchecked explanations never reach the public pages.
The explanations attribute every claim to its source and assign no single cause (see METHODS.md section 7).
"""

import datetime as dt
from pathlib import Path

import pandas as pd

import db
from events import is_checked

HERE = Path(__file__).parent
CSV = HERE / "data" / "spikes_explained.csv"
REPORT = HERE / "docs" / "SPIKE_EXPLANATIONS.md"
PORTWATCH_START = dt.date(2019, 1, 1)
LANES = {"strait-of-hormuz": "Hormuz", "bab-el-mandeb-strait": "Bab el-Mandeb", "cape-of-good-hope": "Cape of Good Hope"}


def load():
    df = pd.read_csv(CSV, dtype=str).fillna("")
    df["window_start"] = pd.to_datetime(df["window_start"]).dt.date
    df["window_end"] = pd.to_datetime(df["window_end"]).dt.date
    df["checked"] = [is_checked(v) for v in df["hand_checked"]]
    return df


def linked_spikes(con, start, end):
    return con.execute("""SELECT spike_id, benchmark, kind, direction, extreme_date, size_pct, size_usd, nonpositive
                          FROM spike WHERE extreme_date BETWEEN ? AND ? ORDER BY extreme_date""", [start, end]).df()


def context(con, start, end):
    """Database facts around one episode. Every value names its table; nothing here is a cause."""
    c = {}
    for b in ["Brent", "WTI"]:
        r = con.execute("""SELECT arg_min(price, price_date), min(price), arg_min(price_date, price),
                                  arg_max(price_date, price), max(price), arg_max(price, price_date)
                           FROM price_series WHERE benchmark = ? AND price_date BETWEEN ? AND ?""", [b, start, end]).fetchone()
        c[b] = None if r[0] is None else {"first": r[0], "low": r[1], "low_date": r[2], "high_date": r[3], "high": r[4], "last": r[5]}
    v = con.execute("""SELECT max(value), arg_max(obs_date, value) FROM daily_indicator
                       WHERE indicator = 'RV20_BRENT' AND obs_date BETWEEN ? AND ?""", [start, end]).fetchone()
    if v[0] is not None:
        rank = con.execute("SELECT avg(CASE WHEN value < ? THEN 1 ELSE 0 END) FROM daily_indicator WHERE indicator = 'RV20_BRENT'",
                           [v[0]]).fetchone()[0]
        c["vol"] = {"peak": v[0], "date": v[1], "rank": rank}
    w = con.execute("""SELECT week_ending, tightness_score, tightness_label, curve_state FROM weekly_reading
                       WHERE week_ending < ? AND tightness_score IS NOT NULL ORDER BY week_ending DESC LIMIT 4""", [start]).df()
    if not w.empty:
        c["tightness"] = {"week": w.iloc[0].week_ending, "score": int(w.iloc[0].tightness_score),
                          "label": w.iloc[0].tightness_label, "avg4": float(w.tightness_score.mean()),
                          "curve": w.iloc[0].curve_state if pd.notna(w.iloc[0].curve_state) else None}
    p = con.execute("""SELECT
          (SELECT spec_net_pct_oi FROM trader_positioning WHERE released <= ? ORDER BY report_date DESC LIMIT 1),
          (SELECT spec_net_pct_oi FROM trader_positioning WHERE released <= ? ORDER BY report_date DESC LIMIT 1)""",
                    [start, end]).fetchone()
    if p[0] is not None:
        c["positioning"] = {"before": p[0], "end": p[1]}
    if end >= PORTWATCH_START:
        ship = {}
        for lane, name in LANES.items():
            r = con.execute("""SELECT avg(tankers) FILTER (WHERE transit_date BETWEEN ? AND ?),
                                      median(tankers) FILTER (WHERE transit_date BETWEEN '2019-01-01' AND '2025-12-31')
                               FROM chokepoint_transit WHERE facility_id = ?""", [max(start, PORTWATCH_START), end, lane]).fetchone()
            if r[0] is not None and r[1]:
                ship[name] = {"avg": r[0], "share": r[0] / r[1]}
        if ship:
            c["shipping"] = ship
    return c


def context_lines(c):
    out = []
    for b in ["Brent", "WTI"]:
        x = c.get(b)
        if x:
            low = f"${x['low']:,.2f} on {x['low_date']:%b %-d, %Y}"
            out.append(f"{b} spot (EIA): ${x['first']:,.2f} at the start, high ${x['high']:,.2f} on {x['high_date']:%b %-d, %Y}, "
                       f"low {low}, ${x['last']:,.2f} at the end.")
    if "vol" in c:
        v = c["vol"]
        out.append(f"Brent 20-day realized volatility peaked at {v['peak']:.0%} on {v['date']:%b %-d, %Y}, "
                   f"higher than {v['rank']:.0%} of all days since 1987 (spikes.py).")
    if "tightness" in c:
        t = c["tightness"]
        curve = f"; futures curve {t['curve']}" if t["curve"] else "; futures curve not available (EIA futures end April 2024)"
        out.append(f"Before it began: US tightness {t['score']:+d} ({t['label']}) in the week ending {t['week']:%b %-d, %Y}, "
                   f"average {t['avg4']:+.1f} over the 4 prior weeks{curve} (weekly_reading).")
    elif True:
        out.append("Before it began: no tightness score (scores start in November 1995).")
    if "positioning" in c:
        p = c["positioning"]
        out.append(f"Large speculators' net position in WTI: {p['before']:.1%} of open interest before, {p['end']:.1%} at the end "
                   "(CFTC, dated to release).")
    if "shipping" in c:
        out.append("Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): " +
                   ", ".join(f"{k} {v['avg']:.1f} ({v['share']:.0%})" for k, v in c["shipping"].items()) + ".")
    return out


def store(con, df):
    """Attach each episode's note and sources to its linked spikes. Re-running replaces earlier links."""
    con.execute("UPDATE spike SET cause_note = NULL, source_ids = NULL, hand_checked = FALSE")
    con.execute("DELETE FROM source WHERE source_id LIKE 'spk-%'")
    for r in df.itertuples():
        ids = []
        for i, (pub, url) in enumerate([(r.source_1_publisher, r.source_1_url), (r.source_2_publisher, r.source_2_url)], 1):
            if url:
                sid = f"spk-{r.episode_id}-{i}"
                con.execute("""INSERT INTO source (source_id, event_id, publisher, url, accessed_date, kind)
                               VALUES (?, NULL, ?, ?, ?, 'citation')""", [sid, pub, url, r.accessed])
                ids.append(sid)
        con.execute("""UPDATE spike SET cause_note = ?, source_ids = ?, hand_checked = ?
                       WHERE extreme_date BETWEEN ? AND ? AND cause_note IS NULL""",
                    [f"{r.episode_id}: {r.name}", ",".join(ids), r.checked, r.window_start, r.window_end])


def report(con, df):
    L = ["# Spike explanations", "",
         f"Generated {dt.date.today().isoformat()} by `explain_spikes.py` from `data/spikes_explained.csv` and the database. "
         "Each explanation attributes its claims to the cited source and assigns no single cause: research such as "
         "Kilian (2009) finds supply shocks have historically explained less of oil price movement than shifts in demand "
         "and fear of shortage. The context lines are measured values from this project's database.", "",
         f"**Hand-checked: {int(df.checked.sum())} of {len(df)}.** Unchecked explanations stay off the public pages.", ""]
    for r in df.itertuples():
        sp = linked_spikes(con, r.window_start, r.window_end)
        status = "hand-checked" if r.checked else "not yet hand-checked"
        L += [f"## {r.episode_id}. {r.name} ({r.window_start:%b %Y} to {r.window_end:%b %Y})", "",
              f"*Status: {status}.*", "", r.explanation, "",
              "Sources: " + "; ".join(f"[{p}]({u})" for p, u in [(r.source_1_publisher, r.source_1_url),
                                                              (r.source_2_publisher, r.source_2_url)] if u) +
              f" (accessed {r.accessed}).", ""]
        L += ["**Context from the database**", ""] + [f"- {x}" for x in context_lines(context(con, r.window_start, r.window_end))]
        if not sp.empty:
            counts = sp.groupby("kind").size().to_dict()
            L.append("- Spikes found by the rules in this window: " + ", ".join(f"{n} {k}" for k, n in counts.items()) + ".")
        if r.notes:
            L += ["", f"Note for checking: {r.notes}"]
        L.append("")
    REPORT.write_text("\n".join(L) + "\n")


def main():
    con = db.connect()
    df = load()
    store(con, df)
    report(con, df)
    linked = con.execute("SELECT count(*), count(*) FILTER (WHERE hand_checked) FROM spike WHERE cause_note IS NOT NULL").fetchone()
    print(f"{len(df)} explanations ({int(df.checked.sum())} hand-checked); {linked[0]} spikes linked ({linked[1]} checked). "
          f"Wrote {REPORT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
