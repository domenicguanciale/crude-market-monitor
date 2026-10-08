"""US weekly retail gasoline and diesel prices from EIA. World Oil Simulation, M1.

Run: .venv/bin/python retail_fuel.py
Source confirmed on the live API Oct 7, 2026: route petroleum/pri/gnd, weekly.
  EMM_EPMR_PTE_NUS_DPG  US regular gasoline, all formulations, retail, $/gallon, from Aug 20, 1990
  EMD_EPD2D_PTE_NUS_DPG US No. 2 diesel, retail, $/gallon, from Mar 21, 1994
EIA data is public domain. Prices include taxes. EIA surveys stations on Mondays.
This shows what consumers paid. It is context, not part of the tightness score.
"""

import pandas as pd

import db
import eia
from check_routes import SERIES_ROUTES

SERIES = {
    "EMM_EPMR_PTE_NUS_DPG": "gasoline",
    "EMD_EPD2D_PTE_NUS_DPG": "diesel",
}


def parse(df, product):
    """eia.fetch_series output (period, value) -> rows for retail_fuel_price."""
    return pd.DataFrame({"product": product, "week_date": pd.to_datetime(df["period"]).dt.date,
                         "price": df["value"].astype(float)}).drop_duplicates(["product", "week_date"])


def store(con, rows):
    """Add new weeks and update revised ones. EIA keeps the full history; nothing is deleted."""
    con.execute("INSERT OR REPLACE INTO retail_fuel_price (product, week_date, price) "
                "SELECT product, week_date, price FROM rows")


def main():
    con = db.connect()
    for series_id, product in SERIES.items():
        rows = parse(eia.fetch_series(SERIES_ROUTES[series_id], series_id, "weekly"), product)
        store(con, rows)
        last = rows.sort_values("week_date").iloc[-1]
        print(f"{product:<9} {series_id:<23} {len(rows):>5} weeks, {rows.week_date.min()} to {last.week_date}, "
              f"latest ${last.price:.3f}/gal")


if __name__ == "__main__":
    main()
