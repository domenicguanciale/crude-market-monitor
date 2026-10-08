# Spike catalog

Generated 2026-10-07 by `spikes.py` from EIA daily spot prices (WTI from Jan 2, 1986, Brent from May 20, 1987). Rules and thresholds: METHODS.md section 11. This table measures moves; it does not explain or predict them. Explanations with sources come next, and every spike is **not yet hand-checked**.

## Read-aloud summary

- **Brent's largest one-day rise** was +51.0% on April 22, 2020, and its **largest one-day fall** -47.5% on April 21, 2020 (negative-price days excluded).
- **WTI's largest one-day rise** was +53.1% on April 22, 2020, and its **largest one-day fall** -33.4% on January 17, 1991 (negative-price days excluded).
- **WTI settled at $-36.98 on April 20, 2020**, a fall of $55.29 in one day. Percent changes are undefined around a negative price, so it is handled in dollars.
- **Brent had 16 days with a move of 8% or more in 2026**; only 1 earlier year(s) had more (most: 21 in 2020).
- **WTI had 13 days with a move of 8% or more in 2026**; only 3 earlier year(s) had more (most: 27 in 2020).
- **Brent's 20-day realized volatility peaked at 112% (annualized) on April 17, 2026**, higher than 99.3% of all trading days since 1987. The latest reading, 90%, is higher than 98% of all days.
- **WTI's 20-day realized volatility peaked at 107% (annualized) on April 20, 2026**, higher than 98.8% of all trading days since 1986. The latest reading, 84%, is higher than 97% of all days.
- **The widest Brent premium over WTI was $37.62 on October 2, 2026** (days with a negative WTI price excluded). That day's Brent print could not be confirmed in news reports (kept as published).
- **The deepest crash episode (60-day rule, positive prices)** was Brent -87.0%, from $70.25 on Jan 6, 2020 to $9.12 on Apr 21, 2020.
- **The largest surge episode (60-day rule)** was Brent +393.9%, from $9.12 on Apr 21, 2020 to $45.04 on Aug 6, 2020.
- These are measured moves. Their causes are not assigned here: research such as Kilian (2009) finds that supply shocks have historically explained less of oil price movement than shifts in demand and fear of shortage, so no single cause is claimed for any spike.

## April 2020: the negative WTI price, its own case

A percent change is undefined after a non-positive price, so these days are listed in dollars and kept out of the percent rankings.

| Date | From | To | Dollar change | Percent change |
|---|---|---|---|---|
| 2020-04-20 | $18.31 | $-36.98 | -55.29 | -302.0% |
| 2020-04-21 | $-36.98 | $8.91 | +45.89 | undefined |

## Top 25 one-day rises, Brent

| Rank | Date | Move | From | To | Rule |
|---|---|---|---|---|---|
| 1 | 2020-04-22 | +51.0% | $9.12 | $13.77 | daily >= 12%, z >= 4 |
| 2 | 2020-04-02 | +35.2% | $14.97 | $20.24 | daily >= 12%, z >= 4 |
| 3 | 2020-05-05 | +24.8% | $20.40 | $25.46 | daily >= 12% |
| 4 | 2020-04-03 | +20.2% | $20.24 | $24.33 | daily >= 12%, z >= 4 |
| 5 | 2009-01-02 | +19.9% | $35.82 | $42.94 | daily >= 12%, z >= 4 |
| 6 | 1991-01-10 | +18.9% | $22.35 | $26.58 | daily >= 12%, z >= 4 |
| 7 | 2026-10-02 (unconfirmed print, see note) | +18.0% | $114.82 | $135.51 | daily >= 12%, z >= 4 |
| 8 | 1998-03-23 | +17.7% | $12.35 | $14.53 | daily >= 12%, z >= 4 |
| 9 | 2020-04-29 | +14.5% | $15.60 | $17.86 | daily >= 12% |
| 10 | 2020-04-08 | +14.1% | $22.10 | $25.22 | daily >= 12% |
| 11 | 2001-11-20 | +13.7% | $16.55 | $18.82 | daily >= 12%, z >= 4 |
| 12 | 1998-12-16 | +13.6% | $9.57 | $10.87 | daily >= 12%, z >= 4 |
| 13 | 1991-01-14 | +13.4% | $26.05 | $29.55 | daily >= 12% |
| 14 | 1988-11-25 | +13.3% | $12.98 | $14.70 | daily >= 12%, z >= 4 |
| 15 | 1990-08-06 | +13.1% | $24.13 | $27.28 | daily >= 12%, z >= 4 |
| 16 | 2026-03-12 | +12.5% | $90.98 | $102.38 | daily >= 12%, z >= 4 |
| 17 | 2004-12-15 | +12.2% | $37.03 | $41.53 | daily >= 12%, z >= 4 |
| 18 | 2026-07-23 | +11.9% | $94.12 | $105.32 | daily >= 8% |
| 19 | 2019-09-16 | +11.7% | $61.25 | $68.42 | daily >= 8%, z >= 4 |
| 20 | 1990-08-02 | +11.6% | $19.93 | $22.25 | daily >= 8%, z >= 4 |
| 21 | 2009-01-26 | +11.3% | $43.13 | $48.00 | daily >= 8% |
| 22 | 2009-04-02 | +10.8% | $45.92 | $50.89 | daily >= 8% |
| 23 | 2008-12-11 | +10.7% | $39.34 | $43.54 | daily >= 8% |
| 24 | 1998-03-18 | +10.5% | $11.05 | $12.21 | daily >= 8%, z >= 4 |
| 25 | 2026-09-10 | +10.5% | $109.51 | $120.98 | daily >= 8% |

