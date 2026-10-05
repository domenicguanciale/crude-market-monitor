# CLAUDE.md

Crude Market Tightness Monitor. Question: when is the oil market tight, and how do prices react when supply is disrupted while it is tight? The user is a fuel buyer deciding when to lock in a contract or review a hedge. The builder is a finance student learning to code, so explain everything in plain language.

Full specs: PROJECT_BRIEF.md (plan), DATA_SPEC.md (series IDs, API), METHODS.md (math). Read them when in doubt; do not guess.

## Working rules

- Work in small steps. After each step, explain what the code does in plain language and wait for the user.
- Use only the tools listed below. Reading `.env` is done with plain Python, and tests use the built-in `unittest`.
- Store data in DuckDB with one table per object type (see the ontology).
- Read the EIA API key from `.env` (`EIA_API_KEY=...`). Never print it, log it, or commit it. `.env` is in `.gitignore`.
- Routes in DATA_SPEC.md marked UNVERIFIED must be confirmed against the live API before use. Never guess a route or series ID.
- Follow METHODS.md for the five-year comparison and the score. If a method seems wrong, tell the user before changing it.
- Commit to git after each working step with a clear message.
- README must include a Mermaid diagram of the ontology, the question, the method, and the limits from METHODS.md section 8.
- Stay neutral about 2026 events: record dates, volumes, and prices only. Measure reactions; never claim to predict.
- Credit "U.S. Energy Information Administration" as the data source. Do not use the EIA logo.

## Tools (PROJECT_BRIEF.md section 8)

| Job | Tool |
|---|---|
| Language | Python |
| Storage | DuckDB, one table per object type |
| Data handling | pandas, requests |
| Charts | Plotly |
| Web page | Streamlit |
| Ontology diagram in README | Mermaid |
| Network graph (version 2) | pyvis |
| Map (version 2) | pydeck or Folium |

## Ontology (full version in ONTOLOGY.md)

| Object | Table | Key properties | Links to |
|---|---|---|---|
| Facility | `facility` | name, type, country, barrels per day | disruption events |
| Disruption event | `disruption_event` | date, day zero, cause, bpd offline, physical loss y/n | facility, sources, weekly reading |
| Price series | `price_series` | benchmark (WTI, Brent), date, price | disruption events via price reactions |
| Weekly reading | `weekly_reading` | week ending, crude stocks, distillate stocks, utilization, production, exports, tightness score, spread | disruption events in that week |
| Source | `source` | publisher, link, date | disruption events |

- Calculated properties: tightness score and Brent minus WTI spread, on each weekly reading.
- Action: "Flag hedge review" fires when the score is tight and a new disruption is logged (version 2).

## Data (DATA_SPEC.md)

Series: `RWTC` (WTI spot), `RBRTE` (Brent spot), `WCESTUS1` (crude stocks ex-SPR, thousand bbl), `WDISTUS1` (distillate stocks, thousand bbl), `WPULEUS3` (refinery utilization, %), `WCRFPUS2` (production, thousand bpd), `WCREXUS2` (exports, thousand bpd). Weeks end Friday; data is released the following Wednesday.

## Five-year comparison (METHODS.md section 1)

1. Week number = ISO week of the week-ending (Friday) date.
2. For each reading, take the values at the same week number in the **prior five calendar years**. The current year is excluded.
3. Compute the five-year low, high and average.
4. `position = (value - low) / (high - low)` gives 0 at the low and 1 at the high. It can fall outside 0 to 1.
   `pct_vs_avg = (value - average) / average`
5. Week 53 is compared with week 52 of the prior years.
6. 2020 and 2026 are kept in the range by default. The README says so. An optional alternative drops 2020.
7. Do not use a z-score, because five values are too few for a reliable standard deviation.

## Tightness score (METHODS.md section 2)

- Inputs: crude stocks, distillate stocks, refinery utilization. **Price is excluded** because it would make the result circular. **Production is excluded** because its direction is ambiguous; it is shown as a context chart only.
- Points from each input's `position`:
  - Stocks (crude, distillate): +1 if position < 0.25, −1 if > 0.75, otherwise 0.
  - Utilization: +1 if position > 0.75, −1 if < 0.25, otherwise 0.
- Score = sum, from −3 to +3. Label: **tight** if ≥ +2, **loose** if ≤ −2, otherwise **normal**.
- Weights are equal. Do not tune them.
- Label the score "US tightness". Always show the **Brent minus WTI spread** next to it as a second, global gauge.
- Weekly spread = average of daily Brent minus WTI over the Saturday-to-Friday week, counting only days with both prices. The user chose this over the Friday close.

## Pipeline

`check_routes.py` (confirm routes) → `fetch.py` (EIA to DuckDB) → `calculate.py` (`seasonal.py`, `score.py`) → `app.py` (Streamlit). Tests: `.venv/bin/python -m unittest discover -s tests -t .`

## Open items

- METHODS.md alternative: show the score with 2020 dropped from the five-year range. 2022 and 2025 score tight in most weeks, partly because 2020 widens the range. Not yet built.
