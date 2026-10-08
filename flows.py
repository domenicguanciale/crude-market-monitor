"""Physical oil flows: who produced oil and where US imports came from (World Oil Simulation, M4).

Run: .venv/bin/python flows.py
Sources confirmed on the live EIA API, Oct 7, 2026 (public domain):
  Tier A, measured bilateral: route petroleum/move/impcus, product EPC0 (crude), monthly, thousand b/d
    (series ending in 2). US imports by country of origin. Rows for regional totals are dropped.
  Tier B, measured country totals: route international, product 57 (crude including lease condensate),
    activity 1 (production), thousand b/d, monthly.
  Country label points and regions: Natural Earth admin-0 countries, 110m (public domain), data/.

What is not here, and why: EIA publishes other countries' crude imports only annually and only to 2020, and no
exports by country. UN Comtrade (bilateral) may not be republished, and JODI's terms are not confirmed. So
modeled worldwide arcs (Tier C, ipf.py) are not built from publishable 2026 data. See README and SOURCES.md.

Revisions: when EIA revises a month, the new value replaces it and the earlier one is kept in previous_volume.
"""

import datetime as dt
import json
from pathlib import Path

import pandas as pd

import db
import eia

HERE = Path(__file__).parent
NATURAL_EARTH = HERE / "data" / "ne_110m_admin_0_countries.geojson"
START = "2010-01"
PAGE = 5000


def fetch_pages(route, params):
    rows, offset = [], 0
    while True:
        d = eia.get(f"{route}/data/", {**params, "offset": offset, "length": PAGE})
        rows.extend(d["data"])
        offset += PAGE
        if offset >= int(d["total"]):
            return rows


def parse_us_imports(rows):
    """impcus rows -> Tier A trade flows into the US, thousand b/d, countries only."""
    df = pd.DataFrame(rows)
    df = df[df["series"].str.endswith("2") & df["area-name"].str.fullmatch(r"[A-Z]{3}", na=False)]
    return pd.DataFrame({"period": pd.to_datetime(df["period"] + "-01").dt.date, "exporter": df["area-name"],
                         "importer": "USA", "product": "crude", "tier": "A",
                         "volume_kbd": pd.to_numeric(df["value"], errors="coerce"), "source_id": "ds-eia-impcus"}
                        ).dropna(subset=["volume_kbd"]).drop_duplicates(["period", "exporter"])


def parse_production(rows):
    """international rows -> monthly crude production by country, thousand b/d."""
    df = pd.DataFrame(rows)
    df = df[df["countryRegionTypeId"] == "c"]
    return pd.DataFrame({"period": pd.to_datetime(df["period"] + "-01").dt.date, "country": df["countryRegionId"],
                         "volume_kbd": pd.to_numeric(df["value"], errors="coerce"), "source_id": "ds-eia-intl"}
                        ).dropna(subset=["volume_kbd"]).drop_duplicates(["period", "country"])


EXTRA_POINTS = HERE / "data" / "ne_label_points_extra.csv"   # small countries missing at 110m (tools/make_label_points.py)


def parse_countries(geojson, extra=None):
    """Natural Earth countries, plus label points for small countries (no name or region in that file)."""
    rows = []
    for f in geojson["features"]:
        p = f["properties"]
        code = p["ISO_A3"] if p["ISO_A3"] != "-99" else p["ADM0_A3"]   # ISO code; '-99' for France and Norway in this file
        rows.append({"iso3": code, "name": p["NAME"], "region": p["REGION_UN"], "subregion": p["SUBREGION"],
                     "label_lat": p["LABEL_Y"], "label_lon": p["LABEL_X"]})
    df = pd.DataFrame(rows).drop_duplicates("iso3")
    if extra is not None and not extra.empty:
        extra = extra[~extra["iso3"].isin(df["iso3"])].assign(name=None, region=None, subregion=None)
        df = pd.concat([df, extra[df.columns]], ignore_index=True)
    return df


def upsert_with_revisions(con, table, df, keys):
    """Insert new rows; when an existing row's volume changes, keep the old value in previous_volume."""
    df = df.assign(fetched=dt.date.today())
    cols = list(df.columns)
    con.execute(f"""INSERT INTO {table} ({', '.join(cols)}) SELECT {', '.join(cols)} FROM df
                    ON CONFLICT ({', '.join(keys)}) DO UPDATE SET
                        previous_volume = CASE WHEN volume_kbd IS DISTINCT FROM EXCLUDED.volume_kbd THEN volume_kbd ELSE previous_volume END,
                        revised = revised OR (volume_kbd IS DISTINCT FROM EXCLUDED.volume_kbd),
                        volume_kbd = EXCLUDED.volume_kbd, source_id = EXCLUDED.source_id, fetched = EXCLUDED.fetched""")


def main():
    con = db.connect()
    countries = parse_countries(json.loads(NATURAL_EARTH.read_text()), pd.read_csv(EXTRA_POINTS))
    con.execute("INSERT OR REPLACE INTO country SELECT iso3, name, region, subregion, label_lat, label_lon FROM countries")
    imports = parse_us_imports(fetch_pages("petroleum/move/impcus", {
        "frequency": "monthly", "data[]": "value", "facets[product][]": "EPC0", "facets[process][]": "IM0", "start": START}))
    upsert_with_revisions(con, "trade_flow", imports, ["period", "exporter", "importer", "product", "tier"])
    prod = parse_production(fetch_pages("international", {
        "frequency": "monthly", "data[]": "value", "facets[productId][]": "57", "facets[activityId][]": "1",
        "facets[unit][]": "TBPD", "facets[countryRegionTypeId][]": "c", "start": START}))
    upsert_with_revisions(con, "production_by_country", prod, ["period", "country"])
    print(f"{len(countries)} countries; {len(imports)} Tier A US import rows ({imports.period.min()} to {imports.period.max()}, "
          f"{imports.exporter.nunique()} origins); {len(prod)} production rows ({prod.period.min()} to {prod.period.max()}, "
          f"{prod.country.nunique()} countries)")
    missing = sorted(set(prod.country) - set(countries.iso3))
    if missing:
        print(f"Producing countries without a Natural Earth label point (shown in tables, not on the map): {', '.join(missing[:20])}")


if __name__ == "__main__":
    main()