## Top 25 one-day falls, Brent

| Rank | Date | Move | From | To | Rule |
|---|---|---|---|---|---|
| 1 | 2020-04-21 | -47.5% | $17.36 | $9.12 | daily >= 12%, z >= 4 |
| 2 | 1991-01-17 | -30.3% | $30.28 | $21.10 | daily >= 12%, z >= 4 |
| 3 | 2020-03-31 | -22.6% | $19.19 | $14.85 | daily >= 12%, z >= 4 |
| 4 | 2020-03-09 | -22.5% | $45.60 | $35.33 | daily >= 12%, z >= 4 |
| 5 | 2020-04-09 | -19.8% | $25.22 | $20.23 | daily >= 12%, z >= 4 |
| 6 | 2020-03-18 | -18.5% | $27.97 | $22.79 | daily >= 12%, z >= 4 |
| 7 | 2001-09-24 | -18.0% | $25.17 | $20.63 | daily >= 12%, z >= 4 |
| 8 | 1990-10-22 | -17.3% | $33.20 | $27.45 | daily >= 12%, z >= 4 |
| 9 | 2008-12-05 | -15.5% | $43.83 | $37.04 | daily >= 12%, z >= 4 |
| 10 | 2026-04-17 | -15.4% | $116.63 | $98.63 | daily >= 12%, z >= 4 |
| 11 | 2020-03-30 | -14.3% | $22.39 | $19.19 | daily >= 12%, z >= 4 |
| 12 | 2020-03-16 | -13.2% | $32.25 | $27.98 | daily >= 12%, z >= 4 |
| 13 | 1991-01-09 | -13.1% | $25.73 | $22.35 | daily >= 12% |
| 14 | 1990-08-27 | -12.6% | $31.65 | $27.65 | daily >= 12%, z >= 4 |
| 15 | 2022-03-09 | -12.5% | $133.18 | $116.58 | daily >= 12%, z >= 4 |
| 16 | 2026-03-23 | -12.4% | $118.42 | $103.79 | daily >= 12%, z >= 4 |
| 17 | 2020-04-20 | -12.1% | $19.75 | $17.36 | daily >= 12% |
| 18 | 2001-11-15 | -12.1% | $18.78 | $16.51 | daily >= 12%, z >= 4 |
| 19 | 2021-11-26 | -11.8% | $82.05 | $72.37 | daily >= 8%, z >= 4 |
| 20 | 2026-04-08 | -11.6% | $138.21 | $122.11 | daily >= 8%, z >= 4 |
| 21 | 2020-03-06 | -11.1% | $51.29 | $45.60 | daily >= 8%, z >= 4 |
| 22 | 2008-10-15 | -10.8% | $74.98 | $66.86 | daily >= 8%, z >= 4 |
| 23 | 2009-01-27 | -10.7% | $48.00 | $42.86 | daily >= 8% |
| 24 | 1991-02-15 | -10.5% | $20.50 | $18.35 | daily >= 8% |
| 25 | 1990-11-30 | -10.0% | $34.65 | $31.20 | daily >= 8% |

