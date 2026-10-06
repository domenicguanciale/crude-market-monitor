# Project brief: Crude Market Tightness Monitor

Updated October 5, 2026 (second version). Put every file in this pack in one empty folder, open Claude Code there, and paste the kickoff prompt from section 10.

## Files in this pack

| File | What it is | When you use it |
|---|---|---|
| PROJECT_BRIEF.md | This plan | First |
| DATA_SPEC.md | Exact series IDs, API rules, and data quirks | Version 1 |
| METHODS.md | The math in plain language, with interview answers | Versions 1 and 1.5 |
| EVENTS_STARTER.csv | 21 sourced supply disruptions, to be hand-checked | Version 2 |
| EVENTS_NOTES.md | How to check the table and its weak spots | Version 2 |
| FOUNDRY_PLAN.md | The rebuild in Palantir Foundry, the video, the exams | Version 3 |

## 1. The question

When is the oil market tight, and how do prices react when supply is disrupted while it is tight?

## 2. Who it is for

A fuel buyer deciding when to lock in a contract or review a hedge. The tool ends in a decision that person can act on.

## 3. Why this project, and why now

- 2026 has seen a very large oil supply disruption. After military action in late February, traffic through the Strait of Hormuz largely stopped. IEA reports flows fell from about 20 million barrels a day to 2.7 million in March through May. Brent went from $61 to $118 in one quarter, which EIA describes as the largest inflation-adjusted increase in its data going back to 1988.
- On September 29, Brent was $113.96 and WTI was $96.16. That $18 gap says the world is short while the US is comparatively well supplied.
- It extends the supply and demand research already on my resume, with code I wrote.
- It is a small version of what a Palantir Deployment Strategist does, and it doubles as a quantitative project for commodities and energy trading internships.

## 4. Three design changes since the first version

1. **Three inputs to the score, not four.** Crude stocks, distillate stocks, and refinery utilization. Price stays out because it is the outcome. Production becomes a context chart. METHODS.md section 2 explains why.
2. **Add the Brent minus WTI spread as a second gauge.** The score uses US data only. Without the spread, the monitor could read "normal" during a global shortage.
3. **Treat 2026 as one episode.** It dominates the event table. Show every result with and without it.

## 5. Ontology

Define this before writing code. One table per object type.

| Object | Key properties | Links to |
|---|---|---|
| Facility | Name, type, country, barrels per day | Disruption events |
| Disruption event | Date, day zero, cause, barrels per day offline, physical loss yes or no | Facility, sources, weekly reading |
| Price series | Benchmark (WTI, Brent), date, price | Disruption events through price reactions |
| Weekly reading | Week ending, crude stocks, distillate stocks, utilization, production, exports, tightness score, spread | Disruption events in that week |
| Source | Publisher, link, date | Disruption events |

- **Calculated properties:** the tightness score and the Brent minus WTI spread on each weekly reading.
- **Action:** "Flag hedge review." It fires when the score is tight and a new disruption is logged, and alerts the buyer.

## 6. Versions

| Version | What it adds | Time |
|---|---|---|
| 1 | Seven EIA series, five-year comparison, three-input score, spread gauge, Streamlit page, README | About six hours |
| 1.5 | Backtest: after "tight" weeks, what did prices do over four weeks compared with all weeks | Two to three hours |
| 2 | Supply Disruption Event Study: one event study with two questions (see below). Hand-check the event table first. Map of events and chokepoints | Six to eight hours |
| 3 | Rebuild in Palantir Foundry and AIP, video under five minutes | Per FOUNDRY_PLAN.md |
| Ongoing | Post the monitor's read every Monday for eight weeks, misses included | 15 minutes a week |

### Version 2: one event study, two questions

Updated October 5, 2026. Version 2 is a single event study over the hand-checked event table, asking two questions with the same method (METHODS.md section 4: constant-mean abnormal returns, windows of 0 to 1, 0 to 5 and 0 to 20 trading days):

1. **How did oil prices react to each disruption?** Brent and WTI.
2. **How did tech funding costs react?** The NASDAQ Composite, the 10-year Treasury yield, and the ICE BofA high-yield spread. FRED carries the spread only from October 2023, so reactions to earlier events cannot use it.

Rules carried over from the expansion: use only hand-checked events; treat the 2026 Iran war as one episode with sub-events; show every result with and without it.

**Dropped:** the lookup-style scenario calculator (METHODS.md section 6) and the pyvis network graph. **Kept:** the map, because the showcase replay uses it.

**Not started:** the event study itself waits until the event table has been hand-checked.

### Version 1 blocks

| Block | Time | Work |
|---|---|---|
| 1 | 30 min | Register for the EIA key. Create a GitHub account |
| 2 | 90 min | Discover the routes, fetch the seven series, store them. Read every line |
| 3 | 90 min | Five-year comparison and the score, per METHODS.md sections 1 and 2 |
| 4 | 90 min | Streamlit page: score, spread, five charts |
| 5 | 45 min | README with the ontology diagram and the limits |
| 6 | 30 min | Push to GitHub. Record a three-minute walkthrough |

If time runs short, drop exports and production and ship five series.

## 7. Who does what

