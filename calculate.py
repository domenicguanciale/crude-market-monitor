"""Compute the calculated properties on every weekly reading and save them.

Run after fetch.py: .venv/bin/python calculate.py
"""

import db
import score
import seasonal


def main():
    con = db.connect()
    weekly = con.execute("SELECT * FROM weekly_reading ORDER BY week_ending").df()
    if weekly.empty:
        raise RuntimeError("weekly_reading is empty. Run fetch.py first.")
    prices = con.execute("SELECT * FROM price_series").df()

    # Step 5: five-year comparison. Step 6: score, label, and weekly Brent minus WTI spread.
    calc = seasonal.compare_all(weekly, exclude_years=seasonal.ABNORMAL_YEARS)
    calc = score.add_scores(calc)
    spread = score.weekly_spread(prices)
    calc = calc.drop(columns="spread").merge(spread, on="week_ending", how="left")

    # Write every calculated column back to its row, matched by week_ending
    new_columns = ["week_year", "week_number"] + [
        f"{prefix}_{stat}"
        for prefix in seasonal.INPUTS.values()
        for stat in ["low", "high", "avg", "position", "pct_vs_avg"]
    ] + ["tightness_score", "tightness_label", "spread"]
    assignments = ", ".join(f"{c} = calc.{c}" for c in new_columns)
    con.execute(f"UPDATE weekly_reading SET {assignments} FROM calc "
                f"WHERE weekly_reading.week_ending = calc.week_ending")

    scored = calc.dropna(subset=["tightness_score"])
    print(f"Saved for {len(calc)} weeks. Scored weeks: {len(scored)}, "
          f"from {scored.week_ending.min():%Y-%m-%d} to {scored.week_ending.max():%Y-%m-%d}.")
    print("Label counts:", scored["tightness_label"].value_counts().to_dict())


if __name__ == "__main__":
    main()
