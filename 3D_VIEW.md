# 3D view

Page: `docs/3d.html`. Data: `docs/data/viz3d.js`, written by `export_3d.py`. One time slider drives three views.

| View | What it shows | Data |
|---|---|---|
| Globe | A pillar at each of six chokepoints. Height is tankers per day (7-day average). A ring marks that lane's own 2019 to 2025 median | IMF PortWatch via `chokepoint_transit` |
| Skyline | One bar per week, 1996 to 2026. Height is the tightness score, from -3 loose to +3 tight. Switch: keep 2020 in the five-year range | `weekly_reading`, scored twice with `compare_2020.scores` |
| Hormuz ships | A map of the Gulf with the coastline and one moving ship for each daily tanker transit. Facility pins appear only for facilities tied to hand-checked events (none yet) | `chokepoint_transit` and `facility` |

The readout panel and the two strips under the canvas show Brent, WTI, the spread, the 10-year yield, the Geopolitical Risk Index and tanker counts for the selected date. The URL hash (`#v=hz&d=2026-03-25`) holds the view and date, so a link opens where you left it.

## Run it

```bash
.venv/bin/python export_3d.py          # after fetch.py and calculate.py
.venv/bin/python tools/check_lanes.py  # confirms every ship lane stays in open water
open docs/3d.html                      # or push and open it on GitHub Pages
```

`docs/index.html` links to the 3D page.

`Crude_Market_Monitor_3D.html` is the same page with the data inlined, for sending as one file. It is git-ignored because no script regenerates it, so a committed copy would go stale. The page loads Three.js 0.160.0 from the jsDelivr CDN, so it needs internet.

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
