# Ontology

The ontology is the list of things this project tracks, what we record about each one, and how they connect. It comes from section 5 of PROJECT_BRIEF.md. Each object type gets its own DuckDB table.

## Object types

| Object | DuckDB table | Key properties | Links to |
|---|---|---|---|
| Facility | `facility` | Name, type, country, barrels per day, latitude, longitude. Includes six oil chokepoints (type 'tanker or shipping lane') | Disruption events, chokepoint transits |
| Disruption event | `disruption_event` | Date, day zero, cause, barrels per day offline, physical loss (yes or no), hand-checked (yes or no), episode. Loaded by `events.py` from EVENTS_STARTER.csv and data/iran_war_2026.csv, plus approved news-reader rows | Facility, sources, weekly reading |
| Price series | `price_series` | Benchmark (WTI, Brent, WTI future 1, WTI future 4), date, price | Disruption events (through price reactions) |
| Weekly reading | `weekly_reading` | Week ending, crude stocks, distillate stocks, utilization, production, exports, SPR stocks, tightness score, spread | Disruption events in that week |
| Source | `source` | Publisher, link, published date, accessed date, terms note, publishable flag, kind (dataset or citation) | Disruption events (citations); every data series (dataset rows from `sources.py`) |
| Retail fuel price | `retail_fuel_price` | Product (gasoline, diesel), week date, price in $/gallon (EIA) | Weekly reading by date |
| Prediction market | `prediction_market` | Platform (Polymarket, Kalshi), question, outcome, topic (gulf_conflict, oil_price), open and close dates, status, result, all-time volume | Market readings; disruption events by date (item 4) |
| Trader positioning | `trader_positioning` | Report date (Tuesday measured), released (Friday published), open interest, large speculator long and short, commercial and small trader positions, net speculative position; from June 2006 also managed money, producer/merchant and swap dealer positions (disaggregated report) | Weekly reading (same week) |
| Chokepoint transit | `chokepoint_transit` | Facility (chokepoint), date, tankers, all ships, tanker and total deadweight tons (IMF PortWatch) | Facility |
| Spike | `spike` | Benchmark, kind (daily, surge, crash, drawdown, spread), rule, direction, start, extreme and end dates and prices, size in dollars and percent, non-positive flag, recovery date; cause note, source ids and hand-checked status (M3) | Price series (derived from it); disruption events and sources (M3) |
| Staged event | `staged_event` | A disruption event proposed by the AI news reader: extracted fields, evidence quotes, model, status (pending, approved, rejected) | Becomes a disruption event, with facility and source, only when the user approves it |
| Daily indicator | `daily_indicator` | Indicator name (OVX, GPR, GPR_ACTS, GPR_THREATS, ...), date, value. Owner and publishing terms are recorded in `fred.INDICATORS` and `gpr.OWNER` / `gpr.PUBLISHABLE` | Price series and disruption events by date |
| Market reading | `market_reading` | Market, date, price (implied chance, 0 to 1), volume that day, all-time volume at snapshot | Prediction market |

## Links

- A **facility** can have many **disruption events**.
- A **disruption event** can cite many **sources**.
- A **disruption event** falls in one **weekly reading**: the week whose week-ending date it falls in.
- A **disruption event** links to the **price series** through its price reaction around day zero (version 2).

- A **prediction market** has many **market readings**, one per day.
- A **trader positioning** report falls in one **weekly reading**: the EIA week that holds its measurement day.
- Prediction markets link to **disruption events** by date only, through the unusual-activity check in item 4. They are never linked to any account or wallet.

## Calculated properties

These are computed from other data, not fetched.

- **Tightness score** on each weekly reading. Ranges from −3 to +3 and is labelled tight, normal or loose. See METHODS.md section 2.
- **Net speculative position** (long − short, and as a share of open interest) on each trader positioning report.
- **Brent minus WTI spread** on each weekly reading. Calculated from the price series.
- **Futures curve gap and curve state** on each weekly reading, **history only, through April 5, 2024**. The gap is contract 1 minus contract 4 as a share of contract 4. The state is backwardation (tight), contango (loose) or flat. No free live source exists, so these are empty after April 2024.

## Price series benchmarks

`price_series` holds four daily series: `WTI` and `Brent` (spot, live), and `WTI future 1` and `WTI future 4` (futures, history only, ending April 5, 2024). They share one table because each is the same kind of object: a benchmark, a date and a price. Code that needs only spot prices must select the `WTI` and `Brent` columns before dropping incomplete days.

## Action

- **Flag hedge review.** Fires when the weekly score is **tight** and a new disruption event is logged, and alerts the fuel buyer. It needs disruption events, so it arrives in version 2.

## What version 1 fills

| Table | Version 1 |
|---|---|
| `weekly_reading` | Filled from EIA, with score and spread calculated |
| `price_series` | Filled with daily WTI and Brent spot prices, plus WTI futures contracts 1 and 4 through April 2024 |
| `facility`, `disruption_event`, `source` | Created empty, filled in version 2 |
| `prediction_market`, `market_reading` | Filled by `fetch_markets.py` (expansion item 3). Add or update only, never delete |
