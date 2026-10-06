"""Daily series from FRED (Federal Reserve Bank of St. Louis), via the official FRED API.

Run: .venv/bin/python fred.py
Needs FRED_API_KEY in .env (free: fredaccount.stlouisfed.org). FRED's terms prohibit scraping,
so the API is used rather than the website's CSV links.

Copyright: some FRED series belong to third parties. FRED allows personal use; publishing them
(e.g. in the public showcase) needs the owner's permission. 'publishable' records this per series.
Credit: series data retrieved from FRED, Federal Reserve Bank of St. Louis.
"""

import pandas as pd
import requests

import db
from eia import load_api_key

API = "https://api.stlouisfed.org/fred/series/observations"

# Indicator name in daily_indicator -> FRED series and its terms. Checked on fred.stlouisfed.org, Oct 5, 2026.
INDICATORS = {
    "OVX": {"fred_id": "OVXCLS", "unit": "index",
            "title": "CBOE Crude Oil ETF Volatility Index",
            "owner": "Chicago Board Options Exchange (copyrighted, reprinted with permission)",
            "publishable": False},
    # Item 10: outcome series for the event study ("how tech funding costs reacted")
    "NASDAQ": {"fred_id": "NASDAQCOM", "unit": "index (Feb 5, 1971 = 100)",
               "title": "NASDAQ Composite Index",
               "owner": "Nasdaq OMX Group (copyrighted)",
               "publishable": False},
    "UST10Y": {"fred_id": "DGS10", "unit": "percent",
               "title": "10-Year Treasury Constant Maturity Yield",
               "owner": "Board of Governors of the Federal Reserve System (H.15, public domain)",
               "publishable": True},
    "HY_SPREAD": {"fred_id": "BAMLH0A0HYM2", "unit": "percentage points",
                  "title": "ICE BofA US High Yield Index Option-Adjusted Spread",
                  "owner": "ICE Data Indices (copyrighted; reproduction prohibited without permission). "
                           "FRED carries only the last three years (from Oct 6, 2023)",
                  "publishable": False},
}


def parse(observations):
    """FRED observations [{date, value}] -> (date, value) rows. FRED marks missing days with '.'."""
    df = pd.DataFrame(observations, columns=["date", "value"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    return pd.DataFrame({"obs_date": pd.to_datetime(df["date"]).dt.date, "value": df["value"]})


def fetch(fred_id):
    resp = requests.get(API, params={"series_id": fred_id, "api_key": load_api_key("FRED_API_KEY"),
                                     "file_type": "json"}, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"FRED returned {resp.status_code} for {fred_id}")  # never echo the URL (it holds the key)
    return resp.json()["observations"]


def store(con, indicator, df):
    """Add new days and update revised ones. FRED keeps the full history, nothing is deleted."""
    rows = df.assign(indicator=indicator)[["indicator", "obs_date", "value"]]
    con.execute("INSERT OR REPLACE INTO daily_indicator SELECT * FROM rows")


def main(names=None):
    con = db.connect()
    for name in names or INDICATORS:
        meta = INDICATORS[name]
        df = parse(fetch(meta["fred_id"]))
        store(con, name, df)
        flag = "" if meta["publishable"] else "  (personal use only: not for the public showcase)"
        print(f"{name:<6} {meta['fred_id']:<14} {len(df):>6} days, {df.obs_date.min()} to {df.obs_date.max()}, "
              f"latest {df.value.iloc[-1]:,.2f}{flag}")


if __name__ == "__main__":
    main()
