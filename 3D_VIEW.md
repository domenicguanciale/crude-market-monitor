# 3D view

Page: `docs/3d.html`. Data: `docs/data/viz3d.js`, written by `export_3d.py`. Code: `docs/js/` (ES modules). One shared time state drives three views, on one time axis from January 2, 1986 to the latest data. The page opens on February 28, 2026, the start of the 2026 Strait of Hormuz disruption.

| View | What it shows | Data |
|---|---|---|
| Globe | A pillar at each of six chokepoints. Height is tankers per day (7-day average). A ring marks that lane's own 2019 to 2025 median. Before January 1, 2019 the pillars say "no data" | IMF PortWatch via `chokepoint_transit` |
| Skyline | One bar per week, from November 1995 (the first week with five full prior years) to today. Weeks after the selected date are faded. Height is the tightness score, from -3 loose to +3 tight. Switch: keep 2020 in the five-year range | `weekly_reading`, scored twice with `compare_2020.scores` |
| Hormuz ships | A map of the Gulf with the coastline and one moving ship for each daily tanker transit. No ships before 2019, and the note says why. Facility pins appear only for facilities tied to hand-checked events (none yet) | `chokepoint_transit` and `facility` |

The readout panel and the two strips under the canvas show Brent, WTI, the spread, the 10-year yield, the Geopolitical Risk Index and tanker counts for the selected date. The URL hash (`#v=hz&d=2026-03-25&k=1`) holds the view, the date and the 2020 switch, so a link opens where you left it. Any value the data does not have for a date (prices before Brent starts in 1987, scores before November 1995, tanker counts before 2019) shows as "n/a", never as an estimate.

## How the code is laid out (M5)

| File | Job |
|---|---|
| `docs/js/state.js` | The one shared state: date, playing, speed, view, 2020 switch. Views subscribe to it and never keep their own copy of the date, so they cannot disagree. Also the URL hash and deterministic playback (`advance`). Pure functions, no drawing |
| `docs/js/data.js` | Reads `viz3d.js`. Each daily series is stored compactly as `{s: first day, v: values}` (format 2). `lastVal` carries a value forward at most 7 days, so a stale number never looks current |
| `docs/js/scenes/globe.js`, `skyline.js`, `hormuz.js` | One file per view. Each returns the same small interface: camera, legend, caption, `update(state)`, `pick` for hover, and a text description for screen readers |
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

`tests/browser/test_pages.py` runs both public pages in headless Chromium (Playwright): no console errors in light and dark mode at desktop and 390 px phone width, no sideways scroll, a non-blank canvas in every view, readouts equal to the database on fixed dates (2008-07-03, 2020-04-21, 2026-04-17), "n/a" before each series starts, and the state module's clamping, hash round trip and deterministic playback. `QA_SHOTS=1` saves screenshots to `docs/qa/`. The tests skip if Playwright is not installed.

## Limits to state if asked

- **Ship positions are schematic.** The database has daily counts per chokepoint, not vessel tracks. The count of ships drawn is real (Hormuz 7-day average, rounded). The lanes are hand-placed waypoints checked against the coastline, and the split between lanes and between directions is a display choice.
- **Facility pins wait for hand-checking.** The facility rows came from the AI-drafted event tables, so `export_3d.py` exports a pin only when a hand-checked event points to it. Coordinates are approximate. The page shows names and places only, never events.
- **Ships have one colour.** The data has no direction or origin per ship, so neither is shown. Which route a ship is drawn on is a display weight, stated on the page.
- **The readout's Brent minus WTI is daily.** The tightness section uses the weekly average, as in the main project.
- **PortWatch counts come from satellite ship signals** and miss ships that switch them off.
- **The skyline is US data only.** The Brent minus WTI spread sits beside it for that reason.
- **Moves together, not causes.** The page puts different sources on one time axis. It does not show that one drove another.

## Publishing rules kept

Same as `export_showcase.py`. Only series cleared for publishing are exported: EIA, FRED 10-year yield, IMF PortWatch (credit shown on the page), the Geopolitical Risk Index (CC BY). NASDAQ, the high-yield spread, OVX and prediction markets are not exported. Disruption events that are not hand-checked are not exported.

## Rebuilding the land files (once)

`land_mask.json` and `region_land.json` come from Natural Earth through the `world-atlas` npm package. The scripts are in `tools/`. Natural Earth is public domain.

## Ideas for the next step

- Real vessel tracks would need an AIS data source with terms that allow publishing. Check the terms before adding one.
- Hand-check events, then draw them on the Hormuz map as dated markers.
- Add the Bab el-Mandeb and Suez lanes to the close-up.

## Prompt for Claude Code

```
Read 3D_VIEW.md, export_3d.py and docs/3d.html. Copy these files into the repo, run export_3d.py and tools/check_lanes.py, open docs/3d.html, and tell me in plain language what each view shows and where each number comes from. Do not change any method. If the page shows anything the data cannot support, tell me before changing it.
```
