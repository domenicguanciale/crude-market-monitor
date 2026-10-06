"""Daily ship transits through oil chokepoints, from IMF PortWatch. Expansion item 9.

Run: .venv/bin/python chokepoints.py
Source confirmed Oct 5, 2026: IMF PortWatch public ArcGIS services (Daily_Chokepoints_Data and
PortWatch_chokepoints_database), no key, daily from Jan 1, 2019, counted from satellite AIS signals.
Terms: IMF data may be downloaded, published and redistributed with attribution to the IMF
(imf.org copyright and terms). Credit: IMF PortWatch (portwatch.imf.org).

Each chokepoint is stored as a facility (type 'tanker or shipping lane', with latitude and
longitude for the map) and its daily counts in chokepoint_transit.
"""

import pandas as pd
import requests

import db

BASE = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services"
DAILY = f"{BASE}/Daily_Chokepoints_Data/FeatureServer/0/query"
DATABASE = f"{BASE}/PortWatch_chokepoints_database/FeatureServer/0/query"
PAGE = 1000   # the service's maxRecordCount

# PortWatch id -> our facility id. The six chokepoints that matter most for oil flows.
CHOKEPOINTS = {
    "chokepoint6": "strait-of-hormuz",
    "chokepoint4": "bab-el-mandeb-strait",
    "chokepoint1": "suez-canal",
    "chokepoint5": "malacca-strait",
    "chokepoint7": "cape-of-good-hope",
    "chokepoint3": "bosporus-strait",
}
OWNER = "IMF PortWatch (attribution to the IMF required)"
PUBLISHABLE = True


def query(url, params):
    resp = requests.get(url, params={**params, "f": "json"}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"PortWatch error: {data['error']}")
    return [f["attributes"] for f in data.get("features", [])]


def fetch_locations():
    ids = ",".join(f"'{p}'" for p in CHOKEPOINTS)
    return query(DATABASE, {"where": f"portid in ({ids})", "outFields": "portid,portname,lat,lon",
                            "returnGeometry": "false"})


def fetch_daily(portid):
    """All daily rows for one chokepoint, page by page."""
    rows, offset = [], 0
    while True:
        page = query(DAILY, {"where": f"portid='{portid}'", "orderByFields": "date",
                             "outFields": "date,portid,n_tanker,n_total,capacity_tanker,capacity",
                             "resultOffset": offset, "resultRecordCount": PAGE})
        rows.extend(page)
        if len(page) < PAGE:
            return rows
        offset += PAGE


def parse_daily(rows):
    df = pd.DataFrame(rows)
    return pd.DataFrame({
        "facility_id": df["portid"].map(CHOKEPOINTS),
        "transit_date": pd.to_datetime(df["date"]).dt.date,
        "tankers": pd.to_numeric(df["n_tanker"]).astype("Int64"),
        "all_ships": pd.to_numeric(df["n_total"]).astype("Int64"),
        "tanker_capacity_t": pd.to_numeric(df["capacity_tanker"]),
        "all_capacity_t": pd.to_numeric(df["capacity"]),
    }).drop_duplicates(["facility_id", "transit_date"])


def store_locations(con, locations):
    for loc in locations:
        con.execute("""INSERT INTO facility (facility_id, name, type, country, latitude, longitude)
                       VALUES (?, ?, 'tanker or shipping lane', NULL, ?, ?)
                       ON CONFLICT (facility_id) DO UPDATE SET latitude = EXCLUDED.latitude,
                           longitude = EXCLUDED.longitude""",
                    [CHOKEPOINTS[loc["portid"]], loc["portname"], loc["lat"], loc["lon"]])


def store_daily(con, df):
    """Add new days and update revised ones. PortWatch keeps the full history; nothing is deleted."""
    con.execute("INSERT OR REPLACE INTO chokepoint_transit SELECT * FROM df")


def main():
    con = db.connect()
    store_locations(con, fetch_locations())
    for portid, facility_id in CHOKEPOINTS.items():
        df = parse_daily(fetch_daily(portid))
        store_daily(con, df)
        print(f"{facility_id:<22} {len(df):>5} days, {df.transit_date.min()} to {df.transit_date.max()}")


if __name__ == "__main__":
    main()
