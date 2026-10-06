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
- Commit to git after each working step with a clear message, then push to GitHub after every commit (user instruction, Oct 5, 2026). Before pushing, confirm `.env` and the database are not tracked.
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
6. Abnormal years (`seasonal.ABNORMAL_YEARS` = 2020, 2026) are never used as comparison values. The range reaches one year further back to keep five values. Whole years only, marked in advance, never single weeks. The user decided this default (dropping 2020) before the backtest was run. Do not change the list based on results. `compare_2020.py` shows the version that keeps 2020.
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

## Futures curve (expansion item 2, history only)

- **No free live source found.** EIA `petroleum/pri/fut` (`RCLC1`, `RCLC4`) ends April 5, 2024. FRED has spot prices only. CME licenses its data, and its site could not be reached to confirm terms. Do not scrape exchange sites or use unofficial feeds.
- `futures.py`: weekly average of (contract 1 − contract 4) / contract 4. Backwardation above +1%, contango below −1%, otherwise flat. The band was fixed in advance, and a sign-only version is also reported.
- Stored in `price_series` as `WTI future 1` and `WTI future 4`, and on `weekly_reading` as `futures_gap`, `futures_gap_pct` and `curve_state`. Never shown as a live gauge on the page.
- Any code using spot prices must select the `Brent` and `WTI` columns before `dropna()`, or the futures ending in 2024 will remove later days.
- `check_routes.py` checks the latest date, not just the listing. Series in `HISTORY_ONLY` are expected to be old.

## Prediction markets (expansion item 3)

