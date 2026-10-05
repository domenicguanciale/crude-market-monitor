"""US tightness score (METHODS.md section 2) and the Brent minus WTI spread.

Three inputs, each scored from its five-year position:
    Stocks (crude, distillate): +1 if position < 0.25, -1 if > 0.75, else 0
    Refinery utilization:       +1 if position > 0.75, -1 if < 0.25, else 0
Score = sum (-3 to +3). Tight at +2 or more, loose at -2 or less, otherwise normal.
Price and production are left out on purpose (see METHODS.md section 2).
"""

import datetime as dt

import pandas as pd

LOW, HIGH = 0.25, 0.75


def stock_points(position):
    """Low stocks are tight."""
    if position < LOW:
        return 1
    if position > HIGH:
        return -1
    return 0


def utilization_points(position):
    """High utilization is tight."""
    if position > HIGH:
        return 1
    if position < LOW:
        return -1
    return 0


def label(score):
    if score >= 2:
        return "tight"
    if score <= -2:
        return "loose"
    return "normal"


def score_week(crude_position, distillate_position, utilization_position):
    """Return (score, label), or (None, None) if any input has no five-year position."""
    positions = [crude_position, distillate_position, utilization_position]
    if any(pd.isna(p) for p in positions):
        return None, None
    total = (stock_points(crude_position)
             + stock_points(distillate_position)
             + utilization_points(utilization_position))
    return total, label(total)


def add_scores(df):
    """Add tightness_score and tightness_label columns to a table of weekly readings."""
    results = [score_week(c, d, u) for c, d, u in
               zip(df["crude_position"], df["distillate_position"], df["utilization_position"])]
    df = df.copy()
    df["tightness_score"] = pd.array([r[0] for r in results], dtype="Int64")  # Int64 allows blanks
    df["tightness_label"] = [r[1] for r in results]
    return df


def week_ending_of(day):
    """The Friday that closes the Saturday-to-Friday week containing this day."""
    return day + dt.timedelta(days=(4 - day.weekday()) % 7)


def weekly_spread(prices):
    """Average daily Brent minus WTI over the trading days in each week.

    prices has columns benchmark, price_date, price. Only days with both prices count.
    """
    wide = prices.pivot(index="price_date", columns="benchmark", values="price").dropna()
    daily = pd.DataFrame({
        "week_ending": [week_ending_of(d) for d in wide.index],
        "spread": wide["Brent"] - wide["WTI"],
    })
    return daily.groupby("week_ending", as_index=False)["spread"].mean()
