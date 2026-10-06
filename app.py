"""Streamlit page: US tightness score, Brent minus WTI spread, and five charts.

Run: .venv/bin/streamlit run app.py
Reads crude_monitor.duckdb, so run fetch.py and calculate.py first.
"""

import datetime as dt

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import db
import score

st.set_page_config(page_title="Crude Market Tightness Monitor", layout="wide")

# Chart colors (reference palette: slot 1 blue, its light band step, neutral gray for the average)
LIGHT = {"line": "#2a78d6", "band": "rgba(42,120,214,0.14)", "avg": "#898781",
         "grid": "#e1e0d9", "axis": "#c3c2b7", "text": "#52514e", "surface": "rgba(0,0,0,0)"}
DARK = {"line": "#3987e5", "band": "rgba(57,135,229,0.22)", "avg": "#898781",
        "grid": "#2c2c2a", "axis": "#383835", "text": "#c3c2b7", "surface": "rgba(0,0,0,0)"}
COLORS = DARK if st.context.theme.type == "dark" else LIGHT

INPUT_NAMES = {"crude": "Crude stocks", "distillate": "Distillate stocks", "utilization": "Refinery utilization"}


@st.cache_data(ttl=3600)
def load_gauges():
    """Daily risk, shipping and financial series (local use: some are not licensed for publishing)."""
    con = duckdb.connect(str(db.DB_PATH), read_only=True)
    daily = con.execute("SELECT indicator, obs_date, value FROM daily_indicator").df()
    hormuz = con.execute("""SELECT transit_date AS obs_date, avg(tankers) OVER (ORDER BY transit_date
                                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS value
                            FROM chokepoint_transit WHERE facility_id = 'strait-of-hormuz'""").df()
    cot = con.execute("SELECT released AS obs_date, 100 * spec_net_pct_oi AS value FROM trader_positioning").df()
    con.close()
    frames = [daily, hormuz.assign(indicator="HORMUZ"), cot.assign(indicator="COT")]
    out = pd.concat(frames, ignore_index=True)
    out["obs_date"] = pd.to_datetime(out["obs_date"])
    return out


@st.cache_data(ttl=3600)
def load():
    con = duckdb.connect(str(db.DB_PATH), read_only=True)
    weekly = con.execute("SELECT * FROM weekly_reading ORDER BY week_ending").df()
    prices = con.execute("SELECT * FROM price_series ORDER BY price_date").df()
    con.close()
    weekly["week_ending"] = pd.to_datetime(weekly["week_ending"])
    prices["price_date"] = pd.to_datetime(prices["price_date"])
    return weekly, prices


def points(prefix, position):
    """Points for one input, using the same rule as score.py."""
    return score.utilization_points(position) if prefix == "utilization" else score.stock_points(position)


def change_text(change, fmt):
    """'No change vs prior week' or e.g. '+2.91 vs prior week'."""
    return "No change vs prior week" if round(change, 2) == 0 else f"{fmt.format(change)} vs prior week"


def style(fig, title, unit):
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        height=360, margin=dict(l=10, r=10, t=70, b=10),
        hovermode="x unified", plot_bgcolor=COLORS["surface"], paper_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["axis"], hoverformat="Week ending %b %-d, %Y")
    fig.update_yaxes(title_text=unit, gridcolor=COLORS["grid"], gridwidth=1, zeroline=False)
    return fig


def band_chart(df, value_col, prefix, title, unit, scale=1.0):
    """The weekly value against its five-year range (shaded) and five-year average (gray)."""
    x = df["week_ending"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df[f"{prefix}_high"] / scale, mode="lines", line=dict(width=0),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=df[f"{prefix}_low"] / scale, mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor=COLORS["band"], name="Five-year range",
                             customdata=df[f"{prefix}_high"] / scale,
                             hovertemplate="Range %{y:,.1f} to %{customdata:,.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=df[f"{prefix}_avg"] / scale, mode="lines",
                             line=dict(color=COLORS["avg"], width=1.5), name="Five-year average",
                             hovertemplate="Average %{y:,.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=df[value_col] / scale, mode="lines",
                             line=dict(color=COLORS["line"], width=2), name="Actual",
                             hovertemplate="Actual %{y:,.1f}<extra></extra>"))
    return style(fig, title, unit)


def line_chart(df, x_col, y_col, title, unit, name, fmt):
    fig = go.Figure(go.Scatter(x=df[x_col], y=df[y_col], mode="lines", name=name,
                               line=dict(color=COLORS["line"], width=2),
                               hovertemplate=f"{name} %{{y:{fmt}}}<extra></extra>"))
    return style(fig, title, unit)


# ---------------------------------------------------------------- data
weekly, prices = load()
scored = weekly.dropna(subset=["tightness_score"])
if scored.empty:
    st.error("No scored weeks yet. Run fetch.py and then calculate.py.")
    st.stop()
latest = scored.iloc[-1]
previous = scored.iloc[-2]
release = latest["week_ending"] + pd.Timedelta(days=5)  # usually the Wednesday after

# ---------------------------------------------------------------- header
st.title("Crude Market Tightness Monitor")
st.caption("When is the oil market tight, and how do prices react when supply is disrupted while it is tight?")
st.markdown(f"**Week ending {latest.week_ending:%B %-d, %Y}** · EIA data released about {release:%B %-d}")

