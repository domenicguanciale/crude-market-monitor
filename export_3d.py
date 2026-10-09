"""Write docs/data/viz3d.js for the 3D page (docs/3d.html).

Run after the data scripts: .venv/bin/python export_3d.py
The page is static (GitHub Pages): no server, no keys. It loads only this one file.
The file is JavaScript (window.VIZ3D = {...}). A second file, docs/data/flows.json, is loaded only when the
world flows view opens (lazy loading, M6), because most visitors never open it. A third, docs/data/dash.json,
holds the series only the 2D dashboard uses (M7) and is fetched when the dashboard scrolls into view.

What goes in:
- Daily tanker transits at the six chokepoints, 7-day average (IMF PortWatch, credit required)
- Daily Brent and WTI (EIA), 10-year Treasury yield (FRED), Geopolitical Risk Index, 7-day average (Caldara and Iacoviello, CC BY)
- The weekly tightness score and its three inputs, computed twice: 2020 left out of the five-year range
  (the project default) and 2020 kept in
- A land mask for the globe and a detailed coastline of the Persian Gulf region (Natural Earth, public domain,
  via the world-atlas package; tools/ has the scripts that made them)
- Daily 20-day realized volatility of Brent and WTI and weekly price and volatility rows (from spikes.py, M6)
- The spike catalog (rule-detected moves). A cause note and its sources are exported only for spikes the
  user has hand-checked; every other pin says "not yet hand-checked"
- flows.json: measured flows only. Tier A (EIA US crude imports by origin) and Tier B (EIA crude production by
  country). Tier C, the modeled allocation in ipf.py, is never exported (no publishable totals or prior)
- Facility pins for the Hormuz close-up, but only facilities tied to a hand-checked disruption event.
  The facility rows were created from the AI-drafted event tables, so an unchecked row never puts a pin
  on the public page. Names and places only.

Same rules as export_showcase.py: only series cleared for publishing leave this machine.
NASDAQ, the high-yield spread, OVX and prediction market data are never exported, and neither are
disruption events that have not been hand-checked.
"""

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

import chokepoints
import compare_2020
import db
import fred
import gpr
import seasonal
import spikes

HERE = Path(__file__).parent
OUT = HERE / "docs" / "data" / "viz3d.js"
FLOWS_OUT = HERE / "docs" / "data" / "flows.json"
DASH_OUT = HERE / "docs" / "data" / "dash.json"
FLOW_BASELINE_YEAR = 2025                # "change from before the disruption" = against the 2025 monthly average
BUDGET_KB = {"viz3d.js": 1536, "flows.json": 512, "dash.json": 512}   # gzipped size limits, checked by tests/test_export_3d.py
LAND = HERE / "land_mask.json"          # made once from world-atlas land-110m, see tools/make_globe_mask.mjs
REGION = HERE / "region_land.json"      # world-atlas land-10m clipped to the Gulf, see tools/make_region_land.mjs
START = dt.date(1986, 1, 2)              # first EIA WTI spot price; the shared timeline starts here (M5)
PORTWATCH_START = dt.date(2019, 1, 1)    # chokepoint data starts here
BASELINE = (dt.date(2019, 1, 1), dt.date(2025, 12, 31))
FIRST_YEAR = 1996                        # first full year of scores (scores start Nov 1995)
REPO = "https://github.com/domenicguanciale/crude-market-monitor"

PUBLISHABLE = {
    "Brent and WTI (EIA)": True,
    "10-year Treasury yield (FRED)": fred.INDICATORS["UST10Y"]["publishable"],
    "Hormuz and other chokepoints (IMF PortWatch)": chokepoints.PUBLISHABLE,
    "Geopolitical Risk Index": gpr.PUBLISHABLE,
    "Realized volatility and spike catalog (computed from EIA prices)": True,
    "US crude imports by origin, Tier A (EIA)": True,
    "Crude production by country, Tier B (EIA)": True,
    "Country label points (Natural Earth)": True,
    "Broad US dollar index (FRED)": fred.INDICATORS["USD_BROAD"]["publishable"],
    "US inventories, refinery use, SPR and futures curve (EIA)": True,
    "US retail gasoline and diesel (EIA)": True,
    "Trader positioning (CFTC Commitments of Traders)": True,
}
EXPORTED_TIERS = ("A",)                  # trade_flow tiers allowed out; "C" (modeled) must never appear here


