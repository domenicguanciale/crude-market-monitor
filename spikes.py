"""Spike catalog: the biggest crashes and surges in oil prices, found by rules in code (World Oil Simulation, M2).

Run after fetch.py: .venv/bin/python spikes.py
Reads daily Brent and WTI spot prices (EIA), writes the `spike` table, realized volatility into
`daily_indicator` (RV20_BRENT, RV60_WTI, ...), and docs/SPIKES.md (ranked tables, sensitivity check,
and a plain-language summary). Every threshold is in CONFIG and documented in METHODS.md section 11.

Negative prices: WTI settled at -$36.98 on April 20, 2020. A percent change is computed only when
the previous price is positive, and a log return only when both prices are positive. Dollar changes
are always computed. April 2020 is listed as its own case, never silently dropped.

This finds and measures moves. It does not explain them (that needs sources, M3), and it does not predict.
"""

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

import db

HERE = Path(__file__).parent
REPORT = HERE / "docs" / "SPIKES.md"

CONFIG = {
    "daily_thresholds": (0.08, 0.12),   # one-day move of at least 8% or 12%
    "z_window": 250,                     # trading days of history behind the unusual-move score
    "z_min_history": 60,
    "z_threshold": 4.0,                  # a log return at least 4 standard deviations from zero
    "episode_window": 60,                # trading days for surges and crashes
    "surge_pct": 0.40,                   # rise of at least 40% from the lowest price in the window
    "crash_pct": 0.35,                   # fall of at least 35% from the highest price in the window
    "cluster_gap": 5,                    # flagged days within 5 trading days belong to one episode
    "drawdown_pct": 0.30,                # turning point confirmed by a 30% move the other way
    "vol_windows": (20, 60),             # realized volatility windows, trading days
    "trading_days_per_year": 252,
    "spread_threshold": 15.0,            # Brent minus WTI at least $15 (or WTI over Brent by $15)
}
# Prints in the source data that could not be confirmed elsewhere. They are kept as published and marked
# wherever they appear (README limits, docs/RECONCILIATION.md).
UNCONFIRMED = {
    ("Brent", dt.date(2026, 10, 2)): "EIA's Brent spot of $135.51 (+18%, WTI flat) matches FRED but was not confirmed in news reports",
}

SENSITIVITY = {
    "daily_threshold": (0.06, 0.08, 0.10, 0.12, 0.15),
    "surge_pct": (0.30, 0.40, 0.50),
    "crash_pct": (0.25, 0.35, 0.45),
    "episode_window": (40, 60, 90),
    "drawdown_pct": (0.20, 0.30, 0.40),
    "spread_threshold": (10.0, 15.0, 20.0),
}


# ---------------------------------------------------------------- returns with negative-price guards
def returns(p):
    """Daily changes for one price series (a pandas Series indexed by date, trading days only)."""
    prev = p.shift(1)
    out = pd.DataFrame({"price": p, "prev": prev, "dollar": p - prev,
                        "prev_date": pd.Series(p.index, index=p.index).shift(1)})
    out["pct"] = np.where(prev > 0, p / prev - 1, np.nan)                       # undefined after a non-positive price
    with np.errstate(divide="ignore", invalid="ignore"):
        out["log"] = np.where((prev > 0) & (p > 0), np.log(p / prev), np.nan)   # never the log of a non-positive price
    out["nonpositive"] = (p <= 0) | (prev <= 0)
    return out


def zscores(log_ret, window=None, min_history=None):
    """Each day's log return divided by the standard deviation of the previous `window` days (today excluded)."""
    window = window or CONFIG["z_window"]
    min_history = min_history or CONFIG["z_min_history"]
    sd = log_ret.shift(1).rolling(window, min_periods=min_history).std()
    return log_ret / sd