## Top 25 one-day rises, WTI

| Rank | Date | Move | From | To | Rule |
|---|---|---|---|---|---|
| 1 | 2020-04-22 | +53.1% | $8.91 | $13.64 | daily >= 12%, z >= 4 |
| 2 | 2020-03-31 | +45.5% | $14.10 | $20.51 | daily >= 12%, z >= 4 |
| 3 | 2020-04-30 | +27.9% | $15.04 | $19.23 | daily >= 12% |
| 4 | 2020-04-02 | +24.2% | $20.28 | $25.18 | daily >= 12%, z >= 4 |
| 5 | 2020-03-19 | +22.5% | $20.48 | $25.09 | daily >= 12%, z >= 4 |
| 6 | 2020-04-29 | +21.3% | $12.40 | $15.04 | daily >= 12% |
| 7 | 1986-08-04 | +21.1% | $11.56 | $14.00 | daily >= 12% |
| 8 | 1990-08-06 | +20.8% | $23.79 | $28.73 | daily >= 12%, z >= 4 |
| 9 | 2020-05-05 | +20.0% | $20.47 | $24.56 | daily >= 12% |
| 10 | 2020-03-23 | +19.8% | $19.48 | $23.33 | daily >= 12%, z >= 4 |
| 11 | 2008-09-22 | +17.8% | $104.05 | $122.61 | daily >= 12%, z >= 4 |
| 12 | 1998-04-27 | +16.6% | $13.23 | $15.43 | daily >= 12%, z >= 4 |
| 13 | 2026-09-28 | +16.6% | $85.23 | $99.37 | daily >= 12%, z >= 4 |
| 14 | 2019-09-16 | +15.2% | $54.76 | $63.10 | daily >= 12%, z >= 4 |
| 15 | 1991-01-22 | +15.2% | $21.63 | $24.91 | daily >= 12% |
| 16 | 1998-06-22 | +14.7% | $11.80 | $13.54 | daily >= 12%, z >= 4 |
| 17 | 2008-12-31 | +14.5% | $38.95 | $44.60 | daily >= 12% |
| 18 | 2009-02-19 | +14.2% | $34.67 | $39.60 | daily >= 12% |
| 19 | 2008-12-26 | +14.1% | $32.94 | $37.58 | daily >= 12% |
| 20 | 2003-03-25 | +13.2% | $29.51 | $33.42 | daily >= 12%, z >= 4 |
| 21 | 1986-04-07 | +12.9% | $12.75 | $14.39 | daily >= 12% |
| 22 | 1998-03-23 | +12.8% | $14.31 | $16.14 | daily >= 12%, z >= 4 |
| 23 | 2020-04-03 | +12.6% | $25.18 | $28.36 | daily >= 12% |
| 24 | 2026-03-06 | +12.2% | $80.88 | $90.77 | daily >= 12%, z >= 4 |
| 25 | 2016-02-12 | +12.0% | $26.19 | $29.32 | daily >= 8% |

## Top 25 one-day falls, WTI

