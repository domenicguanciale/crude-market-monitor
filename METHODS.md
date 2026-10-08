# Methods

Written October 5, 2026. Each section gives one default to build and one alternative. If you cannot explain a step out loud, simplify it until you can.

## 1. Seasonal comparison

Oil inventories rise and fall with the seasons, so a raw number means little. Compare each week to the same week in earlier years.

**Default**

1. For each weekly reading, take its week number (1 to 52) from the week-ending date.
2. Collect the values for that same week number in the prior five calendar years. Do not include the current year.
3. Compute three things: the five-year low, the five-year high, and the five-year average.
4. Compute where this week sits:

```
position = (value - low) / (high - low)
pct_vs_avg = (value - average) / average
```

`position` is 0 at the five-year low and 1 at the five-year high. It can go below 0 or above 1 when the value is outside the range.

Example: stocks are 420. The five-year low is 400, the high is 480, the average is 445. Position = (420 - 400) / (480 - 400) = 0.25. Versus average = (420 - 445) / 445 = minus 5.6 percent.

This matches EIA's own definition: "the highest and lowest weekly stock levels ... over the equivalent week during the prior five years."

**Week 53.** Some years have a 53rd week. Compare it to week 52 of the prior years.

**Why not a z-score.** A z-score measures how many standard deviations a value is from the average. With only five past values the standard deviation is unreliable, so the range position is the better tool here.

**Abnormal years.** 2020 (the pandemic) and 2026 (the Strait of Hormuz closure) distort the range. Default: keep them in and say so. Alternative: also show a version that drops 2020, and compare.

## 2. The tightness score

**What goes in.** Use three inputs, each a physical measure:

| Input | Tight when | Why |
|---|---|---|
| Crude stocks | Low | Less cushion against a supply loss |
| Distillate stocks (diesel and heating oil) | Low | The fuel that ran shortest in 2026 |
| Refinery utilization | High | Little spare capacity to make more fuel |

**What stays out.**

- **Price.** Price is the outcome you are trying to explain. If price is inside the score, then "tight markets have high prices" is true by construction and proves nothing. This is called circularity.
- **Production.** Its direction is ambiguous: low production can mean a shortage or weak demand. Show it as a context chart.

**Default scoring**

1. For each input, compute `position` from section 1.
2. Give each input a point:
   - Stocks: plus 1 if position is below 0.25, minus 1 if above 0.75, otherwise 0.
   - Utilization: plus 1 if position is above 0.75, minus 1 if below 0.25, otherwise 0.
3. Add the three points. The total runs from minus 3 to plus 3.
4. Label: **tight** at plus 2 or more, **loose** at minus 2 or less, otherwise **normal**.

Equal weights are the default because you have no evidence yet for any other weighting. The alternative is to weight by what the backtest shows, but that risks fitting the past too closely.

**A second gauge: the Brent minus WTI spread.** Your inputs are all US data. WTI is the US benchmark and Brent is the global one. On September 29, 2026 Brent was $113.96 and WTI was $96.16. A wide gap means the world is short while the US is comparatively well supplied. Show the spread next to the score and label the score "US tightness." Otherwise the monitor can read "normal" in the middle of a global shortage.

## 3. Backtest

A backtest asks: if this score had existed in the past, would it have told you anything?

**Default**

1. Compute the score for every week from 2010 on.
2. Date each score by the day it became public: the Wednesday after the week ends. Using it earlier is look-ahead bias, meaning the test uses information nobody had yet.
3. For each week, compute the WTI price change over the next four weeks:

```
forward_return = (price four weeks later / price at release) - 1
```

4. Compare three groups: tight weeks, loose weeks, and all weeks. For each, report the count, the average, the median, and the hit rate (the share of weeks where the price rose).
5. Repeat using Brent.

**Three cautions to state in the README**

- **Overlapping windows.** Consecutive weeks share three of their four forward weeks, so 100 tight weeks are not 100 independent tests. Also report the result using every fourth week only.
- **Revised data.** You are using today's revised figures, not the first prints people saw at the time. EIA says it revises rarely, but say this.
- **Few episodes.** Tight periods come in clusters. A handful of episodes drive the result.

**If the result is weak.** Report it. "The score did not predict four-week price changes, and here is the evidence" is a finding, and it is more credible than a tuned success.

## 4. Event study

An event study measures how a price moved around an event, compared with how it normally moves. The standard reference is MacKinlay (1997).

**Default, using daily Brent prices**

