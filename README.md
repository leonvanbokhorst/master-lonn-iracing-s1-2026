# iRacing 2026 Season 1 – Ray FF1600 Rookie Fixed

> 🏎️ **Current Week: 01 – Summit Point Jefferson Circuit** (pre-season prep)  
> 📅 Official race week: 2025-12-16 → 2025-12-22  
> 🎯 Status: **Practice complete** – 4 events, 166 laps, ready for race week!

| Metric              | Start   | Current | Δ           |
| ------------------- | ------- | ------- | ----------- |
| **Best lap**        | 51.438s | 50.985s | **−0.453s** |
| **Consistency (σ)** | 5.22s   | 0.26s   | **−4.96s**  |
| **Coasting %**      | 12.2%   | 1.7%    | **−10.5%**  |
| **Gap to optimal**  | 2.8s    | 0.19s   | **−2.6s**   |

➡️ [**Week 01**](weeks/week01/) | [**Track Dossier**](tracks/track-summit-point-jefferson-circuit.md)

---

This repo is the training-dojo journal for Lonn's Ray FF1600 Rookie Fixed campaign.  
It's the external memory for the season: weekly logs, soft-commitment rituals, and deep-dive lore on every track in the schedule.

The goal isn't farming iRating; it's running the full season with intention:

- show up every week
- stay out of avoidable chaos
- grow racecraft (mirrors, defending, patience, exits)
- let momentum driving slowly sink into muscle memory

Everything here exists to support that.

---

## Repository Shape

- `weeks/`  
  One markdown log per official iRacing week.  
  Each follows the same arc: **intent → prep → races → reflection**.

- `tracks/`  
  Narrative dossiers for each circuit: a bit of history, driving character, Ray FF1600 notes, and references.

- `cars/`  
  Car-focused narratives and handling rituals.  
  Currently: `car-ray-ff1600.md`.

- `tools/`  
  Automation helpers (week generators, schedule YAML, future stats/exports).  
  The internals can evolve; the promise is: keep the logs simple to maintain.

---

## Track Lore Index

Need track context before a session? Start by skimming the track profile, then jump into that week's log.

| Week | Dates                   | Track & Layout                         | Track Profile                                                       | Week Log                        |
| ---- | ----------------------- | -------------------------------------- | ------------------------------------------------------------------- | ------------------------------- |
| 01   | 2025-12-16 → 2025-12-22 | Summit Point – Jefferson Circuit       | [dossier](tracks/track-summit-point-jefferson-circuit.md)           | [**week01/**](weeks/week01/) ✅ |
| 02   | 2025-12-23 → 2025-12-29 | Rudskogen Motorsenter                  | [dossier](tracks/track-rudskogen-motorsenter.md)                    | [week02/](weeks/week02/)        |
| 03   | 2025-12-30 → 2026-01-05 | Winton Motor Raceway – National        | [dossier](tracks/track-winton-motor-raceway-national.md)            | [week03/](weeks/week03/)        |
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

## Car Lore

- [`cars/car-ray-ff1600.md`](cars/car-ray-ff1600.md)  
  History, character, handling cues, and racecraft drills for the Ray FF1600 – the "momentum apprentice" at the centre of this whole thing.

---

## Workflow (for Future Lonn)

Light, repeatable, no drama:

```bash
# After a session, export CSV from Garage61, then:
make add-event WEEK=01 FILE=~/Downloads/export.csv

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