| Rank | Date | Move | From | To | Rule |
|---|---|---|---|---|---|
| 1 | 1991-01-17 | -33.4% | $32.25 | $21.48 | daily >= 12%, z >= 4 |
| 2 | 2020-03-09 | -24.5% | $41.14 | $31.05 | daily >= 12%, z >= 4 |
| 3 | 2020-03-18 | -24.0% | $26.96 | $20.48 | daily >= 12%, z >= 4 |
| 4 | 2020-04-27 | -23.9% | $15.99 | $12.17 | daily >= 12%, z >= 4 |
| 5 | 2020-03-20 | -22.4% | $25.09 | $19.48 | daily >= 12%, z >= 4 |
| 6 | 2020-03-26 | -20.0% | $20.75 | $16.60 | daily >= 12%, z >= 4 |
| 7 | 1986-07-22 | -16.8% | $13.07 | $10.88 | daily >= 12% |
| 8 | 2026-04-08 | -16.1% | $114.58 | $96.17 | daily >= 12%, z >= 4 |
| 9 | 1990-10-22 | -15.8% | $33.82 | $28.46 | daily >= 12%, z >= 4 |
| 10 | 2001-09-24 | -15.7% | $25.46 | $21.46 | daily >= 12%, z >= 4 |
| 11 | 2003-03-26 | -14.1% | $33.42 | $28.71 | daily >= 12%, z >= 4 |
| 12 | 1998-04-23 | -13.1% | $15.07 | $13.09 | daily >= 12%, z >= 4 |
| 13 | 1991-01-28 | -12.9% | $24.15 | $21.03 | daily >= 12% |
| 14 | 1986-03-24 | -12.5% | $13.95 | $12.20 | daily >= 12% |
| 15 | 2008-09-23 | -12.0% | $122.61 | $107.85 | daily >= 12%, z >= 4 |
| 16 | 1990-08-27 | -12.0% | $31.10 | $27.36 | daily >= 12%, z >= 4 |
| 17 | 2022-03-09 | -12.0% | $123.64 | $108.81 | daily >= 8%, z >= 4 |
| 18 | 2009-01-07 | -12.0% | $48.56 | $42.75 | daily >= 8% |
| 19 | 2000-12-20 | -12.0% | $29.34 | $25.83 | daily >= 8%, z >= 4 |
| 20 | 1998-12-17 | -12.0% | $12.55 | $11.05 | daily >= 8% |
| 21 | 1989-04-24 | -11.7% | $23.38 | $20.64 | daily >= 8%, z >= 4 |
| 22 | 1990-11-30 | -11.7% | $32.93 | $29.08 | daily >= 8% |
| 23 | 2005-03-23 | -11.7% | $55.95 | $49.43 | daily >= 8%, z >= 4 |
| 24 | 2026-03-10 | -11.6% | $94.65 | $83.71 | daily >= 8%, z >= 4 |
| 25 | 1990-08-08 | -11.5% | $29.60 | $26.19 | daily >= 8%, z >= 4 |

## Surges: rise of 40% or more within 60 trading days

| Benchmark | Start | Extreme | Size | From | To |
|---|---|---|---|---|---|
| Brent | 2020-04-21 | 2020-08-06 | +393.9% | $9.12 | $45.04 |
| WTI | 2020-04-21 | 2020-08-05 | +374.2% | $8.91 | $42.25 |
| Brent | 1990-06-08 | 1990-09-27 | +182.4% | $14.68 | $41.45 |
| WTI | 1990-06-20 | 1990-10-11 | +166.2% | $15.43 | $41.07 |
| WTI | 2008-12-23 | 2009-06-11 | +140.1% | $30.28 | $72.69 |
| Brent | 2025-12-16 | 2026-04-07 | +130.6% | $59.93 | $138.21 |
| WTI | 2025-12-16 | 2026-04-07 | +106.7% | $55.44 | $114.58 |
| Brent | 2026-07-02 | 2026-10-02 (unconfirmed print, see note) | +97.7% | $68.53 | $135.51 |
| WTI | 2016-02-11 | 2016-06-08 | +95.6% | $26.19 | $51.23 |
| Brent | 2021-12-01 | 2022-03-08 | +91.5% | $69.53 | $133.18 |
| WTI | 2021-12-01 | 2022-03-08 | +88.9% | $65.44 | $123.64 |
| Brent | 2016-01-20 | 2016-05-18 | +88.1% | $26.01 | $48.93 |
| WTI | 2020-10-30 | 2021-03-05 | +85.4% | $35.64 | $66.08 |
| Brent | 2020-10-30 | 2021-02-24 | +84.0% | $36.33 | $66.85 |
| Brent | 2009-02-18 | 2009-06-11 | +82.0% | $39.41 | $71.71 |
| WTI | 1998-12-21 | 1999-05-04 | +74.4% | $10.86 | $18.94 |
| Brent | 1999-02-09 | 1999-05-04 | +73.8% | $9.77 | $16.98 |
| Brent | 2020-03-31 | 2020-04-08 | +69.8% | $14.85 | $25.22 |
| WTI | 1986-03-31 | 1986-05-19 | +67.1% | $10.25 | $17.13 |
| Brent | 1988-10-05 | 1989-01-20 | +62.1% | $11.20 | $18.15 |
| WTI | 2008-12-23 | 2009-01-05 | +60.5% | $30.28 | $48.61 |
| WTI | 2002-01-18 | 2002-04-02 | +54.0% | $18.02 | $27.75 |
| Brent | 2008-12-26 | 2009-03-26 | +53.8% | $33.73 | $51.89 |
| WTI | 2026-07-06 | 2026-09-15 | +53.8% | $69.60 | $107.02 |
| Brent | 2026-07-02 | 2026-07-23 | +53.7% | $68.53 | $105.32 |