def check_publishable():
    blocked = [k for k, ok in PUBLISHABLE.items() if not ok]
    if blocked:
        raise RuntimeError(f"Refusing to export series not cleared for publishing: {blocked}")


def day_index(end):
    return pd.date_range(START, end, freq="D")


def compact(values):
    """A day-indexed list -> {"s": index of the first value, "v": values from there to the last value}.
    Days before a series starts (for example PortWatch before 2019) are simply absent, not padded."""
    first = next((i for i, v in enumerate(values) if v is not None), None)
    if first is None:
        return {"s": 0, "v": []}
    last = max(i for i, v in enumerate(values) if v is not None)
    return {"s": first, "v": values[first:last + 1]}


def aligned(df, date_col, value_col, idx, fill_limit=None, digits=2):
    """One value per calendar day. Gaps (weekends, holidays) carry the last value forward, at most `fill_limit`
    days (None = no limit, 0 = no carrying, so only days with a real value are filled)."""
    s = df.assign(d=pd.to_datetime(df[date_col])).set_index("d")[value_col].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s = s.reindex(s.index.union(idx))
    if fill_limit != 0:
        s = s.ffill(limit=fill_limit)
    s = s.reindex(idx)
    return [None if np.isnan(v) else round(float(v), digits) for v in s]


def chokepoint_block(con, idx):
    fac = con.execute("SELECT facility_id, name, latitude, longitude FROM facility "
                      "WHERE type = 'tanker or shipping lane' AND latitude IS NOT NULL ORDER BY name").fetchall()
    out = []
    for fid, name, lat, lon in fac:
        t = con.execute("SELECT transit_date, tankers FROM chokepoint_transit WHERE facility_id = ? "
                        "ORDER BY transit_date", [fid]).df()
        t["transit_date"] = pd.to_datetime(t["transit_date"])
        t["tankers"] = t["tankers"].astype(float)
        base = t[(t.transit_date >= pd.Timestamp(BASELINE[0])) & (t.transit_date <= pd.Timestamp(BASELINE[1]))]["tankers"].median()
        t["avg7"] = t["tankers"].rolling(7).mean()
        out.append({"id": fid, "name": name, "lat": round(lat, 3), "lon": round(lon, 3),
                    "baseline": float(base), "tankers7": compact(aligned(t, "transit_date", "avg7", idx, 3, 1))})
    return out


def price_block(con, idx):
    px = con.execute("SELECT benchmark, price_date, price FROM price_series WHERE benchmark IN ('Brent', 'WTI') "
                     "AND price_date >= ?", [START - dt.timedelta(days=10)]).df()
    ind = con.execute("SELECT indicator, obs_date, value FROM daily_indicator WHERE indicator IN ('UST10Y', 'GPR') "
                      "AND obs_date >= ? ORDER BY obs_date", [START - dt.timedelta(days=20)]).df()
    g = ind[ind.indicator == "GPR"].copy()
    g["avg7"] = g["value"].rolling(7).mean()
    return {
        "brent": compact(aligned(px[px.benchmark == "Brent"], "price_date", "price", idx, 5)),
        "wti": compact(aligned(px[px.benchmark == "WTI"], "price_date", "price", idx, 5)),
        "ust10y": compact(aligned(ind[ind.indicator == "UST10Y"], "obs_date", "value", idx, 5)),
        "gpr": compact(aligned(g, "obs_date", "avg7", idx, 3, 0)),
    }


