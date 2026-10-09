# 3D view

Page: `docs/3d.html`. Data: `docs/data/viz3d.js`, written by `export_3d.py`. Code: `docs/js/` (ES modules). The world flows data, `docs/data/flows.json`, is fetched only when that view first opens. One shared time state drives five views, on one time axis from January 2, 1986 to the latest data. The page opens in the price terrain on February 28, 2026, the start of the 2026 Strait of Hormuz disruption, with the whole price history behind it.

| View | What it shows | Data |
|---|---|---|
| Price terrain (M6) | Brent (back) and WTI (front) as walls that run through time. Top edge = daily spot price. Colour = that benchmark's 20-day realized volatility, in sevenths of all trading days. WTI's wall drops below the floor on April 20, 2020. The camera follows the date. Pins mark every spike in the catalog (episodes by default, one-day moves on request); hover for dates, size and rule, click to jump there | `price_series`, `spike`, `RV20_*` in `daily_indicator` |
| Globe | A pillar at each of six chokepoints. Height is tankers per day (7-day average). A ring marks that lane's own 2019 to 2025 median. Before January 1, 2019 the pillars say "no data" | IMF PortWatch via `chokepoint_transit` |
| Skyline | One bar per week, years 1986 (back) to today (front), weeks of the year across. Weeks after the selected date are faded. Three measures on the same grid (M6): the tightness score (-3 loose to +3 tight, from November 1995, with the 2020 switch), 20-day volatility on the week's last trading day, or the week's average price, for Brent or WTI. Volatility and price colours split all weeks into sevenths | `weekly_reading` scored twice with `compare_2020.scores`; `price_series` and `RV20_*` |
| Hormuz ships | A map of the Gulf with the coastline and one moving ship for each daily tanker transit. No ships before 2019, and the note says why. Facility pins appear only for facilities tied to hand-checked events (none yet). Hover the strait for the measured count | `chokepoint_transit` and `facility` |
| World flows (M6) | A globe with a column on each producing country (crude production, thousand b/d, Tier B) coloured by the change from its 2025 monthly average, solid arcs for US crude imports by origin (Tier A), and the chokepoint pillars. Filters: region, Tier A, Tier B. A "who sold, who bought" table lists the top 10 each way for the month. No Tier C | `production_by_country`, `trade_flow` (tier A only), `country` |

The readout panel and the two strips under the canvas show Brent, WTI, the spread, the 10-year yield, the Geopolitical Risk Index and tanker counts for the selected date. The URL hash (`#v=hz&d=2026-03-25&k=1`) holds the view, the date and the 2020 switch, so a link opens where you left it. Any value the data does not have for a date (prices before Brent starts in 1987, scores before November 1995, tanker counts before 2019) shows as "n/a", never as an estimate.

## The 2D dashboard (M7)

Below the 3D stage, `docs/js/dash/dashboard.js` draws eight Plotly charts that read the same shared date: a vertical line marks it, and clicking a chart moves it. Plotly (the same pinned version as `index.html`) and `docs/data/dash.json` load only when the dashboard nears the screen; charts off screen catch up when they scroll in.

| Panel | What it shows | Data |
|---|---|---|
| Headline strip | Latest US tightness score, Brent minus WTI, Brent volatility and its rank, Hormuz traffic share, each with its as-of date | `viz3d.js` |
| Prices | Brent and WTI daily spot, log toggle (which hides the negative print, and says so), rule-detected surges and crashes, the zero line, the 2026 disruption shaded | `price_series`, `spike` |
| Volatility | Brent 20-day and 60-day realized volatility, each ranked against all trading days since 1987 | `RV20_BRENT`, `RV60_BRENT` |
| Spread and curve | Daily Brent minus WTI, and weekly WTI contract 1 against contract 4 (history only, ends April 5, 2024) | `price_series`, `weekly_reading.futures_gap_pct`, `curve_state` |
| Shipping | Tankers at the six chokepoints as a share of each lane's 2019 to 2025 median | `chokepoint_transit` |
| Sellers and buyers | Crude production and US imports by region group, monthly, stacked; the months from March 2026 shaded | `production_by_country`, `trade_flow` (tier A) |
| Inventories and policy | Commercial crude, distillates or refinery use against the five-year range and average; the SPR as context | `weekly_reading` |
| Positioning | Managed money (from June 2006) and commercial net positions in WTI futures, as a share of open interest | `trader_positioning` |
| Money | 10-year Treasury yield, broad dollar index, US retail gasoline and diesel | `daily_indicator`, `retail_fuel_price` |
| Spike catalog | All 445 rule-detected spikes, sortable, with rule, hand-check status and sources (only once checked). A date opens the 3D price terrain there | `spike` |

Each chart has a one-sentence summary for the selected date (also its screen-reader label), its source, and a CSV download of the data it plots. CSV files start with two `#` lines (source and a not-advice note), so read them with `pandas.read_csv(path, comment="#")`. A range selector shows all years, since 2019, the 2026 disruption, or two years around the date. Colours are colour-blind safe (Okabe-Ito, blue and orange) and every second series also differs in line style.

## How the code is laid out (M5)