An episode lasts as long as prices stay beyond the threshold, so it can run longer than 60 trading days; its size is measured from its turning point to its extreme.

## Crashes: fall of 35% or more within 60 trading days

| Benchmark | Start | Extreme | Size | From | To |
|---|---|---|---|---|---|
| WTI | 2020-01-06 | 2020-04-20 | -100.25 $ (price below zero) | $63.27 | $-36.98 |
| Brent | 2020-01-06 | 2020-04-21 | -87.0% | $70.25 | $9.12 |
| WTI | 2008-07-14 | 2008-12-23 | -79.1% | $145.16 | $30.28 |
| Brent | 2008-07-11 | 2008-12-26 | -76.5% | $143.68 | $33.73 |
| WTI | 1986-01-06 | 1986-03-31 | -61.4% | $26.53 | $10.25 |
| WTI | 2014-09-26 | 2015-01-28 | -53.9% | $95.55 | $44.08 |
| Brent | 2014-09-17 | 2015-01-13 | -53.8% | $97.70 | $45.13 |
| Brent | 1990-11-01 | 1991-04-02 | -50.5% | $35.65 | $17.63 |
| Brent | 2026-04-07 | 2026-07-02 | -50.4% | $138.21 | $68.53 |
| WTI | 1990-11-26 | 1991-02-22 | -47.6% | $33.28 | $17.43 |
| Brent | 2015-10-16 | 2016-01-20 | -46.9% | $48.96 | $26.01 |
| Brent | 1990-10-11 | 1991-01-09 | -45.7% | $41.15 | $22.35 |
| WTI | 2015-11-03 | 2016-01-20 | -44.3% | $47.88 | $26.68 |
| WTI | 1990-11-08 | 1991-01-18 | -43.7% | $35.61 | $20.05 |
| Brent | 2001-09-14 | 2001-11-15 | -43.5% | $29.22 | $16.51 |
| WTI | 2018-10-03 | 2018-12-27 | -41.8% | $76.40 | $44.48 |
| Brent | 2018-10-04 | 2018-12-28 | -41.2% | $86.07 | $50.57 |
| WTI | 2001-09-14 | 2001-11-15 | -40.9% | $29.59 | $17.50 |
| Brent | 2008-07-03 | 2008-09-16 | -40.4% | $143.95 | $85.85 |
| WTI | 1990-10-11 | 1991-01-04 | -39.4% | $41.07 | $24.88 |
| WTI | 2026-04-07 | 2026-07-06 | -39.3% | $114.58 | $69.60 |
| Brent | 1998-09-24 | 1998-12-10 | -38.7% | $14.84 | $9.10 |
| WTI | 1990-10-11 | 1990-12-12 | -38.4% | $41.07 | $25.30 |
| WTI | 2015-06-10 | 2015-08-24 | -37.7% | $61.36 | $38.22 |
| WTI | 2008-07-03 | 2008-09-16 | -37.0% | $145.31 | $91.49 |

An episode lasts as long as prices stay beyond the threshold, so it can run longer than 60 trading days; its size is measured from its turning point to its extreme.

## Drawdowns: peak to trough of 30% or more

