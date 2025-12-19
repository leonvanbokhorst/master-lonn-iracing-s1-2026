# Implementation Examples: Usage Scenarios

This document provides concrete, step-by-step examples of how to use each enhancement in the Master Lonn iRacing system.

---

## Scenario 1: Full Race Day Workflow (with new tools)

**Context:** It's Saturday, Week 04. Master Lonn is preparing for an official race at Lime Rock Park. He wants to use the full suite of new learning tools.

### Step 1: Pre-Race Preparation (30 minutes before race)

1.  **Spaced Repetition Review:** Check if any old tracks need review.

    ```bash
    make spaced-rep-check
    ```

    *Output shows Summit Point is due for review. He spends 5 minutes reading the `track-summit-point-jefferson-circuit.md` dossier and key learnings.* 

    ```bash
    make spaced-rep-review
    # Interactive prompt to rate mastery of Summit Point
    ```

2.  **Mental Rehearsal:** Prime the brain for the upcoming race.

    ```bash
    make rehearsal-pre WEEK=04 EVENT=08
    ```

    *He visualizes the first two laps, focusing on cold-tire handling and the tricky Turn 1 braking zone.* 

3.  **Scenario Planning:** Anticipate race dynamics.

    ```bash
    make scenario-planner-pre WEEK=04 EVENT=08
    ```

    *He inputs three likely scenarios: (1) Divebomb at T1, (2) Getting stuck behind a slower car, (3) Late-race battle for position.* 

### Step 2: The Race (30 minutes)

Master Lonn participates in the official race event.

### Step 3: Post-Race Debrief (20 minutes after race)

1.  **Add the Event:** Ingest the Garage61 data as usual.

    ```bash
    make add-event WEEK=04 FILE=~/Downloads/race-export.csv TELEMETRY=~/Downloads/best-lap.csv
    ```

2.  **Update Hypothesis:** The active hypothesis is "*Using a wider entry at Lime Rock's T1 improves exit speed*". He checks his telemetry and updates the hypothesis tracker.

    ```bash
    make hypothesis-update ID=3 WEEK=04 EVENT=08
    ```

    *The tool prompts for the metric (e.g., `T1_exit_speed`), the value (e.g., `145.2 kph`), and whether the hypothesis is validated.* 

3.  **Review Scenarios:** How did reality match the plan?

    ```bash
    make scenario-planner-post WEEK=04 EVENT=08
    ```

    *He marks that the "Divebomb at T1" scenario occurred and his planned response (giving space) was effective. He also notes a new pattern: "Cars that overdrive the chicane are vulnerable on the main straight."* 

4.  **Mental Replay:** Solidify the learnings from mistakes.

    ```bash
    make rehearsal-post WEEK=04 EVENT=08
    ```

    *He mentally rehearses the correct line through the chicane where he made a mistake on lap 5.* 

5.  **Edit Debrief:** Finally, he opens the generated event markdown file (`weeks/week04/events/08-date-race.md`) and fills in the qualitative "Feelings" and "Debrief" sections, now enriched by the structured data from the new tools.

---

## Scenario 2: Weekly Review Workflow

**Context:** It's Monday, the end of Week 04. Time to consolidate learnings.

### Step 1: Update Week Summary

```bash
make update-week WEEK=04
```
*This regenerates the `week-progress.png` and updates the stats table in the week's `README.md`.*

### Step 2: Review Season-Level Patterns

```bash
make season-dashboard
```
*This generates `coaching/season-dashboard.png`. He looks at the cross-week consistency trend and notices his σ is consistently lower in races than in practice.* 

### Step 3: Review Hypothesis Report

```bash
make hypothesis-report
```
*This generates `coaching/hypothesis-report.md`. He reviews the newly validated hypothesis about Lime Rock's T1 and sees that the "Coasting Transfer" hypothesis is still active and needs more data.* 

### Step 4: Generate a New Hypothesis for Next Week

Inspired by the season dashboard, he wants to test why he's better in races.

```bash
make hypothesis-add
```

**Interactive prompts:**
```
🔬 NEW HYPOTHESIS
==================================================
Title (short name): Race Day Focus
Hypothesis statement: My consistency improves under race pressure due to heightened focus.
Predicted outcome: In a practice session with a simulated race start and AI opponents, my consistency (σ) will be >20% better than in a solo practice session.
How will you test this? Compare σ from a 15-lap solo session vs. a 15-lap AI race session.
```

### Step 5: Get Adaptive Coaching Feedback

He asks Little Padawan for a summary of the week.

```bash
make adaptive-coach WEEK=04 EVENT=08
```

*The tool analyzes the week's trend (e.g., `plateauing`) and generates a custom LLM prompt. He uses this prompt to get a final, context-aware piece of advice from his AI coach.* 

---

## Scenario 3: Planning a Practice Session

**Context:** It's mid-week and Master Lonn has 45 minutes for a practice session. He wants to use interleaved practice to make it more effective.

### Step 1: Plan the Session

```bash
make plan-practice WEEK=04 EVENT=09
```

**Interactive prompts:**
```
📋 INTERLEAVED PRACTICE SESSION PLANNER
==================================================
Total laps planned: 25

Common focus areas:
  1. baseline - Establish rhythm
  2. sector_X - Focus on specific sector
  3. race_simulation - Race pace with traffic
  4. consistency - Minimize variance
  5. qualifying - Single-lap pace

Focus area 1 (empty to finish): consistency
  Description: Focus on hitting every apex and minimizing σ
Focus area 2 (empty to finish): sector_3
  Description: Work on the final corner exit to maximize straight speed
Focus area 3 (empty to finish): qualifying
  Description: One-lap pace on low fuel
Focus area 4 (empty to finish): 
```

### Step 2: Execute the Session

The tool prints a clear plan to the console, which he follows in iRacing:

```
📊 SESSION PLAN
==================================================

Block 1: Laps 1-8
  Focus: consistency
  Notes: Focus on hitting every apex and minimizing σ

Block 2: Laps 9-16
  Focus: sector_3
  Notes: Work on the final corner exit to maximize straight speed

Block 3: Laps 17-25
  Focus: qualifying
  Notes: One-lap pace on low fuel
```

### Step 3: Debrief

After the session, he runs `make add-event` as usual. The `practice_structure` is already saved in the event's frontmatter, providing valuable context for his debrief and for the AI coach's analysis.