| File | Job |
|---|---|
| `docs/js/state.js` | The one shared state: date, playing, speed, view, skyline measure, 2020 switch. Views subscribe to it and never keep their own copy of the date, so they cannot disagree. Also the URL hash and deterministic playback (`advance`). Pure functions, no drawing |
| `docs/js/data.js` | Reads `viz3d.js`. Each daily series is stored compactly as `{s: first day, v: values}` (format 2). `lastVal` carries a value forward at most 7 days, so a stale number never looks current |
| `docs/js/scenes/price.js`, `skyline.js`, `globe.js`, `hormuz.js`, `flows.js` | One file per view. Each returns the same small interface: camera, legend, caption, `explain()` for the "What am I looking at?" box, `update(state)`, `pick` for hover, `probe` for the tests, and a text description for screen readers. The price terrain also has `follow` (the camera travels with the date) and `select` (a clicked pin jumps the date) |
| `docs/js/scenes/earth.js` | The dotted Earth and the chokepoint pillars, shared by the globe and world flows |
| `docs/js/dash/dashboard.js` | The 2D dashboard, headline strip and spike table (M7) |
| `docs/js/main.js` | Builds the renderer, wires the buttons and slider to the state, and draws only when something changed |

Playback speeds are 14, 35, 120 or 365 days a second. Jump buttons go to 1986, 2019 (PortWatch starts), the 2026 disruption, the 2026 Hormuz low, and today. Playback pauses when the tab is hidden.

## Run it

```bash
.venv/bin/python export_3d.py          # after fetch.py and calculate.py
.venv/bin/python tools/check_lanes.py  # confirms every ship lane stays in open water
.venv/bin/python -m http.server 8503 -d docs   # then open http://localhost:8503/3d.html
```

The page uses ES modules, which browsers refuse to load from a `file://` address, so open it through a local server (above) or on GitHub Pages.

`docs/index.html` links to the 3D page.

`Crude_Market_Monitor_3D.html` is the older single-file version from before M5, with the data inlined. It is git-ignored because no script regenerates it, so it is stale. The page loads Three.js 0.160.0 from the jsDelivr CDN, so it needs internet.

## Tests

`tests/browser/test_pages.py` runs both public pages in headless Chromium (Playwright): no console errors in light and dark mode at desktop and 390 px phone width, no sideways scroll, a non-blank canvas in all five views, a hover tooltip with its source in every view, a clicked spike pin jumping the date, flows.json loading only when its view opens, every dashboard panel drawing with a sentence that matches the database (price, crude stocks, the positioning report and its release date, April 2026 US imports), the dashboard cursor following the date, CSV downloads with a source line, the spike table opening the 3D view, readouts (prices, score, volatility and its rank) equal to the database on fixed dates (2008-07-03, 2020-04-21, 2026-04-17), "n/a" before each series starts, and the state module's clamping, hash round trip and deterministic playback. `QA_SHOTS=1` saves screenshots to `docs/qa/`. The tests skip if Playwright is not installed.

## Limits to state if asked

- **Ship positions are schematic.** The database has daily counts per chokepoint, not vessel tracks. The count of ships drawn is real (Hormuz 7-day average, rounded). The lanes are hand-placed waypoints checked against the coastline, and the split between lanes and between directions is a display choice.
- **Facility pins wait for hand-checking.** The facility rows came from the AI-drafted event tables, so `export_3d.py` exports a pin only when a hand-checked event points to it. Coordinates are approximate. The page shows names and places only, never events.
- **Ships have one colour.** The data has no direction or origin per ship, so neither is shown. Which route a ship is drawn on is a display weight, stated on the page.
- **The readout's Brent minus WTI is daily.** The tightness section uses the weekly average, as in the main project.
- **PortWatch counts come from satellite ship signals** and miss ships that switch them off.
- **The skyline is US data only.** The Brent minus WTI spread sits beside it for that reason.
- **Spike pins are found by rules, not judgement.** A pin gives dates, prices, size and the rule. An explanation appears only once the user has hand-checked it; none has been yet. Spikes that rest on the unconfirmed Brent print of October 2, 2026 are tagged.
- **World flows are measured only.** Production is not exports, and only US imports by origin are published in a source the page may republish. Seven small producers have no map point and are left off. Country data starts in January 2010 and lags by a few months; the page says which month it shows.
- **The skyline's volatility and price rows use EIA spot prices.** Brent starts in May 1987, so earlier Brent rows are empty.
- **Moves together, not causes.** The page puts different sources on one time axis. It does not show that one drove another.

## Publishing rules kept

Same as `export_showcase.py`. Only series cleared for publishing are exported: EIA (including the volatility and spike catalog computed from EIA prices, and EIA production and US imports), FRED 10-year yield, IMF PortWatch (credit shown on the page), the Geopolitical Risk Index (CC BY), Natural Earth. Tier C modeled flows are never exported (`EXPORTED_TIERS`, tested). Spike explanations are exported only when hand-checked (tested). `BUDGET_KB` caps the gzipped size of each file (viz3d.js 1.5 MB, flows.json and dash.json 512 KB each; now about 247 KB, 45 KB and 216 KB), checked by a test. NASDAQ, the high-yield spread, OVX and prediction markets are not exported. Disruption events that are not hand-checked are not exported.

## Rebuilding the land files (once)

`land_mask.json` and `region_land.json` come from Natural Earth through the `world-atlas` npm package. The scripts are in `tools/`. Natural Earth is public domain.

## Ideas for the next step

- Real vessel tracks would need an AIS data source with terms that allow publishing. Check the terms before adding one.
- Hand-check events, then draw them on the Hormuz map as dated markers.
- Add the Bab el-Mandeb and Suez lanes to the close-up (M8).
- Thin out the far year labels on the price terrain, which crowd together in the distance (M10).

## Prompt for Claude Code

```
Read 3D_VIEW.md, export_3d.py and docs/3d.html. Copy these files into the repo, run export_3d.py and tools/check_lanes.py, open docs/3d.html, and tell me in plain language what each view shows and where each number comes from. Do not change any method. If the page shows anything the data cannot support, tell me before changing it.
```