| Benchmark | Start | Extreme | Size | From | To | Regained the peak |
|---|---|---|---|---|---|---|
| WTI | 2020-04-03 | 2020-04-20 | -65.34 $ (price below zero) | $28.36 | $-36.98 | 2020-05-15 |
| Brent | 2019-04-25 | 2020-03-31 | -80.2% | $74.94 | $14.85 | 2021-06-23 |
| WTI | 2019-04-23 | 2020-03-30 | -78.7% | $66.24 | $14.10 | 2021-05-17 |
| Brent | 2008-07-03 | 2008-12-26 | -76.6% | $143.95 | $33.73 | not yet |
| WTI | 2008-09-22 | 2008-12-23 | -75.3% | $122.61 | $30.28 | 2022-03-08 |
| Brent | 2020-04-08 | 2020-04-21 | -63.8% | $25.22 | $9.12 | 2020-05-05 |
| Brent | 2013-02-08 | 2015-01-13 | -62.0% | $118.90 | $45.13 | 2022-03-02 |
| WTI | 1986-01-06 | 1986-03-31 | -61.4% | $26.53 | $10.25 | 1990-08-06 |
| Brent | 2015-05-13 | 2016-01-20 | -60.8% | $66.33 | $26.01 | 2017-12-28 |
| WTI | 2013-09-06 | 2015-03-17 | -60.8% | $110.62 | $43.39 | 2022-03-02 |
| WTI | 1990-10-11 | 1991-02-22 | -57.6% | $41.07 | $17.43 | 2004-05-14 |
| WTI | 2015-06-10 | 2016-02-11 | -57.3% | $61.36 | $26.19 | 2018-01-03 |
| Brent | 1996-10-22 | 1998-03-17 | -56.5% | $25.40 | $11.05 | 1999-11-10 |
| WTI | 1996-12-19 | 1998-06-15 | -56.0% | $26.55 | $11.69 | 1999-11-17 |
| WTI | 2000-09-20 | 2001-11-15 | -53.0% | $37.22 | $17.50 | 2003-02-24 |
| Brent | 2026-04-07 | 2026-07-02 | -50.4% | $138.21 | $68.53 | not yet |
| Brent | 2022-03-08 | 2023-03-17 | -46.7% | $133.18 | $71.03 | 2026-04-07 |
| Brent | 1987-08-03 | 1988-10-05 | -46.5% | $20.95 | $11.20 | 1989-04-19 |
| Brent | 2001-02-08 | 2001-11-15 | -46.2% | $30.68 | $16.51 | 2002-12-24 |
| WTI | 2022-03-08 | 2023-03-17 | -46.1% | $123.64 | $66.61 | not yet |
| Brent | 1990-09-27 | 1991-01-09 | -46.1% | $41.45 | $22.35 | 2004-07-30 |
| WTI | 1987-07-16 | 1988-10-05 | -43.9% | $22.44 | $12.58 | 1989-04-19 |
| Brent | 1991-10-18 | 1994-02-18 | -43.5% | $23.00 | $13.00 | 1996-04-11 |
| WTI | 2018-06-27 | 2018-12-27 | -42.5% | $77.41 | $44.48 | 2021-10-04 |
| WTI | 1991-10-18 | 1994-02-16 | -42.4% | $24.12 | $13.89 | 1996-03-19 |

## Brent minus WTI blowouts ($15 or more)

| Start | Widest | End | Widest spread |
|---|---|---|---|
| 2026-09-10 | 2026-10-02 (unconfirmed print, see note) | 2026-10-06 | $37.62 |
| 2011-06-01 | 2011-09-23 | 2011-11-11 | $29.59 |
| 2026-03-18 | 2026-04-08 | 2026-04-22 | $25.94 |
| 2012-07-10 | 2012-10-10 | 2013-03-20 | $24.87 |
| 2008-09-22 | 2008-09-22 | 2008-09-22 | $-22.18 |
| 2012-02-06 | 2012-04-03 | 2012-04-16 | $21.64 |
| 2011-02-10 | 2011-02-14 | 2011-02-28 | $19.46 |
| 2013-11-18 | 2013-11-27 | 2013-12-04 | $19.27 |
| 2012-05-09 | 2012-05-22 | 2012-06-11 | $18.32 |
| 2011-05-06 | 2011-05-11 | 2011-05-19 | $17.78 |
| 2011-04-05 | 2011-04-11 | 2011-04-15 | $16.96 |
| 2014-01-08 | 2014-01-13 | 2014-01-13 | $16.57 |
| 2026-04-30 | 2026-04-30 | 2026-04-30 | $15.60 |

Days with a non-positive WTI price are excluded: on April 20, 2020 the spread was $54.34 by arithmetic alone.

## Sensitivity check

The same rules at other thresholds. Changing a threshold changes how long the list is, not which moves are at the top: the largest moves pass every threshold.

