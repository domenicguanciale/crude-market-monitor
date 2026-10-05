"""Backtest (METHODS.md section 3): after tight weeks, what did prices do over the next four weeks?

Run after calculate.py: .venv/bin/python backtest.py
Reads the database, changes nothing in it.

Each score is dated to its release (the Wednesday after the week ends), never the Friday,
so the test only uses information that was public at the time.
"""

import datetime as dt

import pandas as pd

import db

START = dt.date(2010, 1, 1)
RELEASE_LAG_DAYS = 5   # Friday week end -> Wednesday release
HORIZON_DAYS = 28      # four weeks
GROUPS = ["tight", "loose", "all"]


def release_date(week_ending, lag_days=RELEASE_LAG_DAYS):
    return week_ending + dt.timedelta(days=lag_days)


def price_on_or_after(prices, day):
    """First (date, price) on or after `day`. prices is a Series indexed by date, sorted.
    Returns (None, None) if the series ends before that day."""
    i = prices.index.searchsorted(day)
    if i >= len(prices):
        return None, None
    return prices.index[i], prices.iloc[i]


def forward_returns(weekly, prices, lag_days=RELEASE_LAG_DAYS, horizon_days=HORIZON_DAYS):
    """One row per scored week: price at release, price four weeks later, and the return.

    weekly needs week_ending and tightness_label. prices is one benchmark's daily Series.
    Weeks whose four-week window runs past the data, or that touch a price at or below zero
    (WTI on April 20, 2020), are left out because a return is not meaningful there.
    """
    rows = []
    for week_ending, label in zip(weekly["week_ending"], weekly["tightness_label"]):
        start_date, start_price = price_on_or_after(prices, release_date(week_ending, lag_days))
        if start_date is None:
            continue
        end_date, end_price = price_on_or_after(prices, start_date + dt.timedelta(days=horizon_days))
        if end_date is None or start_price <= 0 or end_price <= 0:
            continue
        rows.append({"week_ending": week_ending, "label": label,
                     "start_date": start_date, "start_price": start_price,
                     "end_date": end_date, "end_price": end_price,
                     "forward_return": end_price / start_price - 1})
    return pd.DataFrame(rows)


def summarize(results):
    """Count, average, median, hit rate (share of weeks the price rose) for tight, loose and all."""
    out = []
    for group in GROUPS:
        r = results if group == "all" else results[results["label"] == group]
        ret = r["forward_return"]
        out.append({"group": group, "count": len(r),
                    "average": ret.mean() if len(r) else None,
                    "median": ret.median() if len(r) else None,
                    "hit_rate": (ret > 0).mean() if len(r) else None})
    return pd.DataFrame(out).set_index("group")


def every_fourth(results, offset=0):
    """Keep every fourth week so no two four-week windows overlap."""
    return results.sort_values("week_ending").iloc[offset::4]


def load():
    con = db.connect()
    weekly = con.execute(
        "SELECT week_ending, week_year, tightness_label FROM weekly_reading "
        "WHERE tightness_label IS NOT NULL AND week_ending >= ? ORDER BY week_ending", [START]).df()
    weekly["week_ending"] = pd.to_datetime(weekly["week_ending"]).dt.date
    prices = con.execute("SELECT benchmark, price_date, price FROM price_series ORDER BY price_date").df()
    prices["price_date"] = pd.to_datetime(prices["price_date"]).dt.date
    series = {b: g.set_index("price_date")["price"] for b, g in prices.groupby("benchmark")}
    return weekly, series


def fmt(summary):
    s = summary.copy()
    for c in ["average", "median", "hit_rate"]:
        s[c] = s[c].map(lambda v: "" if pd.isna(v) else f"{v:+.2%}" if c != "hit_rate" else f"{v:.0%}")
    return s.to_string()


def main():
    weekly, series = load()
    samples = {"2010 to 2026": weekly, "2010 to 2025 (2026 left out)": weekly[weekly["week_year"] < 2026]}

    for benchmark in ["WTI", "Brent"]:
        for sample_name, sample in samples.items():
            results = forward_returns(sample, series[benchmark])
            print(f"\n=== {benchmark}, {sample_name}: four-week return after release ===")
            print("All weeks (windows overlap):")
            print(fmt(summarize(results)))
            print("Every fourth week (no overlap), offset 0:")
            print(fmt(summarize(every_fourth(results, 0))))
            diffs = []
            for offset in range(4):
                s = summarize(every_fourth(results, offset))
                diffs.append(s.loc["tight", "average"] - s.loc["all", "average"])
            print("Tight minus all, average return, for each of the four offsets: "
                  + ", ".join(f"{d:+.2%}" for d in diffs))

    print("\n=== Check: release dated Thursday instead of Wednesday (holiday weeks release a day late) ===")
    for benchmark in ["WTI", "Brent"]:
        s = summarize(forward_returns(weekly, series[benchmark], lag_days=6))
        print(f"{benchmark}: tight {s.loc['tight', 'average']:+.2%} vs all {s.loc['all', 'average']:+.2%}, "
              f"hit rate tight {s.loc['tight', 'hit_rate']:.0%} vs all {s.loc['all', 'hit_rate']:.0%}")


if __name__ == "__main__":
    main()