def weekly_block(con):
    weekly = con.execute("SELECT * FROM weekly_reading ORDER BY week_ending").df()
    weekly["week_ending"] = pd.to_datetime(weekly["week_ending"])
    modes = {"out": compare_2020.scores(weekly, seasonal.ABNORMAL_YEARS),   # project default: 2020 left out
             "in": compare_2020.scores(weekly)}                              # 2020 kept in the range
    base = modes["out"]
    keep = base["tightness_score"].notna() & (base["week_year"] >= FIRST_YEAR)
    rows = []
    for i in base.index[keep]:
        r = {"d": base.at[i, "week_ending"].date().isoformat(), "y": int(base.at[i, "week_year"]),
             "w": int(base.at[i, "week_number"]), "spread": None if pd.isna(base.at[i, "spread"]) else round(float(base.at[i, "spread"]), 2)}
        for key, df in modes.items():
            sc = df.at[i, "tightness_score"]
            r[key] = None if pd.isna(sc) else [int(sc),
                                               round(float(df.at[i, "crude_position"]), 2),
                                               round(float(df.at[i, "distillate_position"]), 2),
                                               round(float(df.at[i, "utilization_position"]), 2)]
        rows.append(r)
    return rows


# Schematic shipping lanes as (lat, lon) waypoints, checked against the coastline to stay in open water.
# They are NOT vessel tracks. The page uses them only to draw ships moving along plausible paths.
TRUNK = [(26.40, 55.00), (26.46, 55.80), (26.45, 56.40), (26.15, 56.78), (25.75, 57.12),
         (25.40, 57.80), (25.05, 58.70), (24.70, 59.60), (24.35, 60.80), (24.20, 61.40)]
FEEDERS = {   # route -> (facility_id it is drawn from, waypoints into the head of TRUNK)
    "basra":    ("basra-oil-company-fields", [(29.55, 48.85), (28.80, 49.60), (27.90, 50.70), (27.20, 51.90), (26.75, 53.00), (26.25, 53.70), (26.40, 54.40)], 3),
    "kuwait":   ("kuwait-oilfields-kpc",     [(29.05, 48.45), (28.60, 49.30), (27.90, 50.70), (27.20, 51.90), (26.75, 53.00), (26.25, 53.70), (26.40, 54.40)], 2),
    "safaniya": ("safaniya-and-zuluf-offshore-fields", [(28.10, 49.35), (27.60, 50.40), (27.20, 51.90), (26.75, 53.00), (26.25, 53.70), (26.40, 54.40)], 3),
    "adnoc":    ("adnoc-oilfields",          [(25.15, 53.30), (25.60, 54.20), (26.20, 54.75)], 3),
    "iran":     ("iranian-ports",            [(27.05, 56.55), (26.72, 56.50)], 1),
}   # the number is how many display ships each route gets per 12 ships. Display weights, not measured shares.


def region_block(con):
    fac = con.execute("SELECT facility_id, name, type, country, latitude, longitude FROM facility "
                      "WHERE latitude IS NOT NULL AND type <> 'tanker or shipping lane' "
                      "AND facility_id IN (SELECT facility_id FROM disruption_event WHERE hand_checked) "
                      "ORDER BY name").fetchall()
    lanes = []
    for key, (fid, pts, weight) in FEEDERS.items():
        full = pts + TRUNK[:1] + TRUNK[1:] if key != "iran" else pts + TRUNK[2:]
        lanes.append({"key": key, "facility": fid, "weight": weight, "pts": [[round(lo, 3), round(la, 3)] for la, lo in full]})
    return {"land": json.loads(REGION.read_text()),
            "facilities": [{"id": i, "name": n, "type": t, "country": c, "lat": la, "lon": lo} for i, n, t, c, la, lo in fac],
            "lanes": lanes}