def daily_shocks(p, thresholds=None, z_threshold=None):
    """Days with a move at or above the smallest threshold, an unusual-move score at or above z_threshold,
    or a non-positive price on either side of the change."""
    thresholds = thresholds or CONFIG["daily_thresholds"]
    z_threshold = z_threshold or CONFIG["z_threshold"]
    r = returns(p)
    r["z"] = zscores(r["log"])
    lo = min(thresholds)
    hit = (r["pct"].abs() >= lo) | (r["z"].abs() >= z_threshold) | r["nonpositive"]
    rows = r[hit].copy()

    def rule(row):
        if row.nonpositive:
            return "non-positive price"
        parts = [f"daily >= {int(t * 100)}%" for t in sorted(thresholds, reverse=True) if abs(row.pct) >= t][:1]
        if abs(row.z) >= z_threshold:
            parts.append(f"z >= {z_threshold:g}")
        return ", ".join(parts)

    rows["rule"] = [rule(x) for x in rows.itertuples()]
    rows["direction"] = np.where(rows["dollar"] >= 0, "up", "down")
    return rows


# ---------------------------------------------------------------- surges and crashes over a window
def window_episodes(p, direction, pct=None, window=None, gap=None):
    """Surges (direction 'up') or crashes ('down') measured against the extreme price of the last `window` days.

    A day is flagged when the price is at least `pct` above the lowest positive price of the window
    (surge) or at least `pct` below the highest price of the window (crash). Flagged days within `gap`
    trading days form one episode. Each episode runs from its turning point (the low before a surge,
    the high before a crash) to its extreme (the highest or lowest price among the flagged days).
    """
    pct = CONFIG["surge_pct" if direction == "up" else "crash_pct"] if pct is None else pct
    window = window or CONFIG["episode_window"]
    gap = gap or CONFIG["cluster_gap"]
    vals, dates = p.to_numpy(dtype=float), p.index
    flagged = []
    for t in range(len(vals)):
        seg = vals[max(0, t - window):t + 1]
        if direction == "up":
            pos = seg[seg > 0]
            if len(pos) and vals[t] / pos.min() - 1 >= pct:
                flagged.append(t)
        else:
            top = seg.max()
            if top > 0 and vals[t] / top - 1 <= -pct:
                flagged.append(t)
    clusters, cur = [], []
    for t in flagged:
        if cur and t - cur[-1] > gap:
            clusters.append(cur)
            cur = []
        cur.append(t)
    if cur:
        clusters.append(cur)

    out = []
    for c in clusters:
        lo_i = max(0, c[0] - window)
        span = vals[lo_i:c[-1] + 1]
        if direction == "up":
            masked = np.where(span > 0, span, np.inf)
            start = lo_i + int(np.argmin(masked))
            ext = start + int(np.argmax(vals[start:c[-1] + 1]))
        else:
            start = lo_i + int(np.argmax(span))
            ext = start + int(np.argmin(vals[start:c[-1] + 1]))
        out.append(_episode(dates, vals, start, ext, c[-1], direction))
    return pd.DataFrame(out, columns=EPISODE_COLUMNS)


EPISODE_COLUMNS = ["start_date", "extreme_date", "end_date", "direction", "start_price", "extreme_price",
                   "size_usd", "size_pct", "nonpositive", "recovery_date"]


def _episode(dates, vals, start, ext, end, direction, recovery=None):
    s, e = vals[start], vals[ext]
    return {"start_date": dates[start].date() if hasattr(dates[start], "date") else dates[start],
            "extreme_date": dates[ext].date() if hasattr(dates[ext], "date") else dates[ext],
            "end_date": dates[end].date() if hasattr(dates[end], "date") else dates[end],
            "direction": direction, "start_price": s, "extreme_price": e, "size_usd": e - s,
            "size_pct": e / s - 1 if s > 0 else np.nan, "nonpositive": bool(e <= 0 or s <= 0),
            "recovery_date": recovery}