1. Compute daily returns: `return = ln(price today / price yesterday)`. The `ln` is the natural logarithm. For small moves it is close to the percent change.
2. **Day zero** is `first_trading_day_after` from the events table.
3. **Estimation window:** the 60 trading days ending 11 days before day zero. Compute the average daily return and the standard deviation there. This is "normal" behavior.
4. **Abnormal return** on a day = actual return minus the average from step 3. This is the constant-mean model.
5. **Cumulative abnormal return (CAR)** = the sum of abnormal returns over a window. Compute three: day 0 to 1, day 0 to 5, and day 0 to 20.
6. Also express each CAR in standard deviations: `CAR / (daily standard deviation x square root of the number of days)`. A value above 2 is a large move for that period.

Example: the average daily return in the estimation window is 0.05 percent. On day zero Brent rises 12.0 percent. Abnormal return = 11.95 percent.

**Why the constant-mean model.** Stock studies use a market model, which subtracts what the overall stock market did. A commodity has no obvious "market" to subtract, and over a few days the expected return is close to zero anyway. The alternative is to subtract the move in a broad commodity index.

**Overlapping events.** When two events fall within 20 trading days, their windows overlap and you cannot separate their effects. Rows E16 to E18 in the starter table overlap. Treat them as one episode, or use only the 0 to 1 day window for the sub-events.

**Small sample.** With about 15 usable events, do not report an average with a significance test. Show every event in a table, then the median and the range, split by whether barrels were actually lost.

## 5. Relating the reaction to outage size and tightness

1. Compute the outage as a share of world supply: `barrels offline / 100,000,000`. World consumption is about 100 million barrels a day. EIA puts the 20 million barrels a day through the Strait of Hormuz at about 20 percent of global consumption.
2. Make a scatter plot: outage share on the horizontal axis, the 0 to 5 day CAR on the vertical. Color the points by the tightness label that week.
3. Fit one straight line through it as a description, not a law.

With this few points, one event can set the slope. In this data that event is the 2026 Hormuz closure. Show the line with and without it.

## 6. Scenario calculator

Do not build a formula that outputs a single number. Build a lookup.

1. The user enters an outage size and the current tightness label.
2. The tool finds the past events closest in size with the same label.
3. It shows those events by name, with their 1, 5, and 20 day moves, and the low and high of that set.

The output reads: "Three past events of similar size in a tight market moved Brent between X and Y percent over five days." It must also show how many events that is. A range built on two events should say so.

## 7. What published research says

- **Supply shocks have historically mattered less than people assume.** Kilian (2009) separates oil price moves into supply shocks, global demand shocks, and precautionary demand, meaning buying driven by fear of future shortage. He finds supply disruptions made comparatively small contributions to the price of oil, while precautionary demand drove most swings. A 2024 replication with data through January 2025 confirms this. This cuts against a simple "barrels lost equals price up" story, and you should say so.
- **Risk alone moves prices.** EIA documented a 3.4 percent daily move in Brent in January 2020 with no barrels lost. Your table marks these as risk events for this reason.
- **Reactions can reverse quickly.** After the 2019 Abqaiq attack, EIA reports the largest one-day rise in a decade followed by a fall the next day once restoration was announced.
- **2026 is the exception in scale.** EIA describes the first quarter rise in Brent, from $61 to $118, as the largest inflation-adjusted increase in its data going back to 1988. EIA also notes that prices in the third quarter moved on leaders' public statements about military plans and a possible peace deal, which is precautionary demand at work.
- **A ready-made risk measure exists.** The Geopolitical Risk Index by Caldara and Iacoviello counts newspaper coverage of geopolitical tension. It is free, daily, and could be a fourth gauge in a later version.

## 8. Limits (paste into the README)

- The score uses US data only and measures US conditions, not global ones.
- Weekly figures are estimates and are sometimes revised. The backtest uses revised data.
- Forward windows overlap, which overstates how much evidence there is.
- The event table is small, and other news moves prices on the same days.
- The 2026 Strait of Hormuz episode is far larger than any other event and dominates averages. Results are shown with and without it.
- The event table was drafted with AI assistance and hand-checked. The accuracy rate is reported.
- The tool describes how prices reacted in the past. It does not forecast when disruptions happen or what prices will do.
- This is a student project and is not investment advice.

## 9. Interview questions

