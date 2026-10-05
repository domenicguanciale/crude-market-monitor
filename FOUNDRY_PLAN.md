# Foundry rebuild plan (version 3)

Checked October 5, 2026. This is for after the Python version works. Items marked UNVERIFIED need checking inside the platform or with your Palantir contact.

## 1. Developer Tier

- It is free. A Palantir staff member states: "Developer Tier is a free tier of Foundry / AIP and you won't be charged."
- It has fixed limits on compute and storage. If you reach them, you stop. You are not billed.
- Your limits are shown in Control Panel, on the "Your Plan" page.
- Sign up at https://signup.palantirfoundry.com
- UNVERIFIED: how long approval takes, the exact limits, and which AI models are included.

Your data is small (a few thousand weekly rows and about 25 events), so the limits should not be a problem. That is my estimate, not a verified fact.

## 2. Build path

Each step names the Foundry application and what you do in it. All five applications below are described by Palantir as no-code.

| Step | Application | What you do | Documentation |
|---|---|---|---|
| 1 | Data upload | Export your tables from the Python project as CSV files and upload each as a dataset: weekly readings, price series, facilities, disruption events, sources | UNVERIFIED which screen. Ask the Speedrun course |
| 2 | Pipeline Builder | Clean types and dates, join weekly readings to the five-year range, and compute the tightness score. It is "Foundry's primary application for data integration" with drag-and-drop transforms | https://www.palantir.com/docs/foundry/pipeline-builder/overview |
| 3 | Ontology Manager | Define the object types (Facility, Disruption Event, Weekly Reading, Price Series, Source), their properties, and the link types between them | https://www.palantir.com/docs/foundry/ontology-manager/overview |
| 4 | Action types | Define "Flag hedge review." An action type is a set of changes a user can make to objects in one step, and it can send a notification | https://www.palantir.com/docs/foundry/action-types/overview |
| 5 | Workshop | Build the app the fuel buyer sees: the current score, the charts, the event table, and a button that runs the action | https://www.palantir.com/docs/foundry/workshop/overview |
| 6 | AIP Logic | Add one AI function that does real work. Best fit: paste in a news article and have it extract the event date, facility, and barrels offline into a new Disruption Event for human review | https://www.palantir.com/docs/foundry/logic/overview |

Step 6 matters most for the demo. Palantir describes AIP Logic as handling "extracting information from unstructured inputs into the Ontology" with edits that can be "staged" for human review. That is the same event-extraction task you are hand-checking in the Python version, so you can report the accuracy.

UNVERIFIED: whether Workshop in Developer Tier includes a map widget, and whether the tightness score is better computed in Pipeline Builder or as a derived property.

## 3. Courses for each step

| Course | Length | Covers | Needs Developer Tier |
|---|---|---|---|
| Speedrun: Your First End-to-End Workflow | 60 to 90 minutes | Steps 1 to 5 in miniature | Yes |
| Speedrun: Your First AIP Workflow | 60 to 90 minutes | Step 6 | Likely. UNVERIFIED |
| Foundry & AIP Aware learning path | 8 hours | The full set, hands-on | Likely. UNVERIFIED |

All are free at https://learn.palantir.com. Take the first Speedrun as soon as your access arrives, then build your own project the same way.

## 4. Five-minute video outline

Palantir's Build to Apply postings ask for an unlisted YouTube video under five minutes "demonstrating the components of your workflow." They say they assess why you chose the problem, your approach, and the solution.

| Time | Show |
|---|---|
| 0:00 to 0:30 | The problem and the user: a fuel buyer deciding when to lock in a contract, in a year when Brent went from $61 to $118 |
| 0:30 to 1:15 | The ontology: five object types and how they link. Open one Disruption Event and click through to its Facility and Source |
| 1:15 to 2:00 | The pipeline: raw weekly data in, the five-year comparison, the tightness score out |
| 2:00 to 3:00 | The app: today's score, the Brent minus WTI spread, the event table, one past event's price reaction |
| 3:00 to 4:00 | The AI step: paste a news article, show the extracted event staged for review, approve it, and state your measured accuracy |
| 4:00 to 4:40 | The action: "Flag hedge review" fires and the buyer gets the alert |
| 4:40 to 5:00 | What the backtest showed, the limits, and what you would build next |

Record it as a screen capture with your voice. No slides.

## 5. Postings

**Build to Apply.** Six postings were open on Palantir's job board today. All six carry the same title.