# ---------------------------------------------------------------- drawdowns: turning points confirmed by a reversal
def turning_points(p, pct=None):
    """Alternating peaks and troughs. A peak is confirmed once the price falls `pct` below it, a trough once
    the price rises `pct` above it. When a trough is not positive (WTI, April 2020), the rise is measured
    from the lowest positive price since the last peak instead."""
    pct = CONFIG["drawdown_pct"] if pct is None else pct
    v = p.to_numpy(dtype=float)
    pivots, mode, hi, lo = [], None, 0, 0
    lowest_positive = v[0] if v[0] > 0 else np.inf
    for t in range(1, len(v)):
        x = v[t]
        if mode in (None, "up"):
            if x > v[hi]:
                hi = t
            if mode is None and x < v[lo]:
                lo = t
            if mode is None and v[lo] > 0 and x / v[lo] - 1 >= pct:
                pivots.append((lo, "trough")); mode, hi = "up", t
                continue
            if v[hi] > 0 and x / v[hi] - 1 <= -pct:
                pivots.append((hi, "peak")); mode, lo = "down", t
                lowest_positive = x if x > 0 else np.inf
                continue
        if mode == "down":
            if x < v[lo]:
                lo = t
            if x > 0:
                lowest_positive = min(lowest_positive, x)
            base = v[lo] if v[lo] > 0 else lowest_positive
            if np.isfinite(base) and x / base - 1 >= pct:
                pivots.append((lo, "trough")); mode, hi = "up", t
    return pivots


def drawdowns(p, pct=None):
    """Peak-to-trough declines of at least `pct`, with the date the price first regained the peak (or none)."""
    v, dates = p.to_numpy(dtype=float), p.index
    piv = turning_points(p, pct)
    out = []
    for (a, ka), (b, kb) in zip(piv, piv[1:]):
        if ka == "peak" and kb == "trough":
            later = np.nonzero(v[b:] >= v[a])[0]
            rec = dates[b + later[0]] if len(later) else None
            out.append(_episode(dates, v, a, b, b, "down", rec.date() if rec is not None else None))
    return pd.DataFrame(out, columns=EPISODE_COLUMNS)


# ---------------------------------------------------------------- volatility and the spread
def realized_vol(p, window):
    """Annualized standard deviation of daily log returns over `window` trading days."""
    r = returns(p)["log"]
    return r.rolling(window, min_periods=int(window * 0.8)).std() * np.sqrt(CONFIG["trading_days_per_year"])


def percentile_rank(series, value):
    """Share of all days in `series` with a lower value."""
    s = series.dropna()
    return float((s < value).mean()) if len(s) else np.nan


def spread_blowouts(spread, threshold=None, gap=None):
    """Runs of days with Brent minus WTI at least `threshold` dollars (direction 'up') or WTI above Brent by at
    least `threshold` (direction 'down')."""
    threshold = CONFIG["spread_threshold"] if threshold is None else threshold
    gap = gap or CONFIG["cluster_gap"]
    out = []
    for direction, mask in [("up", spread >= threshold), ("down", spread <= -threshold)]:
        idx = np.nonzero(mask.to_numpy())[0]
        clusters, cur = [], []
        for t in idx:
            if cur and t - cur[-1] > gap:
                clusters.append(cur); cur = []
            cur.append(t)
        if cur:
            clusters.append(cur)
        for c in clusters:
            seg = spread.iloc[c[0]:c[-1] + 1]
            ext = seg.idxmax() if direction == "up" else seg.idxmin()
            out.append({"start_date": spread.index[c[0]].date(), "extreme_date": ext.date(),
                        "end_date": spread.index[c[-1]].date(), "direction": direction,
                        "start_price": float(spread.iloc[c[0]]), "extreme_price": float(spread[ext]),
                        "size_usd": float(spread[ext]), "size_pct": np.nan, "nonpositive": False,
                        "recovery_date": None, "days": len(c)})
    return pd.DataFrame(out)


def positive_spread(prices):
    """Daily Brent minus WTI on days when both prices are positive. On April 20, 2020 WTI was negative, which made
    the spread $54.34 by arithmetic alone; that day is reported separately, not as a blowout."""
    both = pd.concat(prices, axis=1, sort=True).dropna()
    both = both[(both["Brent"] > 0) & (both["WTI"] > 0)]
    return both["Brent"] - both["WTI"]


# ---------------------------------------------------------------- the catalog
def load_prices(con):
    px = con.execute("SELECT benchmark, price_date, price FROM price_series WHERE benchmark IN ('Brent', 'WTI') "
                     "ORDER BY price_date").df()
    px["price_date"] = pd.to_datetime(px["price_date"])
    return {b: g.set_index("price_date")["price"].astype(float) for b, g in px.groupby("benchmark")}