def market_block(con, idx):
    """Daily 20-day realized volatility per benchmark, and one row per ISO week for the skyline:
    [ISO year, ISO week, Friday of that week, average price over its trading days, last 20-day volatility]."""
    rv = con.execute("SELECT indicator, obs_date, value FROM daily_indicator WHERE indicator IN ('RV20_BRENT', 'RV20_WTI') "
                     "ORDER BY obs_date").df()
    px = con.execute("SELECT benchmark, price_date, price FROM price_series WHERE benchmark IN ('Brent', 'WTI') "
                     "AND price_date >= ? ORDER BY price_date", [START]).df()
    out = {"rv20": {}, "weekly": {}}
    for b in ("Brent", "WTI"):
        r = rv[rv.indicator == "RV20_" + b.upper()]
        out["rv20"][b.lower()] = compact(aligned(r, "obs_date", "value", idx, 0, 4))   # trading days only, so ranks match spikes.py
        p = px[px.benchmark == b].assign(d=pd.to_datetime(px.price_date))
        p = p.merge(r.assign(d=pd.to_datetime(r.obs_date))[["d", "value"]], on="d", how="left")
        iso = p.d.dt.isocalendar()
        rows = []
        for (y, w), g in p.groupby([iso.year, iso.week]):
            last_rv = g["value"].dropna()
            rows.append([int(y), int(w), dt.date.fromisocalendar(int(y), int(w), 5).isoformat(),
                         round(float(g.price.mean()), 2), None if last_rv.empty else round(float(last_rv.iloc[-1]), 3)])
        out["weekly"][b.lower()] = rows
    return out


def spike_block(con):
    """Every cataloged spike, as found by the rules in spikes.py. Facts only (dates, prices, size, rule).
    The cause note and its sources go out only when the user has hand-checked the spike."""
    rows = con.execute("SELECT spike_id, benchmark, kind, rule, direction, start_date, extreme_date, start_price, "
                       "extreme_price, size_usd, size_pct, nonpositive, hand_checked, cause_note, source_ids "
                       "FROM spike ORDER BY extreme_date, spike_id").fetchall()
    out = []
    for sid, bench, kind, rule, direction, d0, d1, p0, p1, usd, pct, nonpos, checked, note, src in rows:
        r = {"id": sid, "b": bench, "k": kind, "rule": rule, "dir": direction, "d0": d0.isoformat(), "d1": d1.isoformat(),
             "p0": None if p0 is None else round(p0, 2), "p1": None if p1 is None else round(p1, 2),
             "usd": None if usd is None else round(usd, 2), "pct": None if pct is None or pd.isna(pct) else round(pct, 4),
             "neg": bool(nonpos), "checked": bool(checked)}
        # Tag any spike that rests on an unconfirmed print, including Brent minus WTI spikes on a Brent print
        if any(b in (bench, bench.split("-")[0]) and d0 <= d <= d1 for b, d in spikes.UNCONFIRMED):
            r["unconfirmed"] = True
        if checked and note:
            ids = [i for i in (src or "").split(",") if i]
            srcs = con.execute("SELECT publisher, url FROM source WHERE source_id IN (SELECT unnest(?::VARCHAR[]))", [ids]).fetchall() if ids else []
            r["note"] = note
            r["sources"] = [[pub, url] for pub, url in srcs]
        out.append(r)
    return out


