"""Write a short Monday summary of every gauge. Expansion item 10.

Run after the weekly updates: .venv/bin/python monday_summary.py
Writes reports/monday_<date>.md (git-ignored) and prints it. Every figure carries its as-of date,
because the sources update on different days. Neutral wording: levels and changes only.
This is a market monitoring and research tool, not betting or trading advice.
"""

import datetime as dt
from pathlib import Path

import pandas as pd

import db

REPORTS = Path(__file__).parent / "reports"


def change(new, old):
    """'+1.2' style change, or 'n/a' when either value is missing."""
    if new is None or old is None or pd.isna(new) or pd.isna(old):
        return "n/a"
    return f"{new - old:+,.2f}"


def daily_latest(con, indicator, back_days=7):
    """Latest value of a daily indicator and the value about `back_days` calendar days earlier."""
    rows = con.execute("SELECT obs_date, value FROM daily_indicator WHERE indicator = ? ORDER BY obs_date",
                       [indicator]).df()
    if rows.empty:
        return None
    last = rows.iloc[-1]
    earlier = rows[rows.obs_date <= last.obs_date - pd.Timedelta(days=back_days)]
    return {"date": last.obs_date, "value": last.value,
            "before": earlier.iloc[-1].value if not earlier.empty else None}


def gather(con):
    s = {}
    w = con.execute("""SELECT week_ending, tightness_score, tightness_label, crude_position, distillate_position,
                              utilization_position, spread, spr_stocks
                       FROM weekly_reading WHERE tightness_score IS NOT NULL ORDER BY week_ending DESC LIMIT 2""").df()
    s["week"], s["prev_week"] = w.iloc[0], w.iloc[1]
    s["cot"] = con.execute("""SELECT report_date, released, spec_net, spec_net_pct_oi,
                                     spec_net - lag(spec_net) OVER (ORDER BY report_date) AS net_change
                              FROM trader_positioning ORDER BY report_date DESC LIMIT 1""").df().iloc[0]
    s["prices"] = con.execute("""PIVOT (SELECT price_date, benchmark, price FROM price_series
                                        WHERE benchmark IN ('WTI', 'Brent')) ON benchmark USING first(price)
                                 ORDER BY price_date DESC LIMIT 1""").df().iloc[0]
    for name in ["OVX", "GPR", "NASDAQ", "UST10Y", "HY_SPREAD"]:
        s[name] = daily_latest(con, name)
    s["gpr_week"] = con.execute("""SELECT avg(value) FROM daily_indicator WHERE indicator = 'GPR'
                                   AND obs_date > (SELECT max(obs_date) FROM daily_indicator WHERE indicator = 'GPR')
                                                  - INTERVAL 7 DAY""").fetchone()[0]
    s["hormuz"] = con.execute("""SELECT max(transit_date) AS last_day,
          avg(tankers) FILTER (WHERE transit_date > (SELECT max(transit_date) FROM chokepoint_transit) - INTERVAL 7 DAY) AS last_7,
          avg(tankers) FILTER (WHERE transit_date < DATE '2026-01-01') AS normal
        FROM chokepoint_transit WHERE facility_id = 'strait-of-hormuz'""").df().iloc[0]
    s["markets"] = con.execute("""SELECT count(DISTINCT market_key) FROM prediction_market WHERE status = 'open'""").fetchone()[0]
    return s


def render(s, today):
    w, p, cot, px, h = s["week"], s["prev_week"], s["cot"], s["prices"], s["hormuz"]

    def line(label, item, fmt, unit=""):
        if item is None:
            return f"- **{label}:** no data"
        return (f"- **{label}:** {item['value']:{fmt}}{unit} on {item['date']:%b %-d} "
                f"(week change {change(item['value'], item['before'])})")

    out = [
        f"# Crude market monitor: Monday read, {today:%B %-d, %Y}",
        "",
        "Market monitoring and research only. Not betting or trading advice. Levels and changes, no forecasts.",
        "",
        "## Physical market (EIA)",
        f"- **US tightness score:** {int(w.tightness_score):+d}, {w.tightness_label} "
        f"(prior week {int(p.tightness_score):+d}), week ending {w.week_ending:%b %-d}. "
        f"Positions in five-year range: crude {w.crude_position:.2f}, distillate {w.distillate_position:.2f}, "
        f"utilization {w.utilization_position:.2f}.",
        f"- **Brent minus WTI:** ${w.spread:,.2f} weekly average (prior week ${p.spread:,.2f}). "
        f"Latest day {px.price_date:%b %-d}: Brent ${px.Brent:,.2f}, WTI ${px.WTI:,.2f}.",
        f"- **Strategic Petroleum Reserve:** {w.spr_stocks / 1000:,.1f} million barrels "
        f"(week change {change(w.spr_stocks / 1000, p.spr_stocks / 1000)}).",
        "",
        "## Global and risk gauges",
        f"- **Hormuz tanker transits (IMF PortWatch):** {h.last_7:.1f} a day over the 7 days to {h.last_day:%b %-d}, "
        f"against {h.normal:.1f} a day on average in 2019 to 2025.",
        f"- **Geopolitical Risk Index:** {s['gpr_week']:.0f} average over the last 7 days (1985 to 2019 = 100).",
        line("Oil volatility (OVX)", s["OVX"], ",.1f"),
        f"- **Large speculators in WTI (CFTC):** net {cot.spec_net:+,.0f} contracts, {cot.spec_net_pct_oi:.1%} of "
        f"open interest (week change {cot.net_change:+,.0f}), positions {cot.report_date:%b %-d}, "
        f"released {cot.released:%b %-d}.",
        f"- **Prediction markets tracked:** {s['markets']} open on Polymarket and Kalshi. "
        f"Unusual activity is reported in aggregate by `unusual_activity.py`.",
        "",
        "## Financial outcomes",
        line("10-year Treasury yield", s["UST10Y"], ".2f", "%"),
        line("High-yield spread", s["HY_SPREAD"], ".2f", " points"),
        line("NASDAQ Composite", s["NASDAQ"], ",.0f"),
        "",
        "Sources: EIA, CFTC, IMF PortWatch, FRED (Federal Reserve Bank of St. Louis; OVX from CBOE, NASDAQ from "
        "Nasdaq, high-yield spread from ICE, used for personal research), Caldara and Iacoviello GPR index, "
        "Polymarket and Kalshi public market data.",
    ]
    return "\n".join(out) + "\n"


def main():
    con = db.connect()
    today = dt.date.today()
    text = render(gather(con), today)
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"monday_{today:%Y-%m-%d}.md"
    path.write_text(text)
    print(text)
    print(f"Saved to {path.relative_to(Path(__file__).parent)}")


if __name__ == "__main__":
    main()