def catalog(prices):
    """All flagged spikes for every benchmark, plus the Brent minus WTI blowouts, as one table."""
    parts = []
    for bench, p in prices.items():
        ds = daily_shocks(p)
        parts.append(pd.DataFrame({
            "benchmark": bench, "rule": ds["rule"], "direction": ds["direction"],
            "start_date": [d.date() if pd.notna(d) else None for d in ds["prev_date"]], "extreme_date": [d.date() for d in ds.index],
            "end_date": [d.date() for d in ds.index], "start_price": ds["prev"].to_numpy(),
            "extreme_price": ds["price"].to_numpy(), "size_usd": ds["dollar"].to_numpy(), "size_pct": ds["pct"].to_numpy(),
            "nonpositive": ds["nonpositive"].to_numpy(), "recovery_date": None, "kind": "daily"}))
        for kind, df in [("surge", window_episodes(p, "up")), ("crash", window_episodes(p, "down")),
                         ("drawdown", drawdowns(p))]:
            parts.append(df.assign(benchmark=bench, kind=kind,
                                   rule={"surge": f"rise >= {CONFIG['surge_pct']:.0%} in {CONFIG['episode_window']} days",
                                         "crash": f"fall >= {CONFIG['crash_pct']:.0%} in {CONFIG['episode_window']} days",
                                         "drawdown": f"peak to trough >= {CONFIG['drawdown_pct']:.0%}"}[kind]))
    spread = positive_spread(prices)
    sb = spread_blowouts(spread)
    if not sb.empty:
        parts.append(sb.drop(columns="days").assign(benchmark="Brent-WTI", kind="spread",
                                                    rule=f"spread >= ${CONFIG['spread_threshold']:g}"))
    cat = pd.concat(parts, ignore_index=True)
    cat["spike_id"] = [f"{b.upper().replace('-', '_')}-{k.upper()}-{d}" for b, k, d in
                       zip(cat["benchmark"], cat["kind"], cat["extreme_date"])]
    cat = cat.drop_duplicates("spike_id")
    return cat


def sensitivity(prices):
    """How many spikes each rule finds at other thresholds, and which surge and crash episodes survive every one."""
    rows = []
    for bench, p in prices.items():
        r = returns(p)
        for t in SENSITIVITY["daily_threshold"]:
            rows.append((bench, "daily move", f">= {t:.0%}", int((r["pct"].abs() >= t).sum())))
        for direction, key in [("up", "surge_pct"), ("down", "crash_pct")]:
            for t in SENSITIVITY[key]:
                rows.append((bench, "surge" if direction == "up" else "crash", f">= {t:.0%} in 60 days",
                             len(window_episodes(p, direction, pct=t))))
            for w in SENSITIVITY["episode_window"]:
                rows.append((bench, "surge" if direction == "up" else "crash", f"window {w} days",
                             len(window_episodes(p, direction, window=w))))
        for t in SENSITIVITY["drawdown_pct"]:
            rows.append((bench, "drawdown", f">= {t:.0%}", len(drawdowns(p, t))))
    spread = positive_spread(prices)
    for t in SENSITIVITY["spread_threshold"]:
        rows.append(("Brent-WTI", "spread blowout", f">= ${t:g}", len(spread_blowouts(spread, t))))
    return pd.DataFrame(rows, columns=["benchmark", "rule", "setting", "count"])


def robust_episodes(p, direction):
    """Episodes found at the strictest threshold that overlap an episode at the loosest one. When the strict rule
    splits one move into overlapping pieces, only the largest piece is kept."""
    key = "surge_pct" if direction == "up" else "crash_pct"
    strict = window_episodes(p, direction, pct=max(SENSITIVITY[key]))
    loose = window_episodes(p, direction, pct=min(SENSITIVITY[key]))
    strict = strict.assign(mag=strict["size_usd"].abs() / strict["start_price"].abs()).sort_values("mag", ascending=False)
    keep = []
    for e in strict.itertuples():
        found = ((loose["start_date"] <= e.extreme_date) & (loose["extreme_date"] >= e.start_date)).any()
        overlaps = any(k.start_date <= e.extreme_date and k.extreme_date >= e.start_date for k in keep)
        if found and not overlaps:
            keep.append(e)
    return pd.DataFrame(keep)


