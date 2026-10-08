# Spike explanations

Generated 2026-10-07 by `explain_spikes.py` from `data/spikes_explained.csv` and the database. Each explanation attributes its claims to the cited source and assigns no single cause: research such as Kilian (2009) finds supply shocks have historically explained less of oil price movement than shifts in demand and fear of shortage. The context lines are measured values from this project's database.

**Hand-checked: 0 of 12.** Unchecked explanations stay off the public pages.

## S01. 1986 price collapse (Dec 1985 to Apr 1986)

*Status: not yet hand-checked.*

The IMF reports that Saudi Arabia's production had dropped to 2.3 million b/d by 1985, after which it raised production, abandoned official pricing and adopted a spot pricing mechanism. The IMF cites weak demand and rising non-OPEC output as the background.

Sources: [IMF Finance & Development, Down the Slide (Dec 2015)](https://www.imf.org/external/pubs/ft/fandd/2015/12/baffes.htm); [EIA Short-Term Energy Outlook, 2Q 1986 (scanned PDF)](https://www.eia.gov/outlooks/steo/archives/2Q86.pdf) (accessed 2026-10-07).

**Context from the database**

- WTI spot (EIA): $25.56 at the start, high $26.53 on Jan 6, 1986, low $10.25 on Mar 31, 1986, $13.38 at the end.
- Before it began: no tightness score (scores start in November 1995).
- Spikes found by the rules in this window: 1 crash, 15 daily, 1 drawdown, 1 surge.

Note for checking: Source check Oct 7: the EIA PDF is a scanned image and could not be read by machine; read it by eye before adding EIA's monthly figures (netback pricing, 4.5 million b/d in January 1986).

## S02. 1990 invasion of Kuwait and the January 1991 fall (Jul 1990 to Feb 1991)

*Status: not yet hand-checked.*

EIA reports peak lost production of about 4.3 million b/d of combined Iraqi and Kuwaiti crude. On January 16, 1991 the US announced air strikes and a release from the Strategic Petroleum Reserve; the Department of Energy says the release helped calm the global oil market and prices began to moderate.

Sources: [EIA Today in Energy, Effects of crude oil supply disruptions](https://www.eia.gov/todayinenergy/detail.php?id=730); [US Department of Energy, History of SPR releases](https://www.energy.gov/hgeo/opr/history-spr-releases) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $17.70 at the start, high $41.45 on Sep 27, 1990, low $17.58 on Jul 17, 1990, $19.50 at the end.
- WTI spot (EIA): $18.67 at the start, high $41.07 on Oct 11, 1990, low $17.43 on Feb 22, 1991, $19.28 at the end.
- Brent 20-day realized volatility peaked at 176% on Jan 24, 1991, higher than 100% of all days since 1987 (spikes.py).
- Before it began: no tightness score (scores start in November 1995).
- Large speculators' net position in WTI: -6.1% of open interest before, 0.1% at the end (CFTC, dated to release).
- Spikes found by the rules in this window: 5 crash, 36 daily, 2 drawdown, 2 surge.

Note for checking: Source check Oct 7: the $16 and $28 price figures were removed (from EIA's Energy Kids timeline, not the cited article).

## S03. 1997 to 1998 lows (Oct 1997 to Dec 1998)

*Status: not yet hand-checked.*

EIA's April 1998 outlook named increased worldwide production, low winter fuel demand and the Asian financial crisis as contributors to falling prices, and noted that Iraq was increasing production. EIA notes WTI fell to almost $10 per barrel in late 1998.

Sources: [EIA Short-Term Energy Outlook, April 1998](https://www.eia.gov/outlooks/steo/archives/apr98.pdf); [EIA STEO supplement, Why are oil prices so high?](https://www.eia.gov/outlooks/steo/special/pdf/high-oil-price.pdf) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $19.87 at the start, high $21.29 on Oct 3, 1997, low $9.10 on Dec 10, 1998, $10.54 at the end.
- WTI spot (EIA): $21.02 at the start, high $22.86 on Oct 3, 1997, low $10.82 on Dec 10, 1998, $12.14 at the end.
- Brent 20-day realized volatility peaked at 85% on Apr 14, 1998, higher than 98% of all days since 1987 (spikes.py).
- Before it began: US tightness +2 (tight) in the week ending Sep 26, 1997, average +2.0 over the 4 prior weeks; futures curve flat (weekly_reading).
- Large speculators' net position in WTI: -3.4% of open interest before, -4.3% at the end (CFTC, dated to release).
- Spikes found by the rules in this window: 2 crash, 13 daily, 4 drawdown.

Note for checking: Source check Oct 7: the OPEC 10% quota increase was removed (not in the cited sources).

## S04. The run to the 2008 peak and the 2008 to 2009 crash (Jan 2007 to Feb 2009)

*Status: not yet hand-checked.*

The Federal Reserve's 2008 annual report links the rise of WTI above $145 by mid-July 2008 to robust demand, especially from emerging economies, and restrained near-term supply, and the fall that followed to financial market turmoil and the downturn in global activity, with WTI down about 75% from its peak by January 2009.

Sources: [Federal Reserve Board, Annual Report 2008](https://www.federalreserve.gov/boarddocs/rptcongress/annual08/sec1/c1.htm); [EIA working paper, Factors influencing oil prices](https://www.eia.gov/workingpapers/pdf/factors_influencing_oil_prices.pdf) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $58.49 at the start, high $143.95 on Jul 3, 2008, low $33.73 on Dec 26, 2008, $44.41 at the end.
- WTI spot (EIA): $60.77 at the start, high $145.31 on Jul 3, 2008, low $30.28 on Dec 23, 2008, $44.15 at the end.
- Brent 20-day realized volatility peaked at 117% on Jan 5, 2009, higher than 99% of all days since 1987 (spikes.py).
- Before it began: US tightness -2 (loose) in the week ending Dec 29, 2006, average -1.8 over the 4 prior weeks; futures curve contango (weekly_reading).
- Large speculators' net position in WTI: 1.7% of open interest before, 2.4% at the end (CFTC, dated to release).
- Spikes found by the rules in this window: 4 crash, 37 daily, 5 drawdown, 1 spread, 3 surge.

Note for checking: Researchers disagree about the role of speculation in 2008; the working paper surveys the views.

## S05. 2011: Libya and the Brent minus WTI blowout (Feb 2011 to Dec 2011)

*Status: not yet hand-checked.*

EIA reports Brent rose $15 between February 18 and March 2, 2011 as the market coped with the loss of 1.5 million b/d of Libyan exports, while rising inland supply and transport bottlenecks near Cushing held WTI at a discount. EIA puts the record Brent premium at $29.70 on September 22, 2011.

Sources: [EIA Today in Energy, Brent averages over $100 in 2011](https://www.eia.gov/todayinenergy/detail.php?id=4550); [EIA Today in Energy, WTI-Brent spread narrows](https://www.eia.gov/todayinenergy/detail.php?id=4170) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $100.40 at the start, high $126.64 on May 2, 2011, low $99.25 on Feb 8, 2011, $108.09 at the end.
- WTI spot (EIA): $89.54 at the start, high $113.39 on Apr 29, 2011, low $75.40 on Oct 4, 2011, $98.83 at the end.
- Brent 20-day realized volatility peaked at 43% on May 31, 2011, higher than 83% of all days since 1987 (spikes.py).
- Before it began: US tightness -2 (loose) in the week ending Jan 28, 2011, average -2.0 over the 4 prior weeks; futures curve contango (weekly_reading).
- Large speculators' net position in WTI: 9.6% of open interest before, 10.9% at the end (CFTC, dated to release).
- Spikes found by the rules in this window: 3 daily, 1 drawdown, 4 spread.

Note for checking: Source check Oct 7: in this project's daily spot data the spread was $28.92 on Sep 22, 2011 and peaked at $29.59 on Sep 23; EIA's $29.70 is likely a different price basis.

## S06. The 2014 to 2016 collapse (Jun 2014 to Feb 2016)

*Status: not yet hand-checked.*

EIA reports Brent and WTI fell from monthly averages of $112 and $105 in June 2014 to $62 and $59 in December, as robust global production exceeded demand, and US crude output rose 1.2 million b/d in 2014. EIA reports a sustained excess of supply over demand in 2015, and prices ended 2015 below $40.

Sources: [EIA Today in Energy, Crude oil prices down sharply in fourth quarter of 2014](https://www.eia.gov/todayinenergy/detail.php?id=19451); [EIA Today in Energy, Crude oil prices ended 2015 lower](https://www.eia.gov/todayinenergy/detail.php?id=24432) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $109.34 at the start, high $115.19 on Jun 19, 2014, low $26.01 on Jan 20, 2016, $35.92 at the end.
- WTI spot (EIA): $103.07 at the start, high $107.95 on Jun 20, 2014, low $26.19 on Feb 11, 2016, $32.74 at the end.
- Brent 20-day realized volatility peaked at 74% on Feb 17, 2016, higher than 97% of all days since 1987 (spikes.py).
- Before it began: US tightness +1 (normal) in the week ending May 30, 2014, average +1.5 over the 4 prior weeks; futures curve backwardation (weekly_reading).
- Large speculators' net position in WTI: 25.9% of open interest before, 11.6% at the end (CFTC, dated to release).
- Spikes found by the rules in this window: 7 crash, 20 daily, 4 drawdown, 3 surge.

Note for checking: Source check Oct 7: removed '50%', 'weakening demand', 'fewer supply disruptions' (EIA reports disruptions rose in 2014) and the OPEC 30 million b/d target (not in the cited articles).

## S07. September 2019 Abqaiq attack (Sep 2019 to Sep 2019)

*Status: not yet hand-checked.*

EIA reports an attack on September 14, 2019 damaged the Abqaiq processing facility and the Khurais field. On September 16, the first full trading day after, Brent and WTI had their largest one-day increase in a decade, and both fell on September 17 after Saudi Aramco said output would be restored by the end of the month.

Sources: [EIA Today in Energy, Saudi Arabia crude oil production outage](https://www.eia.gov/todayinenergy/detail.php?id=41413) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $61.25 at the start, high $68.42 on Sep 16, 2019, low $60.99 on Sep 30, 2019, $60.99 at the end.
- WTI spot (EIA): $54.76 at the start, high $63.10 on Sep 16, 2019, low $54.09 on Sep 30, 2019, $54.09 at the end.
- Brent 20-day realized volatility peaked at 58% on Sep 18, 2019, higher than 93% of all days since 1987 (spikes.py).
- Before it began: US tightness +2 (tight) in the week ending Sep 6, 2019, average +0.8 over the 4 prior weeks; futures curve backwardation (weekly_reading).
- Large speculators' net position in WTI: 20.6% of open interest before, 20.7% at the end (CFTC, dated to release).
- Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): Hormuz 47.1 (94%), Bab el-Mandeb 17.4 (103%), Cape of Good Hope 12.8 (106%).
- Spikes found by the rules in this window: 2 daily.

Note for checking: The article does not state the barrels taken offline (see news reader demo).

## S08. April 2020: WTI below zero (Mar 2020 to May 2020)

*Status: not yet hand-checked.*

The CFTC reports the May 2020 WTI futures contract settled at -$37.63 on April 20, the day before it expired. EIA reports Cushing storage was 76% full as of April 17 and consumption had sharply declined. A CFTC staff report described several coinciding factors without assigning a root cause.

Sources: [EIA Today in Energy, Low liquidity and limited storage pushed WTI futures below zero](https://www.eia.gov/todayinenergy/detail.php?id=43495); [CFTC staff interim report on WTI trading around April 20, 2020](https://www.cftc.gov/PressRoom/PressReleases/8315-20) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $52.52 at the start, high $52.52 on Mar 2, 2020, low $9.12 on Apr 21, 2020, $34.15 at the end.
- WTI spot (EIA): $46.78 at the start, high $47.27 on Mar 3, 2020, low $-36.98 on Apr 20, 2020, $35.57 at the end.
- Brent 20-day realized volatility peaked at 349% on Apr 24, 2020, higher than 100% of all days since 1987 (spikes.py).
- Before it began: US tightness +0 (normal) in the week ending Feb 28, 2020, average +0.5 over the 4 prior weeks; futures curve flat (weekly_reading).
- Large speculators' net position in WTI: 19.8% of open interest before, 25.4% at the end (CFTC, dated to release).
- Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): Hormuz 43.0 (86%), Bab el-Mandeb 19.5 (115%), Cape of Good Hope 12.0 (100%).
- Spikes found by the rules in this window: 2 crash, 47 daily, 4 drawdown, 1 surge.

Note for checking: Source check Oct 7: -$37.63 is from the CFTC, not EIA. EIA's daily spot WTI series (this database) shows -$36.98 that day; futures settlement and spot are different prices.

## S09. 2022 Russia invasion spike (Feb 2022 to Jun 2022)

*Status: not yet hand-checked.*

EIA reports the front-month Brent futures contract settled above $100 on February 28, 2022, after Russia's further invasion of Ukraine. EIA reports that on March 8 the invasion combined with low global inventories lifted the price to its highest inflation-adjusted level since 2014.

Sources: [EIA Today in Energy, Crude oil prices in 2022](https://www.eia.gov/todayinenergy/detail.php?id=55079); [EIA Today in Energy, Crude oil prices rise above $100](https://www.eia.gov/todayinEnergy/detail.php?id=51498) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $90.24 at the start, high $133.18 on Mar 8, 2022, low $90.24 on Feb 1, 2022, $119.78 at the end.
- WTI spot (EIA): $88.22 at the start, high $123.64 on Mar 8, 2022, low $88.16 on Feb 2, 2022, $107.76 at the end.
- Brent 20-day realized volatility peaked at 92% on Mar 28, 2022, higher than 98% of all days since 1987 (spikes.py).
- Before it began: US tightness +2 (tight) in the week ending Jan 28, 2022, average +2.0 over the 4 prior weeks; futures curve backwardation (weekly_reading).
- Large speculators' net position in WTI: 17.8% of open interest before, 17.5% at the end (CFTC, dated to release).
- Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): Hormuz 59.8 (120%), Bab el-Mandeb 20.3 (119%), Cape of Good Hope 10.0 (83%).
- Spikes found by the rules in this window: 4 daily, 2 surge.

Note for checking: Source check Oct 7: Feb 28 is a futures settlement; this database's EIA spot Brent first passed $100 on Feb 14, 2022 and was $133.18 on Mar 8. The $134 figure was removed (not in the cited articles).

## S10. Red Sea shipping attacks from late 2023 (a disruption without a price spike) (Nov 2023 to Feb 2024)

*Status: not yet hand-checked.*

EIA reports attacks on commercial ships in the Red Sea began in November 2023; crude flows through Bab el-Mandeb were 18% lower in December than in January to November, and some vessels went around southern Africa. EIA reports Brent traded in a range, from $82 in the week before the attacks to $79 on January 18, 2024.

Sources: [EIA Today in Energy, Red Sea attacks increase shipping times and freight rates](https://www.eia.gov/todayinenergy/detail.php?id=61363) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $86.92 at the start, high $89.02 on Nov 2, 2023, low $74.11 on Dec 12, 2023, $84.57 at the end.
- WTI spot (EIA): $81.05 at the start, high $83.04 on Nov 2, 2023, low $68.27 on Dec 12, 2023, $79.22 at the end.
- Brent 20-day realized volatility peaked at 46% on Nov 7, 2023, higher than 86% of all days since 1987 (spikes.py).
- Before it began: US tightness +1 (normal) in the week ending Oct 27, 2023, average +0.5 over the 4 prior weeks; futures curve backwardation (weekly_reading).
- Large speculators' net position in WTI: 18.5% of open interest before, 11.5% at the end (CFTC, dated to release).
- Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): Hormuz 44.6 (89%), Bab el-Mandeb 19.4 (114%), Cape of Good Hope 14.0 (116%).

Note for checking: Compare with Cape of Good Hope and Bab el-Mandeb transits in chokepoint_transit. The database shows Bab el-Mandeb tanker transits at 114% of the 2019 to 2025 median over Nov 2023 to Feb 2024; that median includes the low rerouting years 2024 and 2025, and ship counts are not barrels, so it does not contradict EIA's 18% lower crude flow.

## S11. June 2025 Israel and Iran fighting (Jun 2025 to Jun 2025)

*Status: not yet hand-checked.*

EIA reports Brent (futures, per the article's link) rose from $69 on June 12 to $74 on June 13, 2025, and that maritime traffic through the Strait of Hormuz was not blocked as of June 16.

Sources: [EIA Today in Energy, Strait of Hormuz remains critical oil chokepoint](https://www.eia.gov/todayinEnergy/detail.php?id=65504) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $70.84 at the start, high $80.37 on Jun 19, 2025, low $68.15 on Jun 30, 2025, $68.15 at the end.
- WTI spot (EIA): $68.73 at the start, high $75.89 on Jun 18, 2025, low $65.45 on Jun 24, 2025, $66.30 at the end.
- Brent 20-day realized volatility peaked at 53% on Jun 24, 2025, higher than 91% of all days since 1987 (spikes.py).
- Before it began: US tightness +2 (tight) in the week ending Jun 6, 2025, average +1.2 over the 4 prior weeks; futures curve not available (EIA futures end April 2024) (weekly_reading).
- Large speculators' net position in WTI: 8.4% of open interest before, 11.9% at the end (CFTC, dated to release).
- Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): Hormuz 58.5 (117%), Bab el-Mandeb 11.2 (66%), Cape of Good Hope 16.6 (139%).
- Spikes found by the rules in this window: 1 daily.

Note for checking: A risk event: no barrels lost per the source. This database's EIA spot Brent was $70.84 and $76.00 on those days.

## S12. The 2026 Strait of Hormuz disruption (Feb 2026 to Oct 2026)

*Status: not yet hand-checked.*

EIA reports Brent front-month futures rose from $61 at the start of 2026 to $118 at the end of the first quarter, surpassing $100 on March 12, as Iraq, Saudi Arabia and the UAE shut in oil production; EIA says the quarter's increase was the largest on an inflation-adjusted basis in data going back to 1988. The episode's sub-events are rows W01 to W14 of data/iran_war_2026.csv.

Sources: [EIA Today in Energy, Prices increased sharply in the first quarter of 2026](https://www.eia.gov/todayinenergy/detail.php?id=67424); [IEA commentary on the Strait of Hormuz shock (not reachable at iea.org on Oct 7)](https://www.iea.org/commentaries/how-global-oil-supplies-have-readjusted-to-help-fill-the-huge-gap-left-by-the-strait-of-hormuz-shock) (accessed 2026-10-07).

**Context from the database**

- Brent spot (EIA): $77.24 at the start, high $138.21 on Apr 7, 2026, low $68.53 on Jul 2, 2026, $125.44 at the end.
- WTI spot (EIA): $71.13 at the start, high $114.58 on Apr 7, 2026, low $69.60 on Jul 6, 2026, $96.24 at the end.
- Brent 20-day realized volatility peaked at 112% on Apr 17, 2026, higher than 99% of all days since 1987 (spikes.py).
- Before it began: US tightness +1 (normal) in the week ending Feb 27, 2026, average +2.0 over the 4 prior weeks; futures curve not available (EIA futures end April 2024) (weekly_reading).
- Large speculators' net position in WTI: 8.2% of open interest before, 5.8% at the end (CFTC, dated to release).
- Tanker transits, average per day in the window against the 2019 to 2025 median (IMF PortWatch): Hormuz 2.7 (5%), Bab el-Mandeb 12.1 (71%), Cape of Good Hope 19.6 (163%).
- Spikes found by the rules in this window: 2 crash, 29 daily, 2 drawdown, 3 spread, 5 surge.

Note for checking: Source check Oct 7: '7.5 million b/d shut in during March' is not in EIA article 67424 and was removed. The IEA figure (flows from about 20 to an average of 2.7 million b/d in March to May) was seen only in a reprint credited to the IEA, dated June 29, 2026; confirm at iea.org before use. $61 and $118 are futures; EIA spot Brent was $126.69 on March 31.

