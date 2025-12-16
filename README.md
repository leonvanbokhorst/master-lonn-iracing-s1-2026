# iRacing 2026 Season 1 – Ray FF1600 Rookie Fixed

This is the training-dojo journal for Lonn's Ray FF1600 Rookie Fixed campaign. It's the external memory for the season: weekly logs, soft-commitment rituals, and deep-dive lore on every track in the schedule. The goal isn't farming iRating; it's running the full season with intention: show up every week, stay out of avoidable chaos, grow racecraft (mirrors, defending, patience, exits), and let momentum driving slowly sink into muscle memory. Everything here exists to support that.

---

iRacing 2026 Season 1 runs **December 16, 2025 → March 9, 2026** (12 weeks). Build 2025.12.08.03 launched December 9, 2025.

- **Week:** Currently in prep for [the first week](weeks/week01/)
- **Car:** [Ray FF1600](cars/car-ray-ff1600.md)
- **Track:** [Summit Point Jefferson Circuit](tracks/track-summit-point-jefferson-circuit.md)
- **Official race schedule:** Tuesday 2025-12-16 → 2025-12-22
- **Status:** Practice complete – 10 events, 214 flying laps, ready for race week! 🏁

## Week 01 Summary

| Metric              | Start (Event #1) | Best Achieved    | Latest (Event #8) |
| ------------------- | ---------------- | ---------------- | ----------------- |
| **Best lap**        | 51.438s          | **50.985s** (#3) | 51.107s           |
| **Consistency (σ)** | 6.08s            | **0.81s** (#6)   | 1.03s             |
| **Coasting %**      | 12.2%            | **1.7%** (#4)    | 8.9%              |
| **Gap to optimal**  | 2.8s             | **0.13s** (#8)   | 0.13s             |

**Key learning:** Patience in traffic validated. σ 3.21s (impatient) → 0.81s (patient) in back-to-back races.

---

## Repository Shape

```
├── weeks/              ← Weekly logs + events + data + images
│   └── week01/
│       ├── README.md       Overview, progress viz, summary
│       ├── events/         Individual event pages
│       ├── data/           Garage61 CSVs + telemetry
│       └── images/         Visualizations
├── tracks/             ← Circuit dossiers
├── cars/               ← Car lore (Ray FF1600)
├── coaching/           ← AI coaching notes
│   └── lonn-profile.md     Driver profile, patterns, hypotheses
└── tools/              ← Automation scripts
```

- **`weeks/`** – One folder per week. Each event gets its own page with stats, telemetry, and freeform debrief.
- **`tracks/`** – Narrative dossiers: history, character, sector breakdowns, reference lap notes.
- **`cars/`** – Car-focused handling rituals. Currently: `car-ray-ff1600.md`.
- **`coaching/`** – AI coaching memory. Patterns observed, hypotheses to test, what works for this driver.
- **`tools/`** – Automation: add events, generate visualizations, compare laps.

---

## Track Lore Index

Need track context before a session? Start by skimming the track profile, then jump into that week's log.

| Week | Dates                   | Track & Layout                         | Track Profile                                                       | Week Log                        |
| ---- | ----------------------- | -------------------------------------- | ------------------------------------------------------------------- | ------------------------------- |
| 01   | 2025-12-16 → 2025-12-22 | Summit Point – Jefferson Circuit       | [dossier](tracks/track-summit-point-jefferson-circuit.md)           | [**week01/**](weeks/week01/) ✅ |
| 02   | 2025-12-23 → 2025-12-29 | Rudskogen Motorsenter                  | [dossier](tracks/track-rudskogen-motorsenter.md)                    | [week02/](weeks/week02/)        |
| 03   | 2025-12-30 → 2026-01-05 | Winton Motor Raceway – Grand Prix      | [dossier](tracks/track-winton-motor-raceway-natl-md.md)             | [week03/](weeks/week03/)        |
| 04   | 2026-01-06 → 2026-01-12 | Lime Rock Park – Grand Prix            | [dossier](tracks/track-lime-rock-park-grand-prix.md)                | [week04/](weeks/week04/)        |
| 05   | 2026-01-13 → 2026-01-19 | Motorsport Arena Oschersleben – GP     | [dossier](tracks/track-motorsport-arena-oschersleben-grand-prix.md) | [week05/](weeks/week05/)        |
| 06   | 2026-01-20 → 2026-01-26 | Oran Park Raceway – Grand Prix         | [dossier](tracks/track-oran-park-raceway-grand-prix.md)             | [week06/](weeks/week06/)        |
| 07   | 2026-01-27 → 2026-02-02 | Summit Point – Main Circuit            | [dossier](tracks/track-summit-point-main-circuit.md)                | [week07/](weeks/week07/)        |
| 08   | 2026-02-03 → 2026-02-09 | Virginia International Raceway – North | [dossier](tracks/track-virginia-international-raceway-north.md)     | [week08/](weeks/week08/)        |
| 09   | 2026-02-10 → 2026-02-16 | Circuit de Lédenon                     | [dossier](tracks/track-circuit-de-ledenon.md)                       | [week09/](weeks/week09/)        |
| 10   | 2026-02-17 → 2026-02-23 | Oulton Park – International            | [dossier](tracks/track-oulton-park-international.md)                | [week10/](weeks/week10/)        |
| 11   | 2026-02-24 → 2026-03-02 | Okayama International Circuit – Full   | [dossier](tracks/track-okayama-international-circuit-full.md)       | [week11/](weeks/week11/)        |
| 12   | 2026-03-03 → 2026-03-09 | Circuito de Navarra – Medium           | [dossier](tracks/track-circuito-de-navarra-medium.md)               | [week12/](weeks/week12/)        |

---

## Coaching

This repo includes an AI adaptive coaching method. Not a gimmick—a genuine reflection partner for Lonn to learn from his own data.

**How it works:**

- After events/weeks, ask an LLM to review the data and debrief
- It reads the event pages, telemetry, and coaching profile
- Returns: pattern observations, questions for reflection, hypotheses to test
- Coaching notes live in [`coaching/lonn-profile.md`](coaching/lonn-profile.md)

**What makes it real coaching:**

- Questions, not prescriptions
- Connects data to feeling
- Tracks patterns across weeks
- Remembers what works for _this_ driver
- Honest, even when uncomfortable

**Example prompts:**

- _"Review my latest event"_
- _"Coach me on week 01"_
- _"What should I focus on at Rudskogen?"_
- _"Compare my first and last event this week"_

---

## Workflow (for Future Lonn)

Light, repeatable, no drama:

```bash
# After a session, export CSV from Garage61, then:
make add-event WEEK=01 FILE=~/Downloads/export.csv TELEMETRY=~/Downloads/lap.csv

# Update week visualizations:
make update-week WEEK=01

# Compare best laps (needs telemetry exports):
make compare-laps WEEK=01

# Analyze single lap telemetry:
make viz-telemetry FILE=~/Downloads/lap.csv
```

- After each event, edit the debrief in `weeks/weekXX/events/`
- Add track insights to `tracks/` files—don't trust your brain
- At week end, update reflection in `weeks/weekXX/README.md`

The only hard rule: **keep showing up**.  
Everything else—pace, racecraft, confidence—gets to be a side effect of that habit.