| Benchmark | Rule | Setting | Count |
|---|---|---|---|
| Brent | daily move | >= 6% | 251 |
| Brent | daily move | >= 8% | 106 |
| Brent | daily move | >= 10% | 56 |
| Brent | daily move | >= 12% | 35 |
| Brent | daily move | >= 15% | 18 |
| Brent | surge | >= 30% in 60 days | 61 |
| Brent | surge | >= 40% in 60 days | 36 |
| Brent | surge | >= 50% in 60 days | 17 |
| Brent | surge | window 40 days | 25 |
| Brent | surge | window 60 days | 36 |
| Brent | surge | window 90 days | 42 |
| Brent | crash | >= 25% in 60 days | 38 |
| Brent | crash | >= 35% in 60 days | 15 |
| Brent | crash | >= 45% in 60 days | 7 |
| Brent | crash | window 40 days | 11 |
| Brent | crash | window 60 days | 15 |
| Brent | crash | window 90 days | 19 |
| Brent | drawdown | >= 20% | 50 |
| Brent | drawdown | >= 30% | 22 |
| Brent | drawdown | >= 40% | 12 |
| WTI | daily move | >= 6% | 325 |
| WTI | daily move | >= 8% | 163 |
| WTI | daily move | >= 10% | 82 |
| WTI | daily move | >= 12% | 41 |
| WTI | daily move | >= 15% | 26 |
| WTI | surge | >= 30% in 60 days | 57 |
| WTI | surge | >= 40% in 60 days | 34 |
| WTI | surge | >= 50% in 60 days | 18 |
| WTI | surge | window 40 days | 19 |
| WTI | surge | window 60 days | 34 |
| WTI | surge | window 90 days | 49 |
| WTI | crash | >= 25% in 60 days | 46 |
| WTI | crash | >= 35% in 60 days | 17 |
| WTI | crash | >= 45% in 60 days | 5 |
| WTI | crash | window 40 days | 14 |
| WTI | crash | window 60 days | 17 |
| WTI | crash | window 90 days | 20 |
| WTI | drawdown | >= 20% | 57 |
| WTI | drawdown | >= 30% | 22 |
| WTI | drawdown | >= 40% | 13 |
| Brent-WTI | spread blowout | >= $10 | 20 |
| Brent-WTI | spread blowout | >= $15 | 13 |
| Brent-WTI | spread blowout | >= $20 | 12 |

- **Brent surges found at every threshold tested** (11): Apr 2020 to Aug 2020 (+393.9%), Jun 1990 to Sep 1990 (+182.4%), Dec 2025 to Apr 2026 (+130.6%), Jul 2026 to Oct 2026 (+97.7%), Dec 2021 to Mar 2022 (+88.9%), Jan 2016 to May 2016 (+76.2%), Feb 1999 to May 1999 (+73.8%), Mar 2009 to Jun 2009 (+70.0%)
- **Brent crashes found at every threshold tested** (6): Jan 2020 to Apr 2020 (-87.0%), Jul 2008 to Dec 2008 (-73.5%), Apr 2026 to Jul 2026 (-50.4%), Nov 1990 to Feb 1991 (-49.6%), Oct 2014 to Jan 2015 (-48.1%), Oct 2015 to Jan 2016 (-45.9%)
- **WTI surges found at every threshold tested** (13): Apr 2020 to Aug 2020 (+374.2%), Jun 1990 to Oct 1990 (+166.2%), Feb 2009 to Jun 2009 (+113.6%), Dec 2025 to Apr 2026 (+106.7%), Dec 2021 to Mar 2022 (+86.2%), Feb 2016 to May 2016 (+84.4%), Mar 1986 to May 1986 (+67.1%), Feb 1999 to May 1999 (+66.4%)
- **WTI crashes found at every threshold tested** (5): Jan 2020 to Apr 2020 (-100.25 $ (price below zero)), Jul 2008 to Dec 2008 (-76.1%), Jan 1986 to Mar 1986 (-61.4%), Nov 1990 to Feb 1991 (-47.6%), Oct 2014 to Jan 2015 (-46.4%)

## Notes on the data

- **Brent on October 2, 2026:** EIA's Brent spot of $135.51 (+18%, WTI flat) matches FRED but was not confirmed in news reports.