def flows_block(con):
    """Measured flows by month for the world flows view (written to flows.json, loaded on demand).
    Each country series is {"s": first month index, "v": thousand b/d}; a month without a reported row is null."""
    tiers = list(EXPORTED_TIERS)
    imp = con.execute("SELECT period, exporter, volume_kbd FROM trade_flow WHERE importer = 'USA' AND product = 'crude' "
                      "AND tier IN (SELECT unnest(?::VARCHAR[])) ORDER BY period", [tiers]).df()
    prod = con.execute("SELECT period, country, volume_kbd FROM production_by_country ORDER BY period").df()
    places = {iso: (name, region, lat, lon) for iso, name, region, lat, lon in con.execute(
        "SELECT iso3, name, region, label_lat, label_lon FROM country WHERE label_lat IS NOT NULL").fetchall()}
    first = min(imp.period.min(), prod.period.min())
    last = max(imp.period.max(), prod.period.max())
    months = [m.date() for m in pd.date_range(first, last, freq="MS")]
    pos = {m: i for i, m in enumerate(months)}

    def series(df, key):
        out, base = {}, {}
        for iso, g in df.groupby(key):
            if iso not in places:
                continue
            vals = [None] * len(months)
            for per, v in zip(g.period, g.volume_kbd):
                vals[pos[pd.Timestamp(per).date()]] = None if pd.isna(v) else round(float(v), 1)
            out[iso] = compact(vals)
            y = g[pd.to_datetime(g.period).dt.year == FLOW_BASELINE_YEAR].volume_kbd.dropna()
            if len(y):
                base[iso] = [round(float(y.mean()), 1), int(len(y))]
        return out, base

    production, prod_base = series(prod, "country")
    imports, imp_base = series(imp, "exporter")
    used = set(production) | set(imports) | {"USA"}
    return {
        "months": [m.isoformat()[:7] for m in months],
        "baseline_year": FLOW_BASELINE_YEAR,
        "countries": {iso: [places[iso][0], places[iso][1], round(places[iso][2], 2), round(places[iso][3], 2)] for iso in sorted(used)},
        "production": production, "production_base": prod_base,
        "us_imports": imports, "us_imports_base": imp_base,
        "unmapped_producers": sorted(set(prod.country) - set(places)),
        "subregions": {iso: sub for iso, sub in con.execute("SELECT iso3, subregion FROM country").fetchall() if iso in used},
        "tiers": {"A": "Measured bilateral: EIA US crude oil imports by country of origin, thousand b/d",
                  "B": "Measured country totals: EIA international data, crude oil production, thousand b/d"},
        "sources": [["U.S. Energy Information Administration, petroleum/move/impcus", "https://www.eia.gov/opendata/browser/petroleum/move/impcus"],
                    ["U.S. Energy Information Administration, international", "https://www.eia.gov/opendata/browser/international"],
                    ["Natural Earth (label points, public domain)", "https://www.naturalearthdata.com/about/terms-of-use/"]],
    }


def dash_block(con, idx):
    """Series used only by the 2D dashboard (dash.json). Daily series are trading days only (nothing carried).
    Weekly and positioning tables are columns: {"d": [dates], "name": [values], ...}."""
    def daily(sql, params=(), digits=2):
        df = con.execute(sql, list(params)).df()
        return compact(aligned(df, "d", "v", idx, 0, digits)) if len(df) else {"s": 0, "v": []}
    def r(v, digits):
        return None if v is None or pd.isna(v) else round(float(v), digits)

    out = {
        "brent": daily("SELECT price_date d, price v FROM price_series WHERE benchmark = 'Brent' AND price_date >= ?", [START]),
        "wti": daily("SELECT price_date d, price v FROM price_series WHERE benchmark = 'WTI' AND price_date >= ?", [START]),
        "rv60": {b.lower(): daily("SELECT obs_date d, value v FROM daily_indicator WHERE indicator = ?", ["RV60_" + b.upper()], 4)
                 for b in ("Brent", "WTI")},
        "usd": daily("SELECT obs_date d, value v FROM daily_indicator WHERE indicator = 'USD_BROAD' AND obs_date >= ?", [START]),
    }
    w = con.execute("""SELECT week_ending, crude_stocks, crude_low, crude_avg, crude_high, crude_position,
                              distillate_stocks, distillate_low, distillate_avg, distillate_high, distillate_position,
                              utilization, utilization_low, utilization_avg, utilization_high, utilization_position,
                              spr_stocks, futures_gap_pct, curve_state
                       FROM weekly_reading WHERE week_ending >= ? ORDER BY week_ending""", [START]).df()
    cols = {"d": [d.date().isoformat() for d in pd.to_datetime(w.week_ending)]}
    for c in w.columns[1:]:
        if c == "curve_state":
            cols["curve"] = [None if pd.isna(v) else v for v in w[c]]
        else:
            cols[c] = [r(v, 4 if c.endswith(("position", "pct")) else 1) for v in w[c]]
    out["weekly"] = cols
    t = con.execute("""SELECT report_date, released, mm_net_pct_oi,
                              (commercial_long - commercial_short) / open_interest AS comm_net_pct_oi
                       FROM trader_positioning WHERE contract_code = '067651' ORDER BY report_date""").df()
    out["cot"] = {"d": [d.date().isoformat() for d in pd.to_datetime(t.report_date)],
                  "released": [d.date().isoformat() for d in pd.to_datetime(t.released)],
                  "mm": [r(v, 4) for v in t.mm_net_pct_oi], "comm": [r(v, 4) for v in t.comm_net_pct_oi]}
    for prod in ("gasoline", "diesel"):
        f = con.execute("SELECT week_date, price FROM retail_fuel_price WHERE product = ? ORDER BY week_date", [prod]).df()
        out[prod] = {"d": [d.date().isoformat() for d in pd.to_datetime(f.week_date)], "v": [r(v, 3) for v in f.price]}
    out["sources"] = {
        "prices": "U.S. Energy Information Administration, daily spot prices (RBRTE, RWTC)",
        "volatility": "Computed from EIA daily spot prices (spikes.py)",
        "weekly": "U.S. Energy Information Administration, Weekly Petroleum Status Report; five-year range per METHODS.md section 1",
        "curve": "U.S. Energy Information Administration, NYMEX WTI futures contracts 1 and 4 (RCLC1, RCLC4), ends April 5, 2024",
        "cot": "U.S. Commodity Futures Trading Commission, Commitments of Traders (legacy and disaggregated), WTI 067651",
        "usd": "Board of Governors of the Federal Reserve System via FRED, Nominal Broad U.S. Dollar Index (DTWEXBGS)",
        "ust10y": "Board of Governors of the Federal Reserve System via FRED, 10-year Treasury yield (DGS10)",
        "retail": "U.S. Energy Information Administration, weekly US retail gasoline and diesel prices",
        "shipping": "IMF PortWatch, daily tanker transits, 7-day average",
        "flows": "U.S. Energy Information Administration, international data and US crude imports by origin",
    }
    return out