- Sources confirmed live on Oct 5, 2026, with no key. Polymarket: `gamma-api.polymarket.com` (`/public-search`, `/markets`) and `clob.polymarket.com/prices-history` (daily prices; documented limits of 300 to 1,000 requests per 10 s). Kalshi: `api.elections.kalshi.com/trade-api/v2` (`/series`, `/markets`, `/series/{s}/markets/{t}/candlesticks`; docs say market data is public).
- Selection rule in `prediction_markets.py`, fixed before seeing results. Topic is gulf_conflict or oil_price by title regex, with exclusions. Total volume of at least 10,000. Closes on or after Jan 1, 2026. Open at least 7 days. Kalshi daily, hourly and 15-minute series are skipped.
- Tables: `prediction_market` (one row per market) and `market_reading` (one row per market per day). **Add or update only, never delete**, so closed markets keep their history. Updates use COALESCE so a missing value never erases a stored one.
- Daily volume: Kalshi candles give it for the full history. Polymarket gives only all-time totals, so each run stores `total_volume` and daily Polymarket volume exists only from the first run onward (Oct 5, 2026).
- Privacy: only the fields in `fetch_markets.MARKET_COLUMNS` and `READING_COLUMNS` are stored. Never store or request trade-level or account data (Polymarket's data-api trades include wallets).

## Dates for prediction markets

- All `market_reading` dates are US Eastern days: a reading dated D is the market as of the end of D in New York. Kalshi candles are filed under the Eastern day one second before their end stamp. Polymarket is fetched hourly in 14-day ranges and closed at Eastern midnight, because its daily points are 00:00 UTC snapshots.
- Each day appears once per market: today's snapshot is merged into today's history row. Re-runs fetch only from 3 days before a market's last saved date. A closed market already saved through its close date is skipped.

## Unusual activity (expansion item 4)

- Rules in `activity.py`, fixed before results. Market-day flag: odds move ≥ max(0.10, 4 × median) or volume ≥ max(1,000, 5 × median), against the prior 30 days with at least 14 days of history. The last 2 days before close are skipped. Unusual topic-day: flagged share in the top 5% of days that have at least 20 active markets. Event window: day −4 to day −2 (day −1 skipped as a time-zone buffer), compared with the base rate.
- Events come only from `disruption_event` rows WHERE `hand_checked`. Columns `hand_checked` (default false) and `episode` are added by `db.UPGRADES`. War episode label: `iran_war_2026`.
- Report counts and rates only. Never list markets as suspicious, and never mention accounts.

## Trader positioning (expansion item 5)

- Source confirmed Oct 5, 2026: CFTC Public Reporting Environment, Legacy Futures Only (`publicreporting.cftc.gov/resource/6dca-aqww.json`), no key. Socrata throttles unauthenticated heavy use; we make one request. WTI is code `067651`, continuous from 1986.
- Large speculators = noncommercial. `spec_net` = long − short. `spec_net_pct_oi` = net / open interest.
- Timing: `report_date` is the measurement day (usually Tuesday). `released` is the first Friday at least 2 days later. Timing tests must use `released`. `week_ending` is the EIA week holding the measurement day.

## FRED and copyright (items 6, 7, 10)

- FRED's terms prohibit scraping, so use the official FRED API with `FRED_API_KEY` in `.env`, not the `fredgraph.csv` links.
- Third-party series on FRED are for personal use only unless the owner grants permission. `fred.INDICATORS[...]["publishable"]` records this per series. OVX (CBOE), NASDAQ (Nasdaq) and the ICE BofA high-yield spread are not publishable. The 10-year Treasury yield is public domain. **The item 12 showcase may only publish series marked publishable**; the user decides the rest at item 12.
- `daily_indicator` (indicator, obs_date, value) holds all daily indicator series.
- GPR (`gpr.py`): daily Stata file from matteoiacoviello.com, CC BY, so **publishable with credit**. It is calendar days, updated Mondays. Indicators are GPR, GPR_ACTS and GPR_THREATS. A day-D value reflects articles published on D.

## AI news reader (expansion item 8)

- **Default path, no API key (the user's decision, Oct 5, 2026).** The user pastes an article in a Claude Code session. Claude writes an `Extraction` JSON to `staging/<name>.json` (git-ignored) following the schema and the SYSTEM rules in `news_reader.py`, then runs `news_reader.py stage --extraction ... --url ... --publisher ...`. Never estimate barrels; quotes must be verbatim and 25 words or fewer.
- Optional API path, kept but unused: `ANTHROPIC_API_KEY`, `claude-opus-5-5` via `client.beta.messages.parse` with `fallbacks="default"` (beta `server-side-fallback-2026-07-01`). `anthropic` is imported only on that path.
- `staged_event` is the only table the reader writes on its own. `approve()` is the only path into `disruption_event`, `facility` and `source`, and needs an explicit "yes". Rows default to `hand_checked = FALSE`; `--checked` means the user verified them.
- Never store article text, only quotes of 25 words or fewer. The vocabulary matches EVENTS_STARTER.csv. Wording is neutral.
- `anthropic` is an added dependency beyond the brief's tool list, approved by the user's choice of an API key.

## Global side (expansion item 9)

- SPR: EIA `WCSSTUS1` on `petroleum/stoc/wstk`, confirmed live, stored as `weekly_reading.spr_stocks`. Context only, not in the score.
- Chokepoints: IMF PortWatch public ArcGIS (`Daily_Chokepoints_Data`, `PortWatch_chokepoints_database`), no key. IMF terms allow publishing with attribution, so it is **publishable**. Six chokepoints are stored as `facility` rows with latitude and longitude; daily counts are in `chokepoint_transit`.

## Pipeline

`check_routes.py` (confirm routes) → `fetch.py` (EIA to DuckDB) → `calculate.py` (`seasonal.py`, `score.py`) → `app.py` (Streamlit). Tests: `.venv/bin/python -m unittest discover -s tests -t .`

## Open items

- Done: item 1 (drop-2020 default and backtest), item 2 (futures curve, history only), item 3 (prediction markets), item 4 (unusual activity; event comparison waits for hand-checked events), item 5 (CFTC positioning), item 6 (OVX via the FRED API), item 7 (daily GPR index), item 8 (AI news reader, no-key session path; demo staged row 1, Abqaiq 2019, left pending), item 9 (chokepoints and SPR).
- Next: 10, 11 Iran war episode timeline, 12 interactive showcase (show plan and layout first).
- Item 9: the global side. Tanker transits through the Strait of Hormuz and other chokepoints, if a free public source exists, plus the US strategic petroleum reserve level.
- Item 10: three daily outcome series for the event study (a NASDAQ index, the 10-year Treasury yield, a high-yield corporate bond spread), then a script that writes a short Monday summary of all gauges.
- After item 10: update PROJECT_BRIEF.md so version 2 is one event study with two questions: how oil prices reacted to each disruption, and how tech funding costs reacted. Drop the scenario calculator and the network graph. Keep the map, because the item 12 showcase uses it.
- **Do not start the event study itself.** The user must hand-check the events table first.
- Item 11 rules: every row needs a news agency or official source, and Wikipedia is a pointer only. Where sources disagree on a date, record both and flag it. Every row is "not hand-checked" until the user checks it, and nothing downstream may use an unchecked row. The war is one episode with sub-events, and every result is reported with and without it.
- Item 12 rules: static page in docs/ for GitHub Pages, reading a JSON file from export_showcase.py, with no key in the browser. Use hand-checked events only. Say "moved together, not caused". Not trading advice. Credit EIA and FRED. Works on a phone, in light and dark mode, with one accent colour.

## Expansion rules (added Oct 5, 2026)

- Teaching mode ended Oct 5, 2026 at the user's request: no more teaching questions. Still one item at a time: show the result in plain language, run the tests, commit, push, and wait for approval.
- Confirm every new data source on the live service (route or ID, access rules, whether a key is needed). If it is unavailable or paid, say so and skip it.
- Each new object type gets its own table, and ONTOLOGY.md, CLAUDE.md and the README are updated as items land. Every calculation gets tests.
- This is a market monitoring and research tool, not betting or trading advice. The README and the app must both say so. Public data only.
- Prediction market activity is reported in aggregate only. Never name, link to, or accuse an individual account or wallet.
- Neutral wording about the conflict: dates, volumes and prices only.