# ---------------------------------------------------------------- the two gauges
left, right = st.columns(2, border=True)
with left:
    score_value = int(latest.tightness_score)
    st.metric("US tightness score (−3 loose to +3 tight)",
              f"{score_value:+d} · {latest.tightness_label.capitalize()}",
              delta=change_text(score_value - int(previous.tightness_score), "{:+d}"),
              delta_color="off", delta_arrow="off")
    st.caption("Crude stocks, distillate stocks and refinery utilization, each compared with the same "
               "week in the prior five years, with 2020 left out of the range. US data only.")
with right:
    st.metric("Brent minus WTI spread (weekly average)",
              f"${latest.spread:,.2f} per barrel",
              delta=change_text(latest.spread - previous.spread, "{:+,.2f}"),
              delta_color="off", delta_arrow="off")
    spot = prices.pivot(index="price_date", columns="benchmark", values="price")[["Brent", "WTI"]]
    last_day = spot.dropna().iloc[-1]
    st.caption(f"Global gauge. Latest day {last_day.name:%B %-d}: Brent \\${last_day.Brent:,.2f}, "
               f"WTI \\${last_day.WTI:,.2f}. A wide gap means the world is short while the US is better supplied.")

# How this week's score adds up
rows = []
for prefix, name in INPUT_NAMES.items():
    pos = latest[f"{prefix}_position"]
    rows.append({
        "Input": name,
        "Tight when": "High" if prefix == "utilization" else "Low",
        "Position in five-year range": round(pos, 2),
        "Versus five-year average": f"{latest[f'{prefix}_pct_vs_avg']:+.1%}",
        "Points": f"{points(prefix, pos):+d}",
    })
st.markdown("**How this week's score adds up.** Position is 0 at the five-year low and 1 at the high. "
            "Stocks score +1 below 0.25 and −1 above 0.75; utilization the other way round.")
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ---------------------------------------------------------------- charts
st.subheader("Charts")
span = st.segmented_control("Time range", ["2 years", "5 years", "10 years", "Since 1995"],
                            default="5 years")
years = {"2 years": 2, "5 years": 5, "10 years": 10}.get(span)
start = latest.week_ending - pd.DateOffset(years=years) if years else pd.Timestamp("1995-11-01")
view = weekly[weekly["week_ending"] >= start]

def show(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


c1, c2 = st.columns(2)
with c1:
    show(band_chart(view, "crude_stocks", "crude", "Crude stocks excluding SPR",
                    "Million barrels", scale=1000))
with c2:
    show(band_chart(view, "distillate_stocks", "distillate", "Distillate stocks (diesel and heating oil)",
                    "Million barrels", scale=1000))
c3, c4 = st.columns(2)
with c3:
    show(band_chart(view, "utilization", "utilization", "Refinery utilization",
                    "Percent of operable capacity"))
with c4:
    show(line_chart(view, "week_ending", "spread", "Brent minus WTI spread (weekly average)",
                    "Dollars per barrel", "Spread", "$,.2f"))
show(line_chart(view.assign(production=view["production"] / 1000), "week_ending", "production",
                "US crude production (context only, not in the score)",
                "Million barrels per day", "Production", ",.2f"))

# ---------------------------------------------------------------- risk, shipping and financial gauges
st.subheader("Risk, shipping and financial gauges")
st.caption("Local research view. OVX (CBOE), the NASDAQ Composite (Nasdaq) and the ICE BofA high-yield spread are "
           "licensed for personal use only and are not published in the public showcase. The high-yield spread "
           "is available on FRED only from October 2023.")
gauges = load_gauges()
gview = gauges[gauges["obs_date"] >= start]
GAUGES = [
    ("HORMUZ", "Hormuz tanker transits a day, 7-day average (IMF PortWatch)", "Ships a day", ",.1f"),
    ("GPR", "Geopolitical Risk Index (Caldara and Iacoviello)", "1985-2019 = 100", ",.0f"),
    ("OVX", "Oil volatility index, OVX (CBOE via FRED)", "Index", ",.1f"),
    ("COT", "Large speculators' net position in WTI, share of open interest (CFTC)", "Percent", ",.1f"),
    ("UST10Y", "10-year Treasury yield (Federal Reserve via FRED)", "Percent", ",.2f"),
    ("HY_SPREAD", "ICE BofA US high-yield spread (via FRED)", "Percentage points", ",.2f"),
    ("NASDAQ", "NASDAQ Composite (via FRED)", "Index", ",.0f"),
]
for i in range(0, len(GAUGES), 2):
    cols = st.columns(2)
    for col, (key, title, unit, fmt) in zip(cols, GAUGES[i:i + 2]):
        with col:
            series = gview[gview["indicator"] == key].sort_values("obs_date")
            if series.empty:
                st.info(f"No data yet for {title}. Run the matching loader script.")
            else:
                show(line_chart(series, "obs_date", "value", title, unit, key, fmt))

# ---------------------------------------------------------------- table view
with st.expander("Table view of the weekly data"):
    table = view[["week_ending", "crude_stocks", "distillate_stocks", "utilization", "production", "exports",
                  "crude_position", "distillate_position", "utilization_position",
                  "tightness_score", "tightness_label", "spread"]].sort_values("week_ending", ascending=False)
    st.dataframe(table, hide_index=True, width="stretch")

st.caption("Source: U.S. Energy Information Administration. Stocks in thousand barrels in the table, "
           "production and exports in thousand barrels per day. The score measures US conditions only. "
           "This is a market monitoring and research tool, not betting or trading advice. "
           "It is a student project and is not investment advice.")
