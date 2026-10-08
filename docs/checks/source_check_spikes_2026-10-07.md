# Source check: spike explanations, first drafts (October 7, 2026)

The source-checker opened every source linked in `data/spikes_explained.csv` (episodes S01 to S12) and compared each specific date, price and volume in the first-draft explanations with the source text. It made no edits and filled no `hand_checked` values.

**Result on the first drafts: 44 of 62 claims matched their cited source (71%); 5 of 12 episodes were fully correct.** The drafts were then corrected using only wording the checker found in the sources. All 12 remain **not hand-checked** until the user checks them.

| Episode | Suggested status | Claims matched | What was corrected |
|---|---|---|---|
| S01 1986 collapse | could not confirm | 1 / 6 | EIA's 1986 outlook is a scanned PDF that could not be machine-read; the explanation now uses only the IMF article's figures. Read the EIA PDF by eye before adding its monthly numbers |
| S02 1990 to 1991 | corrected | 3 / 6 | Removed $16 and $28 (from EIA's Energy Kids page, not the cited article); "prices fell" changed to the DOE's "began to moderate" |
| S03 1997 to 1998 | corrected | 3 / 4 | Removed an OPEC 10% quota increase not in the sources |
| S04 2008 | correct | 6 / 6 | "attributes" softened to "links" |
| S05 2011 | correct | 4 / 4 | Dropped "about" before 1.5 million b/d; noted that the database spread was $29.59 at its 2011 peak against EIA's $29.70 |
| S06 2014 to 2016 | corrected | 3 / 7 | Removed "50%", "weakening demand", "fewer supply disruptions" (EIA reports disruptions rose) and the OPEC 30 million b/d target; now uses EIA's monthly averages |
| S07 Abqaiq 2019 | correct | 5 / 5 | None |
| S08 April 2020 | corrected | 5 / 6 | -$37.63 is reported by the CFTC, not EIA; EIA's spot -$36.98 comes from this database |
| S09 2022 | corrected | 3 / 5 | February 28 is a futures settlement, not spot; removed $134 (spot was $133.18 in the database) |
| S10 Red Sea 2023 to 2024 | correct | 6 / 6 | "ships" changed to "vessels" (the source's rerouting example is gas carriers) |
| S11 June 2025 | correct | 2 / 2 | Marked the prices as futures, per the article's link |
| S12 2026 | corrected | 3 / 5 | Removed 7.5 million b/d (not in EIA article 67424); added EIA's statement that the quarter's rise was the largest inflation-adjusted increase in data back to 1988; IEA figure moved to the notes until iea.org can be opened |

**Knock-on finding:** row W01 of `data/iran_war_2026.csv` carries the same 7.5 million b/d figure, attributed to the same EIA article. It is now flagged in W01's notes for the user's check.

**What this shows:** AI-drafted explanations built from search summaries contained wrong numbers, wrong attributions and one contradiction. Checking every claim against the source text is necessary before anything is published.
