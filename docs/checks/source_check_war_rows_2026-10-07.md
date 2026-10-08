# Source check: war timeline rows W01 to W14 (Oct 7, 2026)

Checked by the `source-checker` subagent, which has no Edit or Write tools. It opened each cited page (or a syndicated copy of the same article when the page refused), compared every claim in the row with the source text, and checked weekdays with Python. Its statuses are **suggestions only**. `hand_checked` is still blank for every row, and only the user fills it.

The corrections below were applied to `data/iran_war_2026.csv` using verified wording only. Where a page could not be opened, the row says so, and no value was filled in from memory.

## Results

| Row | Suggested status | Claims matched | What changed in the CSV |
|---|---|---|---|
| W01 | corrected | 5 of 6 | The 7.5 million b/d figure now cites EIA press release press586 (April STEO), described as an EIA estimate of crude production shut in during March. It was not in EIA article 67424. The IEA page returned 403, so its figures were matched in a reprint dated June 29, not June 22 |
| W02 | corrected | 2 of 4 | AFP (Mar 1) is now source 1. Event date is Mar 1 (carrier suspensions) and alt date Feb 28 (declaration "on Saturday"). Caixin's weekday labels are off by one day, and the old Mar 2 date came from Caixin |
| W03 | correct | 5 of 5 | None |
| W04 | correct | 6 of 8 | Notes say EIA 67424 supports only the general shut-in, and the Mar 9 Bloomberg video could not be opened |
| W05 | corrected | 3 of 4 | Removed "OPEC 1.89 million b/d", which was not found in an OPEC source. Added the January baseline of just under 3.4 million b/d |
| W06 | correct | 6 of 6 | "developed by" changed to "operated by" |
| W07 | correct | 4 of 4 | Source 2 labelled as Reuters |
| W08 | correct | 3 of 3 | The Reuters copy at Engineering News replaces Mining Weekly (403). The CENTCOM original returned 403 and is worth opening in a browser |
| W09 | corrected | 5 of 7 | The route is "announced by Iran's Ports and Maritime Organisation". The ceasefire is the Lebanon ceasefire. The unsourced -10.42% and -11.11% were removed |
| W10 | correct | 4 of 4 | Notes say both sources are Bloomberg. The user decides whether that meets the agency rule |
| W11 | corrected | 5 of 7 | Removed "temporarily" and "signed digitally" (no source). Added the blockade term from Arab News Pakistan |
| W12 | correct | 4 of 4 | "alleged ceasefire violations". Notes give the two issuing bodies named and CENTCOM's 55 transits |
| W13 | corrected | 6 of 7 | "Three tankers" changed to "Three merchant ships", since only one was described as a tanker. The AP copy URL was not recorded, so source 1 is unchanged |
| W14 | corrected | 4 of 8 | Event name now matches the source: 10 ships claimed by Iran, after US strikes on five Iranian tankers. The old source 1 was dated before the event and was replaced. The unsourced $99.49 settle was removed, so the PRICES DIFFER flag no longer applies |

Total: 62 of 77 claims matched before correction (81%), with 7 rows suggested correct and 7 corrected.

## Pages that refused

The IEA commentary, the Bloomberg video, both CENTCOM pages, Mining Weekly, cdapress and iranwatch returned 403, and local10 returned 404. Syndicated copies were used where they existed.

## Other notes

- The New Straits Times page (old W14 source 1) contained text addressed to automated readers that asked for a specific output format. The checker ignored it. That page is no longer cited.
- Dates where sources still disagree are kept with `alt_date` and `date_flag`. They are not resolved on the user's behalf: W02, W04, W06, W07, W11, W13.
- Weekdays confirmed: Feb 28, 2026 was a Saturday, Mar 1 a Sunday, Mar 2 a Monday, Mar 7 a Saturday, Apr 21 a Tuesday, Jun 20 a Saturday, Jul 7 a Tuesday.
