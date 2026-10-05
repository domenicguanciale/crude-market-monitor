"""Download the seven EIA series and store them in DuckDB.

Run: .venv/bin/python fetch.py
Safe to re-run: each run replaces the stored data with EIA's latest figures.
Data source: U.S. Energy Information Administration.
"""

from functools import reduce

import pandas as pd

import db
import eia
from check_routes import SERIES_ROUTES  # only routes confirmed on the live API

# Weekly series -> column in weekly_reading
WEEKLY = {
    "WCESTUS1": "crude_stocks",
    "WDISTUS1": "distillate_stocks",
    "WPULEUS3": "utilization",
    "WCRFPUS2": "production",
    "WCREXUS2": "exports",
}

# Daily price series -> benchmark name in price_series
PRICES = {
    "RWTC": "WTI",
    "RBRTE": "Brent",
}


def fetch_weekly():
    """One row per week ending, one column per series."""
    tables = []
    for series_id, column in WEEKLY.items():
        df = eia.fetch_series(SERIES_ROUTES[series_id], series_id, "weekly")
        print(f"  {series_id:<9} {len(df):>6} weeks  {df.period.min():%Y-%m-%d} to {df.period.max():%Y-%m-%d}")
        tables.append(df.rename(columns={"period": "week_ending", "value": column}))
    # Line the five series up side by side by date. Weeks before a series started stay empty.
    weekly = reduce(lambda a, b: a.merge(b, on="week_ending", how="outer"), tables)
    weekly["week_ending"] = weekly["week_ending"].dt.date
    return weekly.sort_values("week_ending").reset_index(drop=True)


def fetch_prices():
    """One row per benchmark per trading day."""
    tables = []
    for series_id, benchmark in PRICES.items():
        df = eia.fetch_series(SERIES_ROUTES[series_id], series_id, "daily")
        print(f"  {series_id:<9} {len(df):>6} days   {df.period.min():%Y-%m-%d} to {df.period.max():%Y-%m-%d}")
        tables.append(pd.DataFrame({
            "benchmark": benchmark,
            "price_date": df["period"].dt.date,
            "price": df["value"],
        }))
    return pd.concat(tables, ignore_index=True)


def store(con, weekly, prices):
    """Replace the stored rows with the fresh download, all or nothing."""
    con.execute("BEGIN TRANSACTION")
    con.execute("DELETE FROM weekly_reading")
    con.execute("""
        INSERT INTO weekly_reading (week_ending, crude_stocks, distillate_stocks, utilization, production, exports)
        SELECT week_ending, crude_stocks, distillate_stocks, utilization, production, exports FROM weekly
    """)
    con.execute("DELETE FROM price_series")
    con.execute("INSERT INTO price_series SELECT benchmark, price_date, price FROM prices")
    con.execute("COMMIT")


def main():
    print("Weekly series:")
    weekly = fetch_weekly()
    print("Daily prices:")
    prices = fetch_prices()

    # Every EIA week should end on a Friday (weekday 4)
    not_friday = [d for d in weekly["week_ending"] if d.weekday() != 4]
    if not_friday:
        raise RuntimeError(f"{len(not_friday)} week-ending dates are not Fridays, e.g. {not_friday[:3]}")

    con = db.connect()
    store(con, weekly, prices)
    print(f"\nStored {len(weekly)} weekly readings and {len(prices)} daily prices in {db.DB_PATH.name}")


if __name__ == "__main__":
    main()