1. **What does your score measure?** Whether US crude stocks, distillate stocks, and refinery utilization are unusually tight for the time of year, compared with the same week in the prior five years.
2. **Why five years?** It is the convention EIA uses in its own weekly charts, so readers already understand it. It is long enough to show a normal range and short enough to reflect the current market.
3. **Why isn't price in the score?** Price is what I am trying to explain. Including it would make the result circular.
4. **Does the score predict prices?** Give the actual backtest result, including if it is weak. Then say what the overlapping-window check showed.
5. **What is look-ahead bias and how did you avoid it?** Using information before it was public. I date each score to the Wednesday release, not the Friday the week ended.
6. **What is an abnormal return?** The actual price move minus the normal move for that period, where normal comes from the 60 trading days before the event.
7. **How many events do you have, and is that enough?** State the number. It is not enough for statistical claims, so I show every event and report ranges.
8. **How do you handle 2026?** As one episode with sub-events, and I show results with and without it because it dominates.
9. **What does the research say about supply shocks?** Kilian found they historically explain little of oil price movement compared with demand and fear of shortage. My risk-event rows are consistent with that.
10. **What would you do with more time?** Add global inventory and shipping data, use first-print data for the backtest, and test the Geopolitical Risk Index as an input.

## 10. Glossary

| Term | Meaning |
|---|---|
| Benchmark | A reference price. WTI for the US, Brent for the world |
| Spread | The difference between two prices |
| Distillate | Diesel and heating oil |
| Refinery utilization | The share of refining capacity in use |
| Position in range | Where a value sits between the five-year low and high |
| Circularity | Using the thing you want to explain as one of its own causes |
| Backtest | Testing a rule on past data |
| Look-ahead bias | Using information before it was available |
| Hit rate | The share of cases where the outcome went the expected way |
| Log return | The natural logarithm of today's price over yesterday's |
| Estimation window | The period used to measure normal behavior |
| Abnormal return | Actual return minus normal return |
| Cumulative abnormal return | The sum of abnormal returns over a window |
| Precautionary demand | Buying driven by fear of future shortage |
| Force majeure | A declaration that a supplier cannot meet contracts because of events outside its control |

## 11. Spike catalog (World Oil Simulation, M2)

The biggest crashes and surges are found by rules in code (`spikes.py`), not picked by eye. Every threshold sits in one `CONFIG` block. The results are in `docs/SPIKES.md` and the `spike` table.

**Daily changes, with negative prices handled.** For each trading day: the dollar change; the percent change, only when the previous price is positive; and the log return, only when both prices are positive. WTI settled at -$36.98 on April 20, 2020. The fall to it is $55.29. The percent change out of it is undefined, so April 2020 is listed separately in dollars and kept out of the percent rankings.

**Rules**

| Rule | Flags | Default |
|---|---|---|
| Daily shock | A one-day move of at least 8% (and, marked separately, 12%), or a log return at least 4 standard deviations from zero, where the standard deviation comes from the previous 250 trading days only | 8%, 12%, z = 4 |
| Surge | The price is at least 40% above the lowest positive price of the last 60 trading days | 40%, 60 days |
| Crash | The price is at least 35% below the highest price of the last 60 trading days | 35%, 60 days |
| Drawdown | A peak is confirmed when the price falls 30% below it, a trough when it rises 30% above it. Each peak-to-trough fall is an episode, with the date the price first regained the peak | 30% |
| Realized volatility | Standard deviation of daily log returns over 20 and 60 trading days, times the square root of 252 to annualize | 20, 60 days |
| Spread blowout | Brent minus WTI at least $15 (or WTI over Brent by $15), on days when both prices are positive | $15 |

- **Episodes.** Flagged days within 5 trading days of each other form one episode. An episode lasts as long as prices stay beyond the threshold, so it can run longer than the 60-day window. Its size is measured from its turning point (the low before a surge, the high before a crash) to its extreme.
- **Sensitivity check.** The same rules run at other thresholds: daily 6% to 15%, surges 30% to 50%, crashes 25% to 45%, windows 40 to 90 days, drawdowns 20% to 40%, spreads $10 to $20. Moving a threshold changes how long the list is, not which moves top it. The surges and crashes found at both the strictest and loosest settings are listed in `docs/SPIKES.md`.
- **Unconfirmed prints** are kept as published and marked. Brent at $135.51 on October 2, 2026 matches EIA and FRED but was not confirmed in news reports.

**Worked example.** WTI on January 6, 2020 was $63.27. By April 3 it was $28.36, more than 35% below the highest price of the previous 60 days, so the crash rule flags it. The episode runs to the trough, -$36.98 on April 20, 2020. Because that trough is below zero, its size is reported in dollars (-$100.25), not as a percent.

**One-minute answer: "How did you find the spikes?"** I wrote the rules first and let the code find the moves. A day counts as a shock if prices moved 8% or more, or the move was more than four standard deviations of the previous year's daily moves. A surge is 40% above the 60-day low, a crash 35% below the 60-day high. Then I reran everything at looser and stricter thresholds: the list gets longer or shorter, but the same episodes stay on top (2020, 2008, 1986, 1990 to 1991, 2014 to 2015, and 2026). Negative WTI in April 2020 breaks percent math, so I handle it in dollars and never take a log of a non-positive price.

