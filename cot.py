"""CFTC Commitments of Traders for WTI crude: large speculators' net position. Expansion item 5.

Run: .venv/bin/python cot.py
Source confirmed live on Oct 5, 2026: CFTC Public Reporting Environment, Legacy Futures Only
report (dataset 6dca-aqww), no key needed. WTI is NYMEX contract code 067651, continuous since
1986 under three names (latest: "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE").

In the legacy report, "noncommercial" traders are the CFTC's large speculators: reportable traders
not using the market for hedging. Net speculative position = noncommercial long - noncommercial short.
Positions are measured on Tuesday (Monday, Wednesday or Friday in holiday weeks) and released
Friday at 3:30 p.m. Eastern, so any use of a reading must date it to its release, never to the
measurement day.

This describes positioning. It is not a trading signal.
"""

import datetime as dt

import pandas as pd
import requests

import db
from score import week_ending_of

URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
WTI_CODE = "067651"
MIN_RELEASE_LAG_DAYS = 2   # positions are published at least 2 days after they are measured

FIELDS = {
    "report_date_as_yyyy_mm_dd": "report_date",
    "open_interest_all": "open_interest",
    "noncomm_positions_long_all": "spec_long",
    "noncomm_positions_short_all": "spec_short",
    "noncomm_postions_spread_all": "spec_spread",   # the CFTC's own spelling of this field
    "comm_positions_long_all": "commercial_long",
    "comm_positions_short_all": "commercial_short",
    "nonrept_positions_long_all": "small_long",
    "nonrept_positions_short_all": "small_short",
}
COLUMNS = ["report_date", "released", "week_ending", "contract_code", "open_interest", "spec_long",
           "spec_short", "spec_spread", "commercial_long", "commercial_short", "small_long", "small_short",
           "spec_net", "spec_net_pct_oi"]


def release_date(report_date):
    """The Friday the report is public: the first Friday at least 2 days after the measurement day.

    Normally Tuesday -> Friday (+3). In holiday weeks the CFTC measures on Monday (-> Friday, +4),
    Wednesday (-> Friday, +2) or Friday (-> the next Friday, +7, a conservative choice).
    A federal holiday can also push publication to the following Monday; not modelled.
    """
    friday = week_ending_of(report_date)
    return friday if (friday - report_date).days >= MIN_RELEASE_LAG_DAYS else friday + dt.timedelta(days=7)


def fetch_rows():
    params = {"cftc_contract_market_code": WTI_CODE, "$select": ",".join(FIELDS),
              "$order": "report_date_as_yyyy_mm_dd", "$limit": 50000}
    resp = requests.get(URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def parse(rows):
    """CFTC rows (numbers arrive as text) -> one row per weekly report, with the calculated net position."""
    df = pd.DataFrame(rows).rename(columns=FIELDS)
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
    for c in FIELDS.values():
        if c != "report_date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["week_ending"] = [week_ending_of(d) for d in df["report_date"]]   # EIA week holding the measurement day
    df["released"] = [release_date(d) for d in df["report_date"]]
    df["contract_code"] = WTI_CODE
    df["spec_net"] = df["spec_long"] - df["spec_short"]
    df["spec_net_pct_oi"] = df["spec_net"] / df["open_interest"]
    return df[COLUMNS].drop_duplicates("report_date").sort_values("report_date").reset_index(drop=True)


def store(con, df):
    """Add new reports and update existing ones. CFTC keeps the full history, nothing is deleted."""
    con.execute(f"INSERT OR REPLACE INTO trader_positioning SELECT {', '.join(COLUMNS)} FROM df")


def main():
    df = parse(fetch_rows())
    con = db.connect()
    store(con, df)
    print(f"Stored {len(df)} weekly WTI reports, {df.report_date.min()} to {df.report_date.max()}")
    last = df.iloc[-1]
    print(f"Latest (positions {last.report_date}, released {last.released}): large speculators net "
          f"{last.spec_net:+,.0f} contracts ({last.spec_net_pct_oi:+.1%} of open interest)")


if __name__ == "__main__":
    main()