| Tool | Job | Examples |
|---|---|---|
| Claude Code | Builds. All code lives here | Fetching data, the score, the page, the tests |
| Subagents inside Claude Code | Independent checking, run in parallel | A reviewer that reads new code and explains it back. A checker that compares each event row to its source and reports mismatches |
| This chat (Cowork) | Research, cross-checking, documents | This pack. Checking Claude Code's output when you paste it here. Resume and outreach drafts |
| The Claude Project | Planning and memory across weeks | Weekly plan, deadlines, interview practice using METHODS.md section 9 |
| Palantir Foundry | Version 3 | The rebuild and the video |

Rule for subagents: they check work and gather sources. You and the main session make the design decisions, so you can explain them.

Note: the four research agents I tried to launch from this chat were stopped at the approval step, so I did this research directly. In Claude Code, subagents run from your own machine and you approve them there.

## 8. Tools

| Job | Tool |
|---|---|
| Language | Python |
| Storage | DuckDB, one table per object type |
| Data handling | pandas, requests |
| Charts | Plotly |
| Web page | Streamlit |
| Ontology diagram in the README | Mermaid |
| Map (version 2 and the showcase) | pydeck or Folium in the app; the static showcase draws its own |

## 9. Cautions

- **Measure reactions. Do not claim to predict strikes or prices.**
- **Call it disruption risk.** Title version 2 "Supply Disruption Event Study."
- **Stay neutral.** This year's events are a live conflict. Record dates, volumes, and prices only, with no views on the parties. That matters most for a government-facing employer.
- **The research cuts both ways.** Kilian's work finds supply shocks have historically explained little of oil price movement compared with demand and fear of shortage. Say so. It shows you read the literature.
- **Check the event table.** It was drafted by AI from page summaries. Hand-check at least 20 rows and report the accuracy.
- **Explain every part.** If you cannot, it does not go on the resume.

## 10. Kickoff prompt for Claude Code

```
Read PROJECT_BRIEF.md, DATA_SPEC.md, and METHODS.md. I'm a finance student learning to code, and we are building version 1 today.

Before writing any code:
1. Give me a plan for version 1 as a short numbered list and wait for my approval.
2. Create ONTOLOGY.md from section 5 of the brief.
3. Create CLAUDE.md that summarizes the ontology, the tools in section 8, the scoring rules in METHODS.md sections 1 and 2, and the rules below.

Rules:
- Work in small steps. After each step, explain what the code does in plain language and wait for me.
- Use only the tools in section 8 of the brief.
- Store data in DuckDB with one table per object type.
- Read my EIA API key from a .env file and never commit it.
- Routes in DATA_SPEC.md marked UNVERIFIED must be confirmed against the live API before use. Do not guess a route or a series ID.
- Follow METHODS.md for the five-year comparison and the score. If you think a method is wrong, tell me before changing it.
- Commit to git after each working step with a clear message.
- In the README include a Mermaid diagram of the ontology, the question, the method, and the limits from METHODS.md section 8.

Start with step 1.
```

When version 1 works, add two subagents with this prompt:

```
Create two subagents for this project.
1. "explainer": after any change, reads the changed code and explains in plain language what it does and what could go wrong. It never edits files.
2. "source-checker": given a row of EVENTS_STARTER.csv, opens the source link and reports whether the date, volume, and price move match, quoting the source. It never edits files.
```

## 11. Instructions for the Claude Project

Create a project, upload this pack under Context, and paste this under Instructions:

```
You are my planning partner for one project: the Crude Market Tightness Monitor described in PROJECT_BRIEF.md. Be direct, tell me the truth, and never use em dashes.

Your job:
- Keep a weekly plan against the versions in section 6 of the brief, at the hours I tell you I have.
- Track deadlines: applications, exams, and the Monday posts.
- Quiz me with the interview questions in METHODS.md section 9 until I can answer each in under a minute.
- When I paste output from Claude Code, check it against METHODS.md and DATA_SPEC.md and tell me what does not match.
- Look up current facts and cite sources with dates. Never invent a source. Label estimates.
- Check my intent before assuming.

I build the code in Claude Code. You plan, check, and prepare me to explain it.
```

## 12. Definition of done for version 1

- The page shows the score, the spread, and the charts for the latest week.
- The README states the question, the method, the limits, and shows the ontology diagram.
- The code is on GitHub with no API key in it.
- I can explain the score and the five-year comparison out loud in two minutes.

## 13. Resume bullet (fill in after it works)

```
Crude Market Tightness Monitor (Python, Claude Code), October 2026
Built a tool that pulls weekly EIA data on crude and distillate inventories and refinery utilization, compares each to its five-year seasonal range, and scores US market tightness alongside the Brent to WTI spread.
```

Add the backtest result as a second line once it exists.

## Sources

- EIA, Prices increased sharply in the first quarter of 2026 (Apr 7, 2026): https://www.eia.gov/todayinenergy/detail.php?id=67424
- EIA, Prices and refinery margins in the third quarter (Oct 5, 2026): https://www.eia.gov/todayinenergy/detail.php?id=68245
- IEA commentary on the Strait of Hormuz shock (June 22, 2026): https://www.iea.org/commentaries/how-global-oil-supplies-have-readjusted-to-help-fill-the-huge-gap-left-by-the-strait-of-hormuz-shock
- FRED, WTI: https://fred.stlouisfed.org/series/DCOILWTICO
- FRED, Brent: https://fred.stlouisfed.org/series/DCOILBRENTEU
- Further sources are listed in each file of the pack.
