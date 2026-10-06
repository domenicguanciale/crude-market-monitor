# Notes on EVENTS_STARTER.csv

Built October 5, 2026. 21 rows: 12 attacks, 4 weather events, 2 blockades, 1 cyber incident, 1 accident, 1 agreement. 16 rows have a date precise enough for a daily study. 5 do not yet.

This is a starter table. It was assembled by an AI assistant from summaries of the source pages, so it will contain errors. Checking it is part of the project.

## Your first job: check it

1. Open the source link for each row and confirm the date, the volume, and the price move.
2. Record the result in a new column called `hand_checked` (correct, corrected, or could not confirm).
3. Count how many rows were right the first time. Report that number in the README. A measured error rate is the "AI did real work and I tested it" evidence reviewers look for.

## What each column means

| Column | Meaning |
|---|---|
| event_date | The day it happened, local time |
| first_trading_day_after | Day zero for the study: the first day prices could react. Weekends and after-close events roll forward. US and UK market holidays are NOT handled, so check each one |
| facility_type | Refinery, processing plant, export terminal, pipeline, field, tanker or shipping lane, other |
| cause | Attack, blockade, weather, accident, cyber, agreement |
| physical_supply_lost | "yes" if barrels actually went offline. "no" if it was a risk event or a rerouting |
| capacity_offline_bpd | Barrels per day offline. Blank when no reliable figure was found |
| capacity_note | What the number measures. Refinery runs, crude production, and pipeline capacity are different things and should not be mixed without saying so |
| usable_for_daily_study | "no" means the source gives only a month, or the event is a campaign with no single date |
| overlaps_other_event | Other rows whose 20-day windows overlap this one |
| confidence | High, medium, or low, based on how directly the source supports the date and volume |

## The 2026 Strait of Hormuz episode changes the project

Rows E16 to E21 are one connected episode, and it is the largest in the table by a wide margin.

- EIA reports military action on February 28, 2026 led to the de facto closure of the strait, with 7.5 million barrels a day of production shut in during March.
- IEA reports flows through the strait fell from about 20 million barrels a day to an average of 2.7 million in March through May.
- Brent rose from $61 at the start of the year to $118 by March 31. The gap between Brent and WTI widened from about $4 to $25.
- A memorandum in mid-June eased prices, and escalations on July 7 and September 9 pushed them back up.

What that means for the analysis:

- **Treat it as one episode with sub-events.** The 20-day windows overlap, so the sub-events are not independent observations.
- **Report results with and without 2026.** One episode this large will drive any average.
- **Keep the wording neutral.** This is a live conflict. Record dates, volumes, and prices only.

## Update, October 5, 2026: the war rows

Rows E16 to E21 are now superseded by `data/iran_war_2026.csv` (W01 to W14). That file replaces the Wikipedia-only details with news-agency or official sources, records both values where sources disagree (`date_flag`), and adds the leads below that could be dated: the Kuwait and UAE cuts, the ceasefire and its extension, the blockade, the strait reopening and re-closure. Check the W rows instead of E16 to E21. Fill `hand_checked` in either CSV, then run `events.py`.

Still open as leads: QatarEnergy's LNG force majeure (no exact date found, and gas rather than crude), the Fujairah terminal attack, the May 2026 US escort operation, individual tanker strikes, Novorossiysk, and the September pipeline attacks affecting Saudi supply.

## Weakest rows

| Row | Problem |
|---|---|
| E18 Iraq force majeure | The news report EIA links to is dated March 20. Wikipedia says March 17. The volume comes from Wikipedia only |
| E16 Start of the Hormuz episode | The February 28 date needs confirming in a news source |
| E05 Abqaiq | The 5.7 million figure is from general knowledge. EIA's page gives Abqaiq's capacity as 7 million barrels a day, not the amount disrupted |
| E01 Fort McMurray, E03 Harvey, E07 Texas freeze | The source confirms the month. The exact start date is from general knowledge |
| E08 Colonial | Capacity is not in the fetched source |
| E12 Keystone | Date of full restart not confirmed |
| E17, E20 | Details beyond the date rely on Wikipedia |

