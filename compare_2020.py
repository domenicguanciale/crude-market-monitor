"""Compare the score with and without 2020 in the five-year range (METHODS.md section 1 alternative).

Run after fetch.py: .venv/bin/python compare_2020.py
Reads the database, changes nothing in it.
"""

import pandas as pd

import db
import score
import seasonal


def scores(weekly, exclude_years=()):
    return score.add_scores(seasonal.compare_all(weekly, exclude_years))


def yearly_counts(scored):
    """Number of tight, normal and loose weeks in each year."""
    counts = (scored.dropna(subset=["tightness_label"])
              .groupby(["week_year", "tightness_label"]).size().unstack(fill_value=0))
    return counts.reindex(columns=["tight", "normal", "loose"], fill_value=0)


def main():
    con = db.connect()
    weekly = con.execute("SELECT * FROM weekly_reading ORDER BY week_ending").df()

    with_2020 = scores(weekly)
    without_2020 = scores(weekly, exclude_years={2020})

    table = yearly_counts(with_2020).join(yearly_counts(without_2020), lsuffix="_with", rsuffix="_without")
    affected = table.loc[2021:2025]
    print("Weeks by label, 2020 kept in the range vs dropped (only 2021-2025 can differ):")
    print(affected.to_string())

    changed = (with_2020["tightness_label"] != without_2020["tightness_label"]) & with_2020["tightness_label"].notna()
    print(f"\nWeeks whose label changed: {changed.sum()} of {with_2020['tightness_label'].notna().sum()}")
    moves = pd.crosstab(with_2020.loc[changed, "tightness_label"], without_2020.loc[changed, "tightness_label"],
                        rownames=["with 2020"], colnames=["without 2020"])
    print(moves.to_string())

    print("\nWhich inputs changed points, 2021-2025:")
    window = with_2020["week_year"].between(2021, 2025)
    for prefix in seasonal.INPUTS.values():
        rule = score.utilization_points if prefix == "utilization" else score.stock_points
        a = with_2020.loc[window, f"{prefix}_position"].dropna().map(rule)
        b = without_2020.loc[window, f"{prefix}_position"].dropna().map(rule)
        print(f"  {prefix:<12} points changed in {(a != b).sum():>3} weeks; "
              f"average points {a.mean():+.2f} with 2020, {b.mean():+.2f} without")


if __name__ == "__main__":
    main()
