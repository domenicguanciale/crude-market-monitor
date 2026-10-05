"""Five-year seasonal comparison, as in METHODS.md section 1.

For each week, compare the value to the same week number in the prior five years:
    position   = (value - low) / (high - low)
    pct_vs_avg = (value - average) / average
"""

import pandas as pd

YEARS_BACK = 5

# Score input column in weekly_reading -> prefix for its comparison columns
INPUTS = {
    "crude_stocks": "crude",
    "distillate_stocks": "distillate",
    "utilization": "utilization",
}


def add_week_numbers(df):
    """Add the ISO year and ISO week (1 to 53) of each week-ending date."""
    iso = pd.to_datetime(df["week_ending"]).dt.isocalendar()
    df = df.copy()
    df["week_year"] = iso["year"].astype(int)
    df["week_number"] = iso["week"].astype(int)
    return df


def five_year_compare(df, column):
    """Return low, high, avg, position and pct_vs_avg for one column.

    df needs week_year, week_number and the column. Rows come back in the same order.
    A week gets no result unless all five prior years have a value for that week.
    """
    # Look up any value by (year, week). Week 53 rows are left out on purpose:
    # the rule compares a week 53 to week 52 of prior years, so week 53 is never a comparison value.
    lookup = {
        (y, w): v
        for y, w, v in zip(df["week_year"], df["week_number"], df[column])
        if w <= 52 and pd.notna(v)
    }

    rows = []
    for year, week, value in zip(df["week_year"], df["week_number"], df[column]):
        compare_week = min(week, 52)  # week 53 -> week 52
        past = [lookup.get((year - k, compare_week)) for k in range(1, YEARS_BACK + 1)]
        if pd.isna(value) or any(p is None for p in past):
            rows.append((None, None, None, None, None))
            continue
        low, high = min(past), max(past)
        avg = sum(past) / len(past)
        position = (value - low) / (high - low) if high != low else None
        pct_vs_avg = (value - avg) / avg
        rows.append((low, high, avg, position, pct_vs_avg))

    return pd.DataFrame(rows, columns=["low", "high", "avg", "position", "pct_vs_avg"],
                        index=df.index, dtype="float64")


def compare_all(df):
    """Add week numbers and the five comparison columns for each score input."""
    df = add_week_numbers(df)
    for column, prefix in INPUTS.items():
        result = five_year_compare(df, column)
        for stat in result.columns:
            df[f"{prefix}_{stat}"] = result[stat]
    return df
