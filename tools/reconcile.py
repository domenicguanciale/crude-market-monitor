"""Reconcile spot-checked numbers: the original source (queried live), the database, and the public page.

Run from the project folder: .venv/bin/python tools/reconcile.py
Writes docs/RECONCILIATION.md. Reads the database read-only and the published data files; changes nothing else.
A row passes when the database equals the live source (and the page equals the database, where the page
shows that number). Run after a refresh, before publishing.
"""

import datetime as dt
import json
import sys
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import cot  # noqa: E402
import eia  # noqa: E402

OUT = ROOT / "docs" / "RECONCILIATION.md"
TOL = 0.005


def eia_value(route, series_id, frequency, date):
    d = eia.get(f"{route}/data/", {"frequency": frequency, "data[]": "value", "facets[series][]": series_id,
                                   "start": date, "end": date})["data"]
    return float(d[0]["value"]) if d else None


def fred_value(series_id, date):
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": series_id, "api_key": eia.load_api_key("FRED_API_KEY"), "file_type": "json",
                             "observation_start": date, "observation_end": date}, timeout=30).json()["observations"]
    return float(r[0]["value"]) if r and r[0]["value"] != "." else None


def cftc_mm_net(date):
    r = requests.get(cot.DISAGG_URL, params={"cftc_contract_market_code": cot.WTI_CODE,
                                             "report_date_as_yyyy_mm_dd": f"{date}T00:00:00.000",
                                             "$select": "m_money_positions_long_all,m_money_positions_short_all"},
                     timeout=30).json()
    return float(r[0]["m_money_positions_long_all"]) - float(r[0]["m_money_positions_short_all"]) if r else None


def portwatch_tankers(date):
    url = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query")
    r = requests.get(url, params={"where": f"portid='chokepoint6' AND date='{date}'", "outFields": "n_tanker",
                                  "f": "json"}, timeout=30).json().get("features", [])
    return float(r[0]["attributes"]["n_tanker"]) if r else None


def page_viz3d():
    text = (ROOT / "docs" / "data" / "viz3d.js").read_text()
    return json.loads(text.split("=", 1)[1].rstrip().rstrip(";"))


def page_value_3d(viz, key, date):
    i = (dt.date.fromisoformat(date) - dt.date.fromisoformat(viz["start"])).days
    if key == "brent":
        series = viz["prices"]["brent"]
    else:
        return None
    return series[i] if 0 <= i < len(series) else None


def main():
    con = duckdb.connect(str(ROOT / "crude_monitor.duckdb"), read_only=True)
    q = lambda sql, *p: (lambda r: None if r is None or r[0] is None else float(r[0]))(con.execute(sql, list(p)).fetchone())
    viz = page_viz3d()
    checks = [
        ("Brent spot, $/bbl", "2026-03-31", "EIA RBRTE",
         eia_value("petroleum/pri/spt", "RBRTE", "daily", "2026-03-31"),
         q("SELECT price FROM price_series WHERE benchmark='Brent' AND price_date=?", "2026-03-31"), page_value_3d(viz, "brent", "2026-03-31")),
        ("Brent spot, $/bbl", "2026-10-02", "EIA RBRTE",
         eia_value("petroleum/pri/spt", "RBRTE", "daily", "2026-10-02"),
         q("SELECT price FROM price_series WHERE benchmark='Brent' AND price_date=?", "2026-10-02"), page_value_3d(viz, "brent", "2026-10-02")),
        ("WTI spot, $/bbl (negative print)", "2020-04-20", "EIA RWTC",
         eia_value("petroleum/pri/spt", "RWTC", "daily", "2020-04-20"),
         q("SELECT price FROM price_series WHERE benchmark='WTI' AND price_date=?", "2020-04-20"), None),
        ("US crude stocks excl. SPR, thousand bbl", "2026-10-02", "EIA WCESTUS1",
         eia_value("petroleum/stoc/wstk", "WCESTUS1", "weekly", "2026-10-02"),
         q("SELECT crude_stocks FROM weekly_reading WHERE week_ending=?", "2026-10-02"), None),
        ("SPR crude stocks, thousand bbl", "2026-10-02", "EIA WCSSTUS1",
         eia_value("petroleum/stoc/wstk", "WCSSTUS1", "weekly", "2026-10-02"),
         q("SELECT spr_stocks FROM weekly_reading WHERE week_ending=?", "2026-10-02"), None),
        ("US retail gasoline, $/gal", "2026-10-05", "EIA EMM_EPMR_PTE_NUS_DPG",
         eia_value("petroleum/pri/gnd", "EMM_EPMR_PTE_NUS_DPG", "weekly", "2026-10-05"),
         q("SELECT price FROM retail_fuel_price WHERE product='gasoline' AND week_date=?", "2026-10-05"), None),
        ("10-year Treasury yield, %", "2026-10-02", "FRED DGS10", fred_value("DGS10", "2026-10-02"),
         q("SELECT value FROM daily_indicator WHERE indicator='UST10Y' AND obs_date=?", "2026-10-02"), None),
        ("Broad dollar index", "2026-10-02", "FRED DTWEXBGS", fred_value("DTWEXBGS", "2026-10-02"),
         q("SELECT value FROM daily_indicator WHERE indicator='USD_BROAD' AND obs_date=?", "2026-10-02"), None),
        ("Managed money net, contracts", "2026-09-29", "CFTC 72hh-3qpy", cftc_mm_net("2026-09-29"),
         q("SELECT mm_net FROM trader_positioning WHERE report_date=?", "2026-09-29"), None),
        ("Hormuz tanker transits, ships", "2026-03-25", "IMF PortWatch", portwatch_tankers("2026-03-25"),
         q("SELECT tankers FROM chokepoint_transit WHERE facility_id='strait-of-hormuz' AND transit_date=?", "2026-03-25"), None),
    ]
    lines = ["# Reconciliation", "",
             f"Generated {dt.date.today().isoformat()} by `tools/reconcile.py`. Each number is queried live from the original "
             "source and compared with the database and, where the public page shows it, the page data file "
             "(`docs/data/viz3d.js`).", "",
             "| Number | Date | Source | At source | In database | On page | Result |", "|---|---|---|---|---|---|---|"]
    fails = 0
    for name, date, src, s, d, p in checks:
        ok = s is not None and d is not None and abs(s - d) <= TOL and (p is None or abs(p - d) <= TOL)
        fails += not ok
        fmt = lambda v: "" if v is None else f"{v:,.3f}".rstrip("0").rstrip(".")
        lines.append(f"| {name} | {date} | {src} | {fmt(s)} | {fmt(d)} | {fmt(p) if p is not None else 'not shown'} | {'match' if ok else 'MISMATCH'} |")
    lines += ["", "## Notes", "",
              "- **Brent at the end of the first quarter of 2026.** EIA's Today in Energy article of April 7, 2026 says the "
              "\"front-month futures price of Brent crude oil finished the quarter at $118/b\". This project's Brent is EIA's daily "
              "**spot** price (RBRTE), $126.69 on March 31, 2026. Both are correct; they are different prices. Any caption that "
              "quotes $118 must say \"front-month futures\".",
              "- **Brent spot on October 2, 2026** ($135.51, +18% in one day with WTI flat) matches EIA and FRED but could not be "
              "confirmed in news reports. It is kept as published and noted in the README limits.",
              "- **WTI on April 20, 2020** is negative in the source. Every return calculation must handle it (no log of a "
              "non-positive price)."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:6 + len(checks)]))
    print(f"\n{len(checks) - fails} of {len(checks)} match. Wrote {OUT.relative_to(ROOT)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
