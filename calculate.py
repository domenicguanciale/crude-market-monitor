"""Compute the calculated properties on every weekly reading and save them.

Run after fetch.py: .venv/bin/python calculate.py
"""

import db
import seasonal


def main():
    con = db.connect()
    weekly = con.execute("SELECT * FROM weekly_reading ORDER BY week_ending").df()
    if weekly.empty:
        raise RuntimeError("weekly_reading is empty. Run fetch.py first.")

    calc = seasonal.compare_all(weekly)

    # Write every new column back to its row, matched by week_ending
    new_columns = ["week_year", "week_number"] + [
        f"{prefix}_{stat}"
        for prefix in seasonal.INPUTS.values()
        for stat in ["low", "high", "avg", "position", "pct_vs_avg"]
    ]
    assignments = ", ".join(f"{c} = calc.{c}" for c in new_columns)
    con.execute(f"UPDATE weekly_reading SET {assignments} FROM calc "
                f"WHERE weekly_reading.week_ending = calc.week_ending")

    scored = calc.dropna(subset=["crude_position", "distillate_position", "utilization_position"])
    print(f"Five-year comparison saved for {len(calc)} weeks. "
          f"All three inputs available from {scored.week_ending.min():%Y-%m-%d}.")


if __name__ == "__main__":
    main()
