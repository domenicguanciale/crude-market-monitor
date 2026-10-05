"""Futures curve shape: the nearest WTI futures contract against the fourth. HISTORY ONLY.

EIA stopped publishing futures prices after April 5, 2024, and no free live source was
found, so this is a research comparison for 1983 to April 2024, never a live gauge.

    gap_pct = (contract 1 - contract 4) / contract 4

Backwardation (near contract above later one): buyers pay up for oil now, a sign of tightness.
Contango (near contract below later one): oil now is plentiful, a sign of looseness.
"""

import pandas as pd

from score import week_ending_of

NEAR, FAR = "WTI future 1", "WTI future 4"

# A gap within plus or minus 1% of the far price counts as flat. Fixed before looking at
# results; curve_history.py also reports the result with no flat band (sign only).
FLAT_BAND = 0.01


def curve_state(gap_pct, band=FLAT_BAND):
    if pd.isna(gap_pct):
        return None
    if gap_pct > band:
        return "backwardation"
    if gap_pct < -band:
        return "contango"
    return "flat"


def weekly_curve(prices, band=FLAT_BAND):
    """Weekly average of the daily contract 1 minus contract 4 gap, in dollars and as a share.

    Only days with both contracts and a positive far price count.
    """
    wide = prices.pivot(index="price_date", columns="benchmark", values="price")
    if NEAR not in wide or FAR not in wide:
        return pd.DataFrame(columns=["week_ending", "futures_gap", "futures_gap_pct", "curve_state"])
    wide = wide[[NEAR, FAR]].dropna()
    wide = wide[wide[FAR] > 0]
    daily = pd.DataFrame({
        "week_ending": [week_ending_of(d) for d in wide.index],
        "futures_gap": wide[NEAR] - wide[FAR],
        "futures_gap_pct": (wide[NEAR] - wide[FAR]) / wide[FAR],
    })
    weekly = daily.groupby("week_ending", as_index=False)[["futures_gap", "futures_gap_pct"]].mean()
    weekly["curve_state"] = weekly["futures_gap_pct"].map(lambda g: curve_state(g, band))
    return weekly


# The curve state that matches each score label
MATCH = {"tight": "backwardation", "loose": "contango", "normal": "flat"}


def agreement(weeks):
    """How often the curve agreed with the score. weeks needs tightness_label and curve_state.

    Returns a dict of counts and rates, plus the base rates to compare against:
    if 40% of all weeks are in backwardation anyway, 45% of tight weeks is barely agreement.
    """
    w = weeks.dropna(subset=["tightness_label", "curve_state"])
    tight, loose = w[w.tightness_label == "tight"], w[w.tightness_label == "loose"]
    back, cont = w[w.curve_state == "backwardation"], w[w.curve_state == "contango"]

    def share(part, whole):
        return len(part) / len(whole) if len(whole) else None

    return {
        "weeks": len(w),
        "tight_weeks": len(tight),
        "loose_weeks": len(loose),
        "tight_in_backwardation": share(tight[tight.curve_state == "backwardation"], tight),
        "loose_in_contango": share(loose[loose.curve_state == "contango"], loose),
        "all_in_backwardation": share(back, w),
        "all_in_contango": share(cont, w),
        "backwardation_scored_tight": share(back[back.tightness_label == "tight"], back),
        "contango_scored_loose": share(cont[cont.tightness_label == "loose"], cont),
        "all_scored_tight": share(tight, w),
        "all_scored_loose": share(loose, w),
        "tight_in_contango": share(tight[tight.curve_state == "contango"], tight),
        "loose_in_backwardation": share(loose[loose.curve_state == "backwardation"], loose),
    }
