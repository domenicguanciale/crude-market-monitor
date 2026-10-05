"""How often did the futures curve agree with the tightness score, 2010 to April 2024? HISTORY ONLY.

Run after calculate.py: .venv/bin/python curve_history.py
Reads the database, changes nothing in it.
"""

import datetime as dt

import pandas as pd

import db
import futures

START, END = dt.date(2010, 1, 1), dt.date(2024, 4, 5)  # EIA futures end April 5, 2024


def pct(v):
    return "n/a" if v is None else f"{v:.0%}"


def report(weeks, title):
    a = futures.agreement(weeks)
    print(f"\n--- {title}: {a['weeks']} weeks ({a['tight_weeks']} tight, {a['loose_weeks']} loose) ---")
    print(f"Tight weeks in backwardation:  {pct(a['tight_in_backwardation'])}   "
          f"(all weeks in backwardation: {pct(a['all_in_backwardation'])})")
    print(f"Loose weeks in contango:       {pct(a['loose_in_contango'])}   "
          f"(all weeks in contango: {pct(a['all_in_contango'])})")
    print(f"Opposite readings: tight but contango {pct(a['tight_in_contango'])}, "
          f"loose but backwardation {pct(a['loose_in_backwardation'])}")
    print(f"Backwardation weeks scored tight: {pct(a['backwardation_scored_tight'])}   "
          f"(all weeks scored tight: {pct(a['all_scored_tight'])})")
    print(f"Contango weeks scored loose:      {pct(a['contango_scored_loose'])}   "
          f"(all weeks scored loose: {pct(a['all_scored_loose'])})")


def main():
    con = db.connect()
    weeks = con.execute(
        "SELECT week_ending, week_year, tightness_label, futures_gap_pct, curve_state FROM weekly_reading "
        "WHERE week_ending BETWEEN ? AND ? ORDER BY week_ending", [START, END]).df()

    print("Futures curve (WTI contract 1 vs contract 4) against the US tightness score. HISTORY ONLY.")
    report(weeks, "2010 to April 2024, flat band +/-1%")

    sign_only = weeks.assign(curve_state=weeks["futures_gap_pct"].map(lambda g: futures.curve_state(g, band=0)))
    report(sign_only, "Same, sign only (no flat band)")

    report(weeks[weeks["week_year"] != 2020], "2010 to April 2024 without 2020 weeks, flat band +/-1%")

    print("\nCross-table, flat band +/-1% (rows: score label, columns: curve state):")
    print(pd.crosstab(weeks["tightness_label"], weeks["curve_state"]).to_string())


if __name__ == "__main__":
    main()