| Title | Team | Type | Locations |
|---|---|---|---|
| Deployment Strategist, Build to Apply - US Government | Echo | Full-time | Washington DC; New York; Fayetteville NC; Honolulu; San Diego; Colorado Springs |

Terms as stated in the New York posting:

- Build a project in Foundry and AIP on a problem of your choice, using public or notional data.
- Submit an unlisted YouTube video under five minutes.
- "Submit your application within 7-10 days of when you begin building."
- On-site, with travel of 25 to 75 percent.
- "Active US Security clearance or eligibility and willingness to obtain a US Security clearance."

No commercial Build to Apply posting appeared on the board today. These are full-time roles. UNVERIFIED: whether Palantir accepts a Build to Apply submission with an internship application. Ask your contact.

**Internship.** The Deployment Strategist internship for summer 2027 was listed in Honolulu at $6,700 a month when checked on October 4, with applications open since July 1, 2026. The job board also lists many other internships. Recheck the board before applying.

The useful point: you can build in this format and send the video to your contact whichever posting you apply to.

## 6. Exams

| Level | Exams | Format | Cost and access |
|---|---|---|---|
| Aware | Foundry Aware | UNVERIFIED. Read the rules screen before starting | At certification.palantir.com |
| Associate | Application Developer, AI Engineer, Data Engineer | Timed, open-book, multiple choice. Valid two years | A voucher code is required. Get one from your Palantir contact or by filing a Foundry issue from a Developer Tier account. Palantir does not publish the price |
| Specialist | Same three domains | Three hours, live, proctored over Zoom: plan (20 minutes), build (120 minutes), modify (40 minutes) | $350 per attempt. Requires the matching Associate exam first. Delivered through ontologize.com |

A third-party guide adds two details it attributes to Palantir's official exam guide: the Data Engineer exam has 60 questions in 120 minutes with a 70 percent pass mark, and there is a 14-day wait after a failed attempt. Treat both as unconfirmed until you see them on Palantir's own pages.

Order for you: Foundry Aware now, Application Developer (Associate) after you finish the Foundry rebuild, since building the project is the best preparation for it.

## 7. Example demos

Not researched. Palantir's public social posts show candidates fast-tracked through Build to Apply after building "a compelling AIP demo," but no specific examples were reviewed. Ask your contact for one or two submissions that impressed their team.

## 8. What was not verified

- Developer Tier approval time, exact limits, and model access.
- The upload screen in step 1, and map support in Workshop.
- The Foundry Aware exam format, cost, and retake rules.
- Associate exam prices and question counts on Palantir's own pages.
- Whether interns can use Build to Apply.
- Example demos.

## 9. Sources

- Palantir Developer Community, Developer Tier billing and usage: https://community.palantir.com/t/developer-tier-billing-and-usage/1074
- Palantir docs, Pipeline Builder: https://www.palantir.com/docs/foundry/pipeline-builder/overview
- Palantir docs, Ontology Manager: https://www.palantir.com/docs/foundry/ontology-manager/overview
- Palantir docs, Action types: https://www.palantir.com/docs/foundry/action-types/overview
- Palantir docs, Workshop: https://www.palantir.com/docs/foundry/workshop/overview
- Palantir docs, AIP Logic: https://www.palantir.com/docs/foundry/logic/overview
- Palantir Learning: https://learn.palantir.com/
- Palantir Learning FAQ: https://learn.palantir.com/page/faqs
- Palantir job board (accessed Oct 5, 2026): https://jobs.lever.co/palantir
- Palantir, Deployment Strategist, Build to Apply, New York (accessed Oct 5, 2026): https://jobs.lever.co/palantir/ec006383-f48c-452c-a124-88657b5e3277
- Palantir, Deployment Strategist, Internship (accessed Oct 4, 2026): https://jobs.lever.co/palantir/a6ba9190-115c-47e8-9915-90e68307c18f
- Palantir Developer Community, certifications refresh (July 27, 2026): https://community.palantir.com/t/palantir-certifications-are-getting-a-refresh-with-a-brand-new-ai-engineer-exam-launching-3-august/7022
- Palantir Developer Community, Specialist exams (Sept 22, 2026): https://community.palantir.com/t/palantir-specialist-certification-exams-launch-on-30-september/7256
- Third-party guide to Palantir certifications: https://certiguard.io/guides/palantir-certifications-cost-and-registration/