def main():
    check_publishable()
    con = db.connect()
    end = con.execute("""SELECT greatest((SELECT max(price_date) FROM price_series WHERE benchmark IN ('Brent', 'WTI')),
                                         (SELECT max(transit_date) FROM chokepoint_transit))""").fetchone()[0]
    idx = day_index(pd.Timestamp(end))
    data = {
        "format": 2,                      # series are {"s": first day index, "v": values}
        "generated": dt.date.today().isoformat(),
        "portwatch_start": PORTWATCH_START.isoformat(),
        "repo": REPO,
        "start": START.isoformat(),
        "days": len(idx),
        "baseline": [d.isoformat() for d in BASELINE],
        "land": json.loads(LAND.read_text()),
        "region": region_block(con),
        "chokepoints": chokepoint_block(con, idx),
        "prices": price_block(con, idx),
        "weeks": weekly_block(con),
        "market": market_block(con, idx),
        "spikes": spike_block(con),
        "credits": ["EIA (Brent, WTI, inventories, refinery utilization, SPR, futures, retail fuel, production by country, US imports by origin)",
                    "IMF PortWatch (tanker transits)", "Federal Reserve via FRED (10-year Treasury yield, broad dollar index)",
                    "CFTC (Commitments of Traders)", "Caldara and Iacoviello (Geopolitical Risk Index, CC BY)",
                    "Natural Earth (land outlines and label points, public domain)"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.VIZ3D=" + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"Wrote {OUT.relative_to(HERE)} ({OUT.stat().st_size / 1024:.0f} KB): {len(idx)} days, "
          f"{len(data['chokepoints'])} chokepoints, {len(data['weeks'])} scored weeks, {len(data['spikes'])} spikes")
    dash = dash_block(con, idx)
    DASH_OUT.write_text(json.dumps(dash, separators=(",", ":")))
    print(f"Wrote {DASH_OUT.relative_to(HERE)} ({DASH_OUT.stat().st_size / 1024:.0f} KB): {len(dash['weekly']['d'])} weeks, "
          f"{len(dash['cot']['d'])} positioning reports")
    flows = flows_block(con)
    FLOWS_OUT.write_text(json.dumps(flows, separators=(",", ":")))
    print(f"Wrote {FLOWS_OUT.relative_to(HERE)} ({FLOWS_OUT.stat().st_size / 1024:.0f} KB): {len(flows['months'])} months, "
          f"{len(flows['production'])} producers, {len(flows['us_imports'])} US import origins (Tier A and B only)")


if __name__ == "__main__":
    main()
