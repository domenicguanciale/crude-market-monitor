"""Daily Geopolitical Risk Index (Caldara and Iacoviello). Expansion item 7.

Run: .venv/bin/python gpr.py
Source confirmed on Oct 5, 2026: https://www.matteoiacoviello.com/gpr.htm, daily "Recent GPR" file in
Stata format (read by pandas, no extra library). No key. Updated every Monday.
Licence: Creative Commons BY ("completely open access ... provided the source and authors are
credited"), so it may be published with credit.
Cite: Caldara, Dario and Matteo Iacoviello (2022), "Measuring Geopolitical Risk," American Economic
Review 112(4), 1194-1225. Data downloaded from https://www.matteoiacoviello.com/gpr.htm.

The index counts newspaper articles about geopolitical tension in 10 newspapers, scaled so that
1985-2019 averages 100. A value on day D reflects articles published on D, which often report
events from D-1: keep that in mind when lining it up with events.
"""

import io

import pandas as pd
import requests

import db

URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.dta"

# Indicator name in daily_indicator -> column in the file, with owner and publishing terms
SERIES = {
    "GPR": {"column": "GPRD", "title": "Daily Geopolitical Risk Index (1985-2019 = 100)"},
    "GPR_ACTS": {"column": "GPRD_ACT", "title": "Daily GPR Acts (1985-2019 = 100)"},
    "GPR_THREATS": {"column": "GPRD_THREAT", "title": "Daily GPR Threats (1985-2019 = 100)"},
}
OWNER = "Caldara and Iacoviello, matteoiacoviello.com/gpr.htm (Creative Commons BY)"
PUBLISHABLE = True   # with credit to the source and authors


def fetch():
    resp = requests.get(URL, timeout=120)
    resp.raise_for_status()
    return pd.read_stata(io.BytesIO(resp.content))


def parse(df):
    """The file's wide table -> long rows (indicator, obs_date, value), one per series per day."""
    rows = []
    for name, meta in SERIES.items():
        part = pd.DataFrame({"indicator": name,
                             "obs_date": pd.to_datetime(df["date"]).dt.date,
                             "value": pd.to_numeric(df[meta["column"]], errors="coerce").astype("float64")})
        rows.append(part.dropna(subset=["value"]))
    return pd.concat(rows, ignore_index=True)


def store(con, rows):
    """Add new days and update revised ones. Nothing is deleted."""
    con.execute("INSERT OR REPLACE INTO daily_indicator SELECT indicator, obs_date, value FROM rows")


def main():
    rows = parse(fetch())
    con = db.connect()
    store(con, rows)
    for name, part in rows.groupby("indicator"):
        print(f"{name:<12} {len(part):>6} days, {part.obs_date.min()} to {part.obs_date.max()}, "
              f"latest {part.value.iloc[-1]:,.1f}")


if __name__ == "__main__":
    main()