Wikipedia is used as a pointer for 2026 dates. Replace it with a news or agency source for any row you keep.

## Rows that need a date before they can be used

E02 Nigeria 2016, E10 Libya December 2021, E11 Libya April 2022, E13 Red Sea, E14 Russian refineries. Each is a campaign or a gradual event. Either find the date of one specific incident or analyze these at weekly frequency.

## Leads not yet in the table

- Drone attacks on the Novorossiysk terminal in the third quarter of 2026 (EIA mentions them without dates).
- Pipeline attacks affecting Saudi supply in September 2026, after which Saudi Aramco halted October deliveries to some European refiners (EIA, no dates).
- Individual tanker strikes in March through September 2026.
- The UAE's output falling by more than half around March 16, 2026.
- The May and June 2019 tanker incidents near Fujairah.
- Libya's January 2020 blockade and the August 2024 shutdown.
- Hurricanes Katrina and Rita in 2005, and the 2011 Libyan civil war, for a longer history.

## Sources

- EIA, Saudi Arabia crude oil production outage (2019): https://www.eia.gov/todayinenergy/detail.php?id=41413
- EIA, Risk of oil supply disruptions can have an immediate effect on oil prices (Jan 31, 2020): https://www.eia.gov/todayinenergy/detail.php?id=42675
- EIA, Unplanned global oil supply disruptions (June 9, 2016): https://www.eia.gov/todayinEnergy/detail.php?id=26592
- EIA, Hurricane Harvey (2017): https://www.eia.gov/todayinenergy/detail.php?id=32852
- EIA, Cold weather led to refinery shutdowns (2021): https://www.eia.gov/todayinenergy/detail.php?id=46936
- EIA, Average US retail gasoline price exceeds $3.00 (May 18, 2021): https://www.eia.gov/todayinenergy/detail.php?id=47996
- EIA, Hurricane Ida (Sept 16, 2021): https://www.eia.gov/todayinenergy/detail.php?id=49576
- EIA, Conflict in Libya (2022): https://www.eia.gov/todayinenergy/detail.php?id=53419
- EIA, Red Sea attacks (2024): https://www.eia.gov/todayinenergy/detail.php?id=61363
- EIA, Strait of Hormuz remains critical oil chokepoint (June 16, 2025): https://www.eia.gov/todayinEnergy/detail.php?id=65504
- EIA, Prices increased sharply in the first quarter of 2026 (Apr 7, 2026): https://www.eia.gov/todayinenergy/detail.php?id=67424
- EIA, Prices and refinery margins in the third quarter (Oct 5, 2026): https://www.eia.gov/todayinenergy/detail.php?id=68245
- EIA press release, April 7, 2026: https://www.eia.gov/pressroom/releases/press586.php
- EIA press release, July 7, 2026: https://www.eia.gov/pressroom/releases/press590.php
- IEA commentary on the Strait of Hormuz shock (June 22, 2026): https://www.iea.org/commentaries/how-global-oil-supplies-have-readjusted-to-help-fill-the-huge-gap-left-by-the-strait-of-hormuz-shock
- Reuters via SWI swissinfo.ch, Russian refining capacity (Apr 15, 2024): https://www.swissinfo.ch/eng/exclusive-russia-restoring-oil-refining-capacity-knocked-out-by-drones/75776966
- Pipeline and Gas Journal, Keystone shutdown (Dec 2022): https://pgjonline.com/news/2022/december/tc-energy-s-keystone-pipeline-shut-after-oil-release-into-kansas-creek
- Business Day, Gulf of Oman tanker attacks (June 13, 2019): https://www.businessday.co.za/bd/markets/2019-06-13-oil-prices-jump-after-attacks-on-two-tankers-in-the-gulf-of-oman/
- Wikipedia, 2026 Strait of Hormuz crisis (pointer only): https://en.wikipedia.org/wiki/2026_Strait_of_Hormuz_crisis
