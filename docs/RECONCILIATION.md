# Reconciliation

Generated 2026-10-07 by `tools/reconcile.py`. Each number is queried live from the original source and compared with the database and, where the public page shows it, the page data file (`docs/data/viz3d.js`).

| Number | Date | Source | At source | In database | On page | Result |
|---|---|---|---|---|---|---|
| Brent spot, $/bbl | 2026-03-31 | EIA RBRTE | 126.69 | 126.69 | 126.69 | match |
| Brent spot, $/bbl | 2026-10-02 | EIA RBRTE | 135.51 | 135.51 | 135.51 | match |
| WTI spot, $/bbl (negative print) | 2020-04-20 | EIA RWTC | -36.98 | -36.98 | not shown | match |
| US crude stocks excl. SPR, thousand bbl | 2026-10-02 | EIA WCESTUS1 | 424,134 | 424,134 | not shown | match |
| SPR crude stocks, thousand bbl | 2026-10-02 | EIA WCSSTUS1 | 282,983 | 282,983 | not shown | match |
| US retail gasoline, $/gal | 2026-10-05 | EIA EMM_EPMR_PTE_NUS_DPG | 4.354 | 4.354 | not shown | match |
| 10-year Treasury yield, % | 2026-10-02 | FRED DGS10 | 5.28 | 5.28 | not shown | match |
| Broad dollar index | 2026-10-02 | FRED DTWEXBGS | 121.385 | 121.385 | not shown | match |
| Managed money net, contracts | 2026-09-29 | CFTC 72hh-3qpy | 79,592 | 79,592 | not shown | match |
| Hormuz tanker transits, ships | 2026-03-25 | IMF PortWatch | 2 | 2 | not shown | match |

## Notes

- **Brent at the end of the first quarter of 2026.** EIA's Today in Energy article of April 7, 2026 says the "front-month futures price of Brent crude oil finished the quarter at $118/b". This project's Brent is EIA's daily **spot** price (RBRTE), $126.69 on March 31, 2026. Both are correct; they are different prices. Any caption that quotes $118 must say "front-month futures".
- **Brent spot on October 2, 2026** ($135.51, +18% in one day with WTI flat) matches EIA and FRED but could not be confirmed in news reports. It is kept as published and noted in the README limits.
- **WTI on April 20, 2020** is negative in the source. Every return calculation must handle it (no log of a non-positive price).
