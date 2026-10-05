# Data specification

Checked October 5, 2026. Hand this file to Claude Code so it does not guess. Items marked UNVERIFIED must be confirmed by Claude Code against the live API before use.

## 1. Getting a key

- Register at https://www.eia.gov/opendata/register.php with name, email, a category (choose student), and a reason.
- It is free. The key arrives by email. EIA does not state how long that takes.
- You must credit "U.S. Energy Information Administration" as the source and may not use the EIA logo.
- EIA's bulk download facility needs no key.

## 2. API basics

| Item | Value |
|---|---|
| Base URL | `https://api.eia.gov/v2/` |
| Key | Passed in the URL as `?api_key=YOUR_API_KEY`. It cannot go in a header |
| Getting values | Add `/data` to a route. Without `/data` the API returns metadata: the available frequencies and facets |
| Facet | A filter on the data, such as one series. Example: `&facets[series][]=WCESTUS1` |
| Columns | `&data[]=value` |
| Frequency | `&frequency=weekly` (or `daily`, `monthly`) |
| Dates | `&start=2015-01-01&end=2026-10-01` |
| Sorting | `&sort[0][column]=period&sort[0][direction]=asc` |
| Paging | `&offset=0&length=5000` |
| Row limit | 5,000 rows per JSON response. Page with `offset` for more |
| Rate limit | Not published. A third-party guide quotes EIA guidance of under about 9,000 requests an hour and under 5 a second |

A weekly series since 1982 is about 2,300 rows, so each series fits in one request.

## 3. Series

Series IDs were confirmed on EIA's history pages. Routes are a different matter: see the note under the table.

| What | Series ID | Units | Frequency | Starts | ID verified |
|---|---|---|---|---|---|
| WTI spot price, Cushing | `RWTC` | Dollars per barrel | Weekly and daily | Jan 1986 | Yes |
| Brent spot price | `RBRTE` | Dollars per barrel | Weekly and daily | May 1987 | Yes |
| US crude stocks excluding the strategic reserve | `WCESTUS1` | Thousand barrels | Weekly | Aug 20, 1982 | Yes |
| US refinery utilization | `WPULEUS3` | Percent of operable capacity | Weekly | Nov 2, 1990 | Yes |
| US crude production | `WCRFPUS2` | Thousand barrels per day | Weekly | Jan 7, 1983 | Yes |
| US distillate fuel stocks | `WDISTUS1` | Thousand barrels | Weekly | Aug 20, 1982 | Yes |
| US crude exports | `WCREXUS2` | Thousand barrels per day | Weekly | Feb 1991 | Yes |

The last two are additions to the original four. Section 8 of PROJECT_BRIEF.md explains why.

**Routes**

| Data | Route | Status |
|---|---|---|
| Weekly stocks | `petroleum/stoc/wstk` | Confirmed by a third-party guide, not by EIA's own page |
| Spot prices | `petroleum/pri/spt` | UNVERIFIED |
| Refinery utilization | `petroleum/pnp/wiup` | UNVERIFIED |
| Weekly supply estimates, including production | `petroleum/sum/sndw` | UNVERIFIED |
| Weekly exports | `petroleum/move/wkly` | UNVERIFIED |

EIA's route browser would not load for checking. Claude Code should discover the routes from the API itself:

1. Request `https://api.eia.gov/v2/petroleum?api_key=YOUR_API_KEY` to list the child routes.
2. For a candidate route, request `.../v2/petroleum/stoc/wstk/facet/series?api_key=YOUR_API_KEY` to list its series IDs.
3. Confirm the series ID appears before requesting data.

## 4. Example request

```
https://api.eia.gov/v2/petroleum/stoc/wstk/data/?api_key=YOUR_API_KEY&frequency=weekly&data[]=value&facets[series][]=WCESTUS1&sort[0][column]=period&sort[0][direction]=asc&offset=0&length=5000
```

The parameter pattern follows EIA's documentation. The route is the third-party-confirmed one. Test it before building on it.

## 5. Release schedule

- The Weekly Petroleum Status Report comes out Wednesdays at 10:30 a.m. Eastern.
- After a federal holiday it usually moves to Thursday, at 11:00 a.m. or 12:00 p.m.
- The history page checked today showed a release on September 30, 2026 and the next on October 7, 2026.
- Each report covers the week ending the previous Friday. So the number for a week is not public until five days after that week ends. The backtest must respect this (see METHODS.md, section 3).

## 6. How EIA defines the five-year range

From Appendix B of the Weekly Petroleum Status Report:

> "The 5-year ranges provide the reader with the highest and lowest weekly stock levels for a given product by region over the equivalent week during the prior five years."

So EIA's range is the high and low for the same week in the prior five years. The current year is not included.

## 7. Backup source

FRED (the St. Louis Fed's data site) carries the two price series and needs no key for manual downloads.

| Series | FRED ID | Checked |
|---|---|---|
| WTI daily | `DCOILWTICO` | Yes. $96.16 on Sept 29, 2026 |
| Brent daily | `DCOILBRENTEU` | Yes. $113.96 on Sept 29, 2026 |
| Crude stocks | Not found under `WCESTUS1` | The page returned an error |

EIA's history pages also offer a spreadsheet download for each series, which works without a key.

## 8. Data quirks to handle

- **Revisions.** EIA revises weekly data "only if the revision is expected to substantively affect understanding of U.S. petroleum supplies." Weekly figures are sample-based estimates, and the monthly data that follows can differ.
- **Weeks end on Friday.** Store the week-ending date and derive the week number from it.
- **Week 53.** Some years have 53 weeks. METHODS.md gives the rule.
- **The adjustment line.** EIA's balance has a "Crude Oil Supply Adjustment" item, formerly "Unaccounted-for Crude Oil." It affects how production and stocks reconcile. It does not need handling in version 1, but know it exists.
- **2020 and 2026 are abnormal years.** The pandemic and the Strait of Hormuz closure both sit inside or next to the five-year window. Say in the README how you treat them.
- **Units differ.** Stocks are in thousand barrels, production and exports in thousand barrels per day, utilization in percent.

## 9. What was not verified

- Four of the five routes in section 3.
- The exact rate limit, which EIA does not publish.
- How quickly the key email arrives.
- Any methodology changes to weekly production since 2023.
- A FRED ID for weekly crude stocks.

## 10. Sources

- EIA Open Data: https://www.eia.gov/opendata/
- EIA API registration: https://www.eia.gov/opendata/register.php
- EIA API technical documentation: https://www.eia.gov/opendata/documentation.php
- EIA history pages, pattern `https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=SERIES_ID&f=W`, checked for all seven series
- EIA Weekly Petroleum Status Report schedule: https://www.eia.gov/petroleum/supply/weekly/schedule.php
- EIA Weekly Petroleum Status Report, Appendix B: https://www.eia.gov/petroleum/supply/weekly/pdf/appendixb.pdf
- FRED, WTI: https://fred.stlouisfed.org/series/DCOILWTICO
- FRED, Brent: https://fred.stlouisfed.org/series/DCOILBRENTEU
- Third-party guide to the EIA API (route and rate guidance): https://www.oilpriceapi.com/eia-api
