# Ontology

The ontology is the list of things this project tracks, what we record about each one, and how they connect. It comes from section 5 of PROJECT_BRIEF.md. Each object type gets its own DuckDB table.

## Object types

| Object | DuckDB table | Key properties | Links to |
|---|---|---|---|
| Facility | `facility` | Name, type, country, barrels per day | Disruption events |
| Disruption event | `disruption_event` | Date, day zero, cause, barrels per day offline, physical loss (yes or no) | Facility, sources, weekly reading |
| Price series | `price_series` | Benchmark (WTI, Brent), date, price | Disruption events (through price reactions) |
| Weekly reading | `weekly_reading` | Week ending, crude stocks, distillate stocks, utilization, production, exports, tightness score, spread | Disruption events in that week |
| Source | `source` | Publisher, link, date | Disruption events |

## Links

- A **facility** can have many **disruption events**.
- A **disruption event** can cite many **sources**.
- A **disruption event** falls in one **weekly reading**: the week whose week-ending date it falls in.
- A **disruption event** links to the **price series** through its price reaction around day zero (version 2).

## Calculated properties

These are computed from other data, not fetched.

- **Tightness score** on each weekly reading. Ranges from −3 to +3 and is labelled tight, normal or loose. See METHODS.md section 2.
- **Brent minus WTI spread** on each weekly reading. Calculated from the price series.

## Action

- **Flag hedge review.** Fires when the weekly score is **tight** and a new disruption event is logged, and alerts the fuel buyer. It needs disruption events, so it arrives in version 2.

## What version 1 fills

| Table | Version 1 |
|---|---|
| `weekly_reading` | Filled from EIA, with score and spread calculated |
| `price_series` | Filled with daily WTI and Brent from EIA |
| `facility`, `disruption_event`, `source` | Created empty, filled in version 2 |
