"""Write docs/data/viz3d.js for the 3D page (docs/3d.html).

Run after the data scripts: .venv/bin/python export_3d.py
The page is static (GitHub Pages): no server, no keys. It loads only this one file.
The file is JavaScript (window.VIZ3D = {...}) instead of JSON so the page also opens by double-clicking it.

What goes in:
- Daily tanker transits at the six chokepoints, 7-day average (IMF PortWatch, credit required)
- Daily Brent and WTI (EIA), 10-year Treasury yield (FRED), Geopolitical Risk Index, 7-day average (Caldara and Iacoviello, CC BY)
- The weekly tightness score and its three inputs, computed twice: 2020 left out of the five-year range
  (the project default) and 2020 kept in
- A land mask for the globe and a detailed coastline of the Persian Gulf region (Natural Earth, public domain,
  via the world-atlas package; tools/ has the scripts that made them)
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

HERE = Path(__file__).parent
OUT = HERE / "docs" / "data" / "viz3d.js"
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
}


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
    """One value per calendar day. Gaps (weekends, holidays) carry the last value forward."""
    s = df.assign(d=pd.to_datetime(df[date_col])).set_index("d")[value_col].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s = s.reindex(s.index.union(idx)).ffill(limit=fill_limit).reindex(idx)
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
        "credits": ["EIA (Brent, WTI, inventories, refinery utilization)", "IMF PortWatch (tanker transits)",
                    "Federal Reserve via FRED (10-year Treasury yield)", "Caldara and Iacoviello (Geopolitical Risk Index, CC BY)",
                    "Natural Earth (land outlines, public domain)"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.VIZ3D=" + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"Wrote {OUT.relative_to(HERE)} ({OUT.stat().st_size / 1024:.0f} KB): {len(idx)} days, "
          f"{len(data['chokepoints'])} chokepoints, {len(data['weeks'])} scored weeks")


if __name__ == "__main__":
    main()