**What 2026 looks like against history** (from `docs/SPIKES.md`, Oct 7, 2026): Brent had 16 days with moves of 8% or more in 2026, more than any year except 2020. Brent's 20-day realized volatility peaked at 112% annualized on April 17, 2026, higher than 99.3% of all trading days since 1987. These are measured moves; causes are not assigned by the rules.

## 12. Physical flows and the modeled allocation (World Oil Simulation, M4)

**Three tiers, labelled on the page.**
- **Tier A, measured bilateral flows.** EIA's US crude imports by country of origin, monthly, in thousand barrels per day (`trade_flow`, tier A). Rows that are regional totals are dropped.
- **Tier B, measured country totals.** EIA's monthly crude oil production by country, including lease condensate (`production_by_country`).
- **Tier C, modeled allocation.** Iterative proportional fitting (`ipf.py`) balances a table of flows so each exporter's row adds up to its total and each importer's column to its total, starting from a prior pattern of who trades with whom. Cells that are zero in the prior stay zero.

**Worked example.** Two exporters (A, B) and two importers (X, Y). Last year's flows are the prior: A to X 60, A to Y 40, B to X 20, B to Y 80. This year, A exports 120 and B 80; X imports 90 and Y 110.
1. Scale each row to its total. A's row is multiplied by 120/100, giving 72 and 48; B's by 80/100, giving 16 and 64. The columns now add to 88 and 112, not 90 and 110.
2. Scale each column to its total. X's column is multiplied by 90/88 and Y's by 110/112, giving 73.64, 47.14, 16.36 and 62.86. Now the rows are slightly off (120.78 and 79.22).
3. Repeat. After 6 rounds every row and column matches within a millionth: A to X 73.38, A to Y 46.62, B to X 16.62, B to Y 63.38.

The test suite checks this example and that rows and columns reconcile within the tolerance.

**Why no Tier C arcs are published yet.** The method needs two things that publishable 2026 data does not provide:
- **Every importer's and exporter's monthly totals.** EIA publishes other countries' crude imports only annually and only to 2020, and no exports by country.
- **A measured prior for the rest of the world.** UN Comtrade's bilateral data may not be republished, and JODI's terms are not confirmed.

With no prior, the method spreads each exporter's oil across importers in proportion to their size, which can draw routes that do not exist. So the page shows measured flows (US imports) and measured production, and states the gap. Tier C will run once a defensible prior and totals are available.

**One-minute answer: "What are the modeled arcs?"** They are not measured trade. IPF takes each country's total exports and imports and a starting guess of who trades with whom, and adjusts the guess until every total matches. The result is only as good as the starting guess, and for 2026 I could not get a publishable one, so I publish the measured US flows and production instead of pretending to know the rest.

## Sources

- EIA, Weekly Petroleum Status Report, Appendix B: https://www.eia.gov/petroleum/supply/weekly/pdf/appendixb.pdf
- MacKinlay, A. Craig (1997), "Event Studies in Economics and Finance," Journal of Economic Literature 35(1), pages 13 to 39: https://ideas.repec.org/a/aea/jeclit/v35y1997i1p13-39.html
- Kilian, Lutz (2009), "Not All Oil Price Shocks Are Alike," American Economic Review 99(3), as summarized and confirmed in a 2024 replication: https://arxiv.org/html/2409.00769v2
- Caldara, Dario and Matteo Iacoviello (2022), "Measuring Geopolitical Risk," American Economic Review 112(4), pages 1194 to 1225. Data: https://www.matteoiacoviello.com/gpr.htm
- EIA, Risk of oil supply disruptions can have an immediate effect on oil prices (Jan 31, 2020): https://www.eia.gov/todayinenergy/detail.php?id=42675
- EIA, Saudi Arabia crude oil production outage (2019): https://www.eia.gov/todayinenergy/detail.php?id=41413
- EIA, Prices increased sharply in the first quarter of 2026 (Apr 7, 2026): https://www.eia.gov/todayinenergy/detail.php?id=67424
- EIA, Prices and refinery margins in the third quarter (Oct 5, 2026): https://www.eia.gov/todayinenergy/detail.php?id=68245
- EIA, Strait of Hormuz remains critical oil chokepoint (June 16, 2025): https://www.eia.gov/todayinEnergy/detail.php?id=65504
- FRED, WTI and Brent daily prices: https://fred.stlouisfed.org/series/DCOILWTICO and https://fred.stlouisfed.org/series/DCOILBRENTEU