def mark(bench, date):
    return " (unconfirmed print, see note)" if (bench, date) in UNCONFIRMED else ""


def size_text(r):
    if r.nonpositive:
        return f"{r.size_usd:+,.2f} $ (price below zero)"
    return pct(r.size_pct)


def store(con, cat, vols):
    con.execute("DELETE FROM spike")   # derived from prices on every run; nothing measured is lost
    cols = ["spike_id", "benchmark", "kind", "rule", "direction", "start_date", "extreme_date", "end_date",
            "start_price", "extreme_price", "size_usd", "size_pct", "nonpositive", "recovery_date"]
    df = cat[cols].copy()
    con.execute(f"INSERT INTO spike ({', '.join(cols)}) SELECT {', '.join(cols)} FROM df")
    con.execute("DELETE FROM daily_indicator WHERE indicator LIKE 'RV%'")
    if not vols.empty:
        con.execute("INSERT INTO daily_indicator SELECT indicator, obs_date, value FROM vols")


# ---------------------------------------------------------------- report
def pct(v):
    return "n/a" if pd.isna(v) else f"{v:+.1%}"


def report(prices, cat, vols, sens):
    L = ["# Spike catalog", "",
         f"Generated {dt.date.today().isoformat()} by `spikes.py` from EIA daily spot prices "
         f"(WTI from {prices['WTI'].index.min():%b %-d, %Y}, Brent from {prices['Brent'].index.min():%b %-d, %Y}). "
         "Rules and thresholds: METHODS.md section 11. This table measures moves; it does not explain or predict them. "
         "Explanations with sources come next, and every spike is **not yet hand-checked**.", ""]

    # --- plain-language summary
    facts = summary_facts(prices, cat, vols)
    L += ["## Read-aloud summary", ""] + [f"- {f}" for f in facts] + [""]

    # --- negative price case
    neg = cat[(cat["kind"] == "daily") & cat["nonpositive"]].sort_values("extreme_date")
    L += ["## April 2020: the negative WTI price, its own case", "",
          "A percent change is undefined after a non-positive price, so these days are listed in dollars and kept out "
          "of the percent rankings.", "", "| Date | From | To | Dollar change | Percent change |", "|---|---|---|---|---|"]
    for r in neg.itertuples():
        L.append(f"| {r.extreme_date} | ${r.start_price:,.2f} | ${r.extreme_price:,.2f} | {r.size_usd:+,.2f} | "
                 f"{pct(r.size_pct) if not pd.isna(r.size_pct) else 'undefined'} |")
    L.append("")

    # --- top 25 daily moves each way
    for bench in ["Brent", "WTI"]:
        d = cat[(cat["benchmark"] == bench) & (cat["kind"] == "daily") & ~cat["nonpositive"]].dropna(subset=["size_pct"])
        for direction, title in [("up", "rises"), ("down", "falls")]:
            top = d[d["direction"] == direction].reindex(d["size_pct"].abs().sort_values(ascending=False).index)
            top = top[top["direction"] == direction].head(25)
            L += [f"## Top 25 one-day {title}, {bench}", "", "| Rank | Date | Move | From | To | Rule |",
                  "|---|---|---|---|---|---|"]
            for i, r in enumerate(top.itertuples(), 1):
                L.append(f"| {i} | {r.extreme_date}{mark(bench, r.extreme_date)} | {pct(r.size_pct)} | ${r.start_price:,.2f} | ${r.extreme_price:,.2f} | {r.rule} |")
            L.append("")

    # --- episodes
    for kind, title in [("surge", "Surges: rise of 40% or more within 60 trading days"),
                        ("crash", "Crashes: fall of 35% or more within 60 trading days"),
                        ("drawdown", "Drawdowns: peak to trough of 30% or more")]:
        dd = kind == "drawdown"
        L += [f"## {title}", "", "| Benchmark | Start | Extreme | Size | From | To |" + (" Regained the peak |" if dd else ""),
              "|---|---|---|---|---|---|" + ("---|" if dd else "")]
        e = cat[cat["kind"] == kind].copy()
        e["abs"] = (e["size_usd"].abs() / e["start_price"].abs())
        for r in e.sort_values("abs", ascending=False).head(25).itertuples():
            rec = f" {r.recovery_date or 'not yet'} |" if dd else ""
            L.append(f"| {r.benchmark} | {r.start_date} | {r.extreme_date}{mark(r.benchmark, r.extreme_date)} | {size_text(r)} | "
                     f"${r.start_price:,.2f} | ${r.extreme_price:,.2f} |{rec}")
        if kind != "drawdown":
            L.append("")
            L.append("An episode lasts as long as prices stay beyond the threshold, so it can run longer than 60 trading days; "
                     "its size is measured from its turning point to its extreme.")
        L.append("")

    sp = cat[cat["kind"] == "spread"].sort_values("size_usd", key=lambda s: s.abs(), ascending=False)
    L += [f"## Brent minus WTI blowouts (${CONFIG['spread_threshold']:g} or more)", "",
          "| Start | Widest | End | Widest spread |", "|---|---|---|---|"]
    for r in sp.head(15).itertuples():
        L.append(f"| {r.start_date} | {r.extreme_date}{mark('Brent', r.extreme_date)} | {r.end_date} | ${r.extreme_price:,.2f} |")
    L += ["", "Days with a non-positive WTI price are excluded: on April 20, 2020 the spread was $54.34 by arithmetic alone.", ""]

    L += ["## Sensitivity check", "",
          "The same rules at other thresholds. Changing a threshold changes how long the list is, not which moves are "
          "at the top: the largest moves pass every threshold.", "",
          "| Benchmark | Rule | Setting | Count |", "|---|---|---|---|"]
    for r in sens.itertuples():
        L.append(f"| {r.benchmark} | {r.rule} | {r.setting} | {r.count} |")
    L.append("")
    for bench, p in prices.items():
        for direction, word in [("up", "surges"), ("down", "crashes")]:
            rob = robust_episodes(p, direction)
            if not rob.empty:
                L.append(f"- **{bench} {word} found at every threshold tested** ({len(rob)}): " +
                         ", ".join(f"{r.start_date:%b %Y} to {r.extreme_date:%b %Y} ({size_text(r)})"
                                   for r in rob.sort_values("size_pct", key=lambda s: s.abs(), ascending=False).head(8).itertuples()))
    L += ["", "## Notes on the data", ""] + [f"- **{b} on {d:%B %-d, %Y}:** {note}." for (b, d), note in UNCONFIRMED.items()]
    L.append("")
    REPORT.write_text("\n".join(L) + "\n")


