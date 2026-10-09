# Sources

Every data source the project uses or has checked, with its terms and whether it may appear on the public pages (`docs/index.html`, `docs/3d.html`). The code enforces the same flags: `fred.INDICATORS[...]["publishable"]`, `gpr.PUBLISHABLE`, `chokepoints.PUBLISHABLE`, and the `PUBLISHABLE` checks in `export_showcase.py` and `export_3d.py`. If a source's terms are unclear, it stays local until a decision is made.

"Checked" is the date the access and terms were confirmed on the live service.

## In use

| Source | URL | What it provides | Terms summary | Attribution text | Public | Checked |
|---|---|---|---|---|---|---|
| U.S. Energy Information Administration (EIA) API v2 | https://www.eia.gov/opendata/ | Weekly US stocks, refinery utilization, production, exports, SPR; daily Brent and WTI spot; WTI futures (history only, ends April 5, 2024) | US government data, public domain. Credit EIA; do not use the EIA logo. Free key | "Source: U.S. Energy Information Administration" | Yes | Oct 5, 2026 |
| FRED, 10-year Treasury yield (`DGS10`) | https://fred.stlouisfed.org/series/DGS10 | Daily yield | Federal Reserve H.15, no third-party copyright notice. FRED API key required for automated access | "Board of Governors of the Federal Reserve System, via FRED, Federal Reserve Bank of St. Louis" | Yes | Oct 5, 2026 |
| FRED, OVX (`OVXCLS`) | https://fred.stlouisfed.org/series/OVXCLS | Daily oil volatility index | Copyright CBOE, "reprinted with permission". Personal use only | "Chicago Board Options Exchange, via FRED" | **No** | Oct 5, 2026 |
| FRED, NASDAQ Composite (`NASDAQCOM`) | https://fred.stlouisfed.org/series/NASDAQCOM | Daily index | Copyright Nasdaq OMX Group | "Nasdaq OMX Group, via FRED" | **No** | Oct 5, 2026 |
| FRED, ICE BofA US High Yield spread (`BAMLH0A0HYM2`) | https://fred.stlouisfed.org/series/BAMLH0A0HYM2 | Daily spread, only from Oct 6, 2023 on FRED | Copyright ICE Data Indices; reproduction prohibited without written permission | "ICE Data Indices, via FRED" | **No** | Oct 5, 2026 |
| CFTC Commitments of Traders, Legacy Futures Only (`6dca-aqww`) | https://publicreporting.cftc.gov/ | Weekly WTI positions since 1986 (noncommercial = large speculators) | US government, public domain. No key; unauthenticated requests are throttled | "Source: CFTC Commitments of Traders" | Yes | Oct 5, 2026 |
| IMF PortWatch | https://portwatch.imf.org/ | Daily tanker and ship transits at chokepoints since 2019, chokepoint coordinates | IMF data may be published and redistributed with attribution to the IMF | "IMF PortWatch" | Yes | Oct 5, 2026 |
| Geopolitical Risk Index (Caldara and Iacoviello) | https://www.matteoiacoviello.com/gpr.htm | Daily GPR, acts and threats, since 1985 | Creative Commons BY | "Caldara, Dario and Matteo Iacoviello (2022), Measuring Geopolitical Risk, American Economic Review 112(4). Data from matteoiacoviello.com/gpr.htm" | Yes | Oct 5, 2026 |
| Polymarket public market data | https://docs.polymarket.com/ | Daily odds and volume snapshots for Gulf-conflict and oil-price markets | No key for market data. Redistribution terms not confirmed | "Polymarket" | **No** (local only) | Oct 5, 2026 |
| Kalshi public market data | https://docs.kalshi.com/ | Daily candles (odds, volume) for the same topics | Docs state market data is public, no key. Redistribution terms not confirmed | "Kalshi" | **No** (local only) | Oct 5, 2026 |
| Natural Earth (via the world-atlas package) | https://www.naturalearthdata.com/about/terms-of-use/ | Land outlines for the globe and the Gulf coastline | Public domain; crediting is optional | "Made with Natural Earth" | Yes | Oct 7, 2026 |
| News agencies and official bodies cited per event row | Each row of `data/iran_war_2026.csv` and `EVENTS_STARTER.csv` | Dates, volumes, prices for disruption events | Facts cited with links; no article text reproduced. Rows are published only after hand-checking | Per row | Only hand-checked rows | Oct 5, 2026 |

## Checked for the World Oil Simulation

In use from M1: the dollar index, EIA retail gasoline and diesel, and the CFTC disaggregated report. In use from M4: EIA US imports by origin (Tier A) and EIA international production by country (Tier B), plus Natural Earth label points. UN Comtrade and JODI stay local and unused: without them, modeled worldwide arcs (Tier C) are not published. Published on the 3D page from M6 and M7: the EIA series above, the FRED 10-year yield and dollar index, CFTC positioning (legacy and disaggregated), IMF PortWatch and the GPR index, each credited in the page footer and in each chart's source line.

| Source | URL | What it would provide | Terms summary | Public | Checked |
|---|---|---|---|---|---|
| FRED, Nominal Broad U.S. Dollar Index (`DTWEXBGS`) | https://fred.stlouisfed.org/series/DTWEXBGS | Daily dollar index from 2006 | Federal Reserve H.10, no third-party copyright notice in the series notes | Yes | Oct 7, 2026 |
| EIA retail gasoline (`EMM_EPMR_PTE_NUS_DPG`) and diesel (`EMD_EPD2D_PTE_NUS_DPG`) | route `petroleum/pri/gnd` | Weekly US retail prices from 1990 and 1994 | EIA, public domain | Yes | Oct 7, 2026 |
| EIA US imports by country of origin (in use from M4, https://www.eia.gov/opendata/browser/petroleum/move/impcus) | route `petroleum/move/impcus` | Monthly US crude imports by origin (Tier A, measured) | EIA, public domain | Yes | Oct 7, 2026 |
| EIA international data (in use from M4, https://www.eia.gov/opendata/browser/international) | route `international` | Monthly production, exports and imports by country, to June 2026 (Tier B) | EIA, public domain | Yes | Oct 7, 2026 |
| CFTC Disaggregated Futures Only (`72hh-3qpy`) | https://publicreporting.cftc.gov/ | Weekly WTI managed money, swap dealer, producer positions from June 2006 | US government, public domain, no key | Yes | Oct 7, 2026 |
| IEA reports and commentaries | https://www.iea.org/help-centre/usage-and-rights | Cited figures such as Hormuz flows | Most text and figures CC BY 4.0. Datasets, data explorers and the Oil Market Report are excluded | Cited numbers only | Oct 7, 2026 |
| UN Comtrade (HS 2709) | https://comtrade.un.org/licenseagreement.html | Bilateral crude trade between reporting countries | Copyright United Nations; "internal use only"; re-dissemination needs written permission from UNSD. Free key for the API | **No** (local only) | Oct 7, 2026 |
| JODI Oil World Database | https://www.jodidata.org/oil/database/data-downloads.aspx | Monthly production, exports, imports, demand by country since 2002 | Free download; no terms of use found on the site | **No** until terms are confirmed | Oct 7, 2026 |
| China customs crude imports by origin | n/a | Monthly imports by origin | No verifiable, publishable feed found | Skipped | Oct 7, 2026 |

## Software (loaded by the public pages)

| Library | Version | Licence | Loaded from |
|---|---|---|---|
| Plotly.js | 2.35.2 | MIT | cdn.jsdelivr.net |
| Three.js | 0.160.0 | MIT | cdn.jsdelivr.net |
