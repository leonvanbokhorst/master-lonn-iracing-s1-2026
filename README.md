# iRacing 2026 Season 1 – Ray FF1600 Rookie Fixed

> 🏎️ **Current Week: 01 – Summit Point Jefferson Circuit** (pre-season prep)  
> 📅 Official race week: 2025-12-16 → 2025-12-22  
> 🎯 Status: **Practice phase** – building consistency before race week

| Metric         | Current   | Target  | Notes                        |
| -------------- | --------- | ------- | ---------------------------- |
| Best lap       | 51.29s    | sub-50s | 0.7s gained in one day       |
| Gap to VRS ref | ~2.0s     | <1.5s   | was 2.8s, improving steadily |
| Clean lap band | 51.7–52.5 | ±0.5s   | laps becoming "siblings"     |
| Practice laps  | 53        | –       | 2 sessions logged            |

➡️ [**Week 01 Log**](weeks/week01-summit-point-raceway.md) | [**Track Dossier**](tracks/track-summit-point-jefferson-circuit.md)

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

- `season-notes.md`  
  Season-long reflections and themes. Meta-level stuff: patterns, confidence shifts, "what this season is teaching me".

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

| Week | Dates (UTC)             | Track & Layout                               | Track Profile                                                                                                          | Weekly Log                                                                                         |
| ---- | ----------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 01   | 2025-12-16 → 2025-12-22 | Summit Point Raceway – Jefferson Circuit     | [`tracks/track-summit-point-jefferson-circuit.md`](tracks/track-summit-point-jefferson-circuit.md)                     | [`weeks/week01-summit-point-raceway.md`](weeks/week01-summit-point-raceway.md)                     |
| 02   | 2025-12-23 → 2025-12-29 | Rudskogen Motorsenter                        | [`tracks/track-rudskogen-motorsenter.md`](tracks/track-rudskogen-motorsenter.md)                                       | [`weeks/week02-rudskogen-motorsenter.md`](weeks/week02-rudskogen-motorsenter.md)                   |
| 03   | 2025-12-30 → 2026-01-05 | Winton Motor Raceway – National              | [`tracks/track-winton-motor-raceway-national.md`](tracks/track-winton-motor-raceway-national.md)                       | [`weeks/week03-winton-motor-raceway.md`](weeks/week03-winton-motor-raceway.md)                     |
| 04   | 2026-01-06 → 2026-01-12 | Lime Rock Park – Grand Prix                  | [`tracks/track-lime-rock-park-grand-prix.md`](tracks/track-lime-rock-park-grand-prix.md)                               | [`weeks/week04-lime-rock-park.md`](weeks/week04-lime-rock-park.md)                                 |
| 05   | 2026-01-13 → 2026-01-19 | Motorsport Arena Oschersleben – Grand Prix   | [`tracks/track-motorsport-arena-oschersleben-grand-prix.md`](tracks/track-motorsport-arena-oschersleben-grand-prix.md) | [`weeks/week05-motorsport-arena-oschersleben.md`](weeks/week05-motorsport-arena-oschersleben.md)   |
| 06   | 2026-01-20 → 2026-01-26 | Oran Park Raceway – Grand Prix               | [`tracks/track-oran-park-raceway-grand-prix.md`](tracks/track-oran-park-raceway-grand-prix.md)                         | [`weeks/week06-oran-park-raceway.md`](weeks/week06-oran-park-raceway.md)                           |
| 07   | 2026-01-27 → 2026-02-02 | Summit Point Raceway – Main Circuit          | [`tracks/track-summit-point-main-circuit.md`](tracks/track-summit-point-main-circuit.md)                               | [`weeks/week07-summit-point-raceway.md`](weeks/week07-summit-point-raceway.md)                     |
| 08   | 2026-02-03 → 2026-02-09 | Virginia International Raceway – North       | [`tracks/track-virginia-international-raceway-north.md`](tracks/track-virginia-international-raceway-north.md)         | [`weeks/week08-virginia-international-raceway.md`](weeks/week08-virginia-international-raceway.md) |
| 09   | 2026-02-10 → 2026-02-16 | Circuit de Lédenon – Full Circuit            | [`tracks/track-circuit-de-ledenon.md`](tracks/track-circuit-de-ledenon.md)                                             | [`weeks/week09-circuit-de-ledenon.md`](weeks/week09-circuit-de-ledenon.md)                         |
| 10   | 2026-02-17 → 2026-02-23 | Oulton Park Circuit – International          | [`tracks/track-oulton-park-international.md`](tracks/track-oulton-park-international.md)                               | [`weeks/week10-oulton-park-circuit.md`](weeks/week10-oulton-park-circuit.md)                       |
| 11   | 2026-02-24 → 2026-03-02 | Okayama International Circuit – Full         | [`tracks/track-okayama-international-circuit-full.md`](tracks/track-okayama-international-circuit-full.md)             | [`weeks/week11-okayama-international-circuit.md`](weeks/week11-okayama-international-circuit.md)   |
| 12   | 2026-03-03 → 2026-03-09 | Circuito de Navarra – Speed Circuit (Medium) | [`tracks/track-circuito-de-navarra-medium.md`](tracks/track-circuito-de-navarra-medium.md)                             | [`weeks/week12-circuito-de-navarra.md`](weeks/week12-circuito-de-navarra.md)                       |

---

## Car Lore

- [`cars/car-ray-ff1600.md`](cars/car-ray-ff1600.md)  
  History, character, handling cues, and racecraft drills for the Ray FF1600 – the "momentum apprentice" at the centre of this whole thing.

---

## Workflow Reminders (for Future Lonn)

Light, repeatable, no drama:

- Use `uv run tools/create_week.py --week <n>` to scaffold a new week file from the template.
- After each session (practice / race), log at least one line in that week's file while the memory is fresh.
- Add any new track insights, brake-bias experiments or racecraft notes straight into the matching `tracks/` file—don't trust your brain to "remember it later".
- At the end of each week, write a short reflection in `weeks/weekXX-*.md` **and** optionally one meta-note in `season-notes.md`.

The only hard rule: keep showing up.  
Everything else—pace, racecraft, confidence—gets to be a side effect of that habit.