def summary_facts(prices, cat, vols):
    f = []
    for bench in ["Brent", "WTI"]:
        d = cat[(cat["benchmark"] == bench) & (cat["kind"] == "daily") & ~cat["nonpositive"]].dropna(subset=["size_pct"])
        up, down = d.loc[d["size_pct"].idxmax()], d.loc[d["size_pct"].idxmin()]
        f.append(f"**{bench}'s largest one-day rise** was {pct(up.size_pct)} on {up.extreme_date:%B %-d, %Y}, and its "
                 f"**largest one-day fall** {pct(down.size_pct)} on {down.extreme_date:%B %-d, %Y} "
                 "(negative-price days excluded).")
    neg = cat[(cat["kind"] == "daily") & cat["nonpositive"]]
    if not neg.empty:
        r = neg.sort_values("extreme_date").iloc[0]
        f.append(f"**WTI settled at ${r.extreme_price:,.2f} on {r.extreme_date:%B %-d, %Y}**, a fall of "
                 f"${-r.size_usd:,.2f} in one day. Percent changes are undefined around a negative price, so it is "
                 "handled in dollars.")
    for bench in ["Brent", "WTI"]:
        r = returns(prices[bench])
        big = r[r["pct"].abs() >= CONFIG["daily_thresholds"][0]]
        by_year = big.groupby(big.index.year).size()
        y2026 = int(by_year.get(2026, 0))
        rank = int((by_year > y2026).sum()) + 1
        f.append(f"**{bench} had {y2026} days with a move of 8% or more in 2026**; "
                 f"{'that is the most of any year' if rank == 1 else f'only {rank - 1} earlier year(s) had more'} "
                 f"(most: {int(by_year.max())} in {int(by_year.idxmax())}).")
    for bench in ["Brent", "WTI"]:
        v = vols[vols["indicator"] == f"RV20_{bench.upper()}"].set_index("obs_date")["value"]
        v26 = v[pd.to_datetime(v.index).year == 2026]
        if len(v26):
            peak_day, peak = v26.idxmax(), v26.max()
            f.append(f"**{bench}'s 20-day realized volatility peaked at {peak:.0%} (annualized) on {peak_day:%B %-d, %Y}**, "
                     f"higher than {percentile_rank(v, peak):.1%} of all trading days since "
                     f"{pd.to_datetime(v.index.min()):%Y}. The latest reading, {v.iloc[-1]:.0%}, is higher than "
                     f"{percentile_rank(v, v.iloc[-1]):.0%} of all days.")
    sp = cat[(cat["kind"] == "spread") & (cat["direction"] == "up")]
    if not sp.empty:
        w = sp.loc[sp["extreme_price"].idxmax()]
        sp26 = sp[pd.to_datetime(sp["extreme_date"]).dt.year == 2026]
        line = (f"**The widest Brent premium over WTI was ${w.extreme_price:,.2f} on {w.extreme_date:%B %-d, %Y}** "
                "(days with a negative WTI price excluded)")
        if not sp26.empty and sp26["extreme_price"].max() < w.extreme_price:
            w26 = sp26.loc[sp26["extreme_price"].idxmax()]
            line += f"; the widest in 2026 was ${w26.extreme_price:,.2f} on {w26.extreme_date:%B %-d}"
        if (("Brent", w.extreme_date) in UNCONFIRMED):
            line += ". That day's Brent print could not be confirmed in news reports (kept as published)"
        f.append(line + ".")
    crash = cat[(cat["kind"] == "crash") & ~cat["nonpositive"]].dropna(subset=["size_pct"])
    if not crash.empty:
        c = crash.loc[crash["size_pct"].idxmin()]
        f.append(f"**The deepest crash episode (60-day rule, positive prices)** was {c.benchmark} {pct(c.size_pct)}, from "
                 f"${c.start_price:,.2f} on {c.start_date:%b %-d, %Y} to ${c.extreme_price:,.2f} on {c.extreme_date:%b %-d, %Y}.")
    surge = cat[(cat["kind"] == "surge") & ~cat["nonpositive"]].dropna(subset=["size_pct"])
    if not surge.empty:
        s = surge.loc[surge["size_pct"].idxmax()]
        f.append(f"**The largest surge episode (60-day rule)** was {s.benchmark} {pct(s.size_pct)}, from ${s.start_price:,.2f} on "
                 f"{s.start_date:%b %-d, %Y} to ${s.extreme_price:,.2f} on {s.extreme_date:%b %-d, %Y}.")
    f.append("These are measured moves. Their causes are not assigned here: research such as Kilian (2009) finds that "
             "supply shocks have historically explained less of oil price movement than shifts in demand and fear of "
             "shortage, so no single cause is claimed for any spike.")
    return f


def main():
    con = db.connect()
    prices = load_prices(con)
    cat = catalog(prices)
    vols = []
    for bench, p in prices.items():
        for w in CONFIG["vol_windows"]:
            v = realized_vol(p, w).dropna()
            vols.append(pd.DataFrame({"indicator": f"RV{w}_{bench.upper()}", "obs_date": v.index.date, "value": v.values}))
    vols = pd.concat(vols, ignore_index=True)
    store(con, cat, vols)
    sens = sensitivity(prices)
    report(prices, cat, vols, sens)
    counts = cat.groupby(["benchmark", "kind"]).size().unstack(fill_value=0)
    print(counts.to_string())
    print(f"\nWrote {len(cat)} spikes to the spike table, {len(vols)} volatility values, and {REPORT.relative_to(HERE)}")
    print("\n".join("- " + f.replace("**", "") for f in summary_facts(prices, cat, vols)))


if __name__ == "__main__":
    main()
