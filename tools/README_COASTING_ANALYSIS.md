# Coasting Analysis System

## Overview

The Coasting Analysis System transforms coasting from a passive metric into an **actionable learning tool**. Instead of just reporting "Coasting: 7.5%", it tells you **WHERE** it happens, **WHY** it happens, **HOW MUCH** time it costs, and **WHAT TO DO** about it.

## The Problem

Traditional coasting metrics provide a single number without context:

```
Coasting: 7.5%
```

This doesn't answer the critical questions:
- Which corners have the most coasting?
- Is it entry hesitation, mid-corner searching, or late throttle application?
- How much lap time is this costing?
- Which zones should I prioritize fixing?

## The Solution

The Coasting Analysis System provides:

1. **Corner-by-Corner Breakdown**: See exactly which corners have coasting
2. **Time Cost Analysis**: Understand the lap time impact of each zone
3. **Root Cause Classification**: Entry hesitation vs. mid-corner searching vs. exit issues
4. **Priority Recommendations**: Specific, actionable advice for the top 3 problem zones
5. **Visual Hotspot Map**: Track map with coasting zones sized by impact

## Tools

### 1. `analyze_coasting.py` - Deep Analysis

Provides comprehensive text-based analysis with detailed metrics.

**Usage:**
```bash
python tools/analyze_coasting.py <telemetry_file>

# Or via Makefile:
make analyze-coasting FILE=weeks/week01/data/processed/telemetry.csv
```

**Output Example:**
```
======================================================================
COASTING IMPACT ANALYSIS
======================================================================

📊 Overall Summary:
   Coasting: 7.5% of lap
   Estimated time cost: 0.152s
   Potential lap time: 50.838s (−0.152s)
   Number of coasting zones: 5

🎯 Corner-by-Corner Breakdown:
   Corner     Coasting %   Time Cost    Primary Issue
   ---------- ------------ ------------ ------------------------------
   T3           12.5%       0.087s      Exit Late Throttle
   T6            8.3%       0.042s      Mid Searching
   T1            3.2%       0.023s      Entry Hesitation
   T4            0.0%       0.000s      ✅ Clean
   T2            0.0%       0.000s      ✅ Clean

🔥 Top Priority Zones (highest impact):

   1. T3 exit
      Time cost: 0.087s
      💡 Apply throttle earlier at T3 exit - smooth and progressive

   2. T6 mid
      Time cost: 0.042s
      💡 Trust the line through T6 - you're searching mid-corner

   3. T1 entry
      Time cost: 0.023s
      💡 Commit to turn-in earlier - you're hesitating before T1

📈 Making progress. Focus on eliminating the top 3 priority zones.
```

### 2. `visualize_coasting_impact.py` - Visual Dashboard

Creates a comprehensive 6-panel visualization showing coasting impact.

**Usage:**
```bash
python tools/visualize_coasting_impact.py <telemetry_file> [output_file]

# Or via Makefile:
make viz-coasting-impact FILE=weeks/week01/data/processed/telemetry.csv
```

**Visualization Panels:**

1. **Hotspot Map** (top left, large)
   - Track map with coasting zones overlaid
   - Color-coded by severity:
     - Red = Severe (>0.05s cost)
     - Orange = Moderate (>0.02s cost)
     - Gray = Minor (<0.02s cost)
   - Line thickness proportional to time cost

2. **Corner Breakdown Chart** (top right)
   - Bar chart showing coasting % per corner
   - Sorted by severity (worst first)
   - Color-coded for quick identification

3. **Time Cost Analysis** (middle right)
   - Bar chart showing time cost per corner
   - Helps prioritize which corners to fix first
   - Total time cost displayed in title

4. **Coasting Phase Distribution** (bottom left)
   - Pie chart showing entry vs. mid vs. exit coasting
   - Helps identify systematic issues
   - Example: If 80% is exit coasting → late throttle application

5. **Severity Breakdown** (bottom middle)
   - Bar chart showing number of zones by severity
   - Quick health check: How many severe zones?

6. **Priority Recommendations** (bottom right)
   - Top 3 problem zones with specific recommendations
   - Time cost for each zone
   - Actionable advice based on phase analysis

## How It Works

### Corner Detection

The system automatically detects corners using lateral G-force and speed changes:

- Lateral G > 0.3g = in corner
- Groups consecutive samples into corners
- Assigns corner numbers (T1, T2, T3, etc.)

**Note:** In future versions, corner definitions can be loaded from track-specific config files for more accurate analysis.

### Coasting Detection

Coasting is defined as:
```
(Throttle < 10%) AND (Brake < 2%) AND (|LongAccel| < 0.5 m/s²)
```

This ensures we only flag true "dead time" between brake and throttle, not trail braking or maintenance throttle.

### Phase Classification

Each coasting zone is classified by where it occurs in the corner:

- **Entry** (first 30% of corner): Hesitation before turn-in
- **Mid** (middle 40% of corner): Searching for apex or line
- **Exit** (last 30% of corner): Late throttle application
- **Transition** (between corners): Gap between brake release and throttle

### Time Cost Estimation

Time cost is estimated using a simplified model:

```
time_cost ≈ duration × speed_loss × 0.01
```

Where:
- `duration` = length of coasting zone in seconds
- `speed_loss` = average speed loss during coasting (m/s)

This is a rough estimate; actual impact depends on track, corner, car, etc. But it's useful for **relative comparison** between zones.

### Severity Classification

Zones are classified by time cost:

- **Severe**: >0.05s (red) - High priority, significant impact
- **Moderate**: 0.02-0.05s (orange) - Medium priority
- **Minor**: <0.02s (gray) - Low priority, may be acceptable

## Workflow Integration

### Daily Practice

After each session with telemetry:

```bash
# Quick analysis
make analyze-coasting FILE=weeks/week01/data/processed/best_lap.csv

# Visual dashboard
make viz-coasting-impact FILE=weeks/week01/data/processed/best_lap.csv
```

### Weekly Review

Compare coasting across events:

```bash
# Analyze first and last event
make analyze-coasting FILE=weeks/week01/events/01-date-practice/telemetry.csv
make analyze-coasting FILE=weeks/week01/events/13-date-race/telemetry.csv

# Create visualizations for both
make viz-coasting-impact FILE=weeks/week01/events/01-date-practice/telemetry.csv
make viz-coasting-impact FILE=weeks/week01/events/13-date-race/telemetry.csv
```

### Integration with Learning Tools

#### Mental Rehearsal

Use coasting analysis to inform pre-session visualization:

```bash
# Identify problem zones
make analyze-coasting FILE=last_session.csv

# Before next session
make rehearsal-pre EVENT=next_event.md
# Focus: "Visualize smooth throttle application at T3 exit"
```

#### Hypothesis Testing

Create hypotheses based on coasting analysis:

```bash
# Analyze coasting
make analyze-coasting FILE=current_best.csv
# Output: "T3 exit: 0.087s lost to late throttle"

# Create hypothesis
make hypothesis-create
# Hypothesis: "Applying throttle 0.5s earlier at T3 exit will reduce coasting by 50%"
# Expected: "Coasting in T3 drops from 12.5% to <6%"
```

#### Spaced Repetition

Add key learnings to SRS:

```bash
# After eliminating coasting in T3
make srs-add
# Q: "What's the optimal throttle point at T3 exit?"
# A: "At apex, not after. Smooth progressive application. Eliminated 0.087s of coasting."
```

## Interpreting Results

### Coasting Percentage Targets

For a momentum car like the Ray FF1600:

- **<2%**: Outstanding - transitions are clean
- **2-5%**: Good - minor refinement needed
- **5-10%**: Opportunity - focus on priority zones
- **>10%**: Significant unlock available - coasting elimination is your biggest gain

### Common Patterns

**Entry Coasting (Hesitation)**
- **Symptom**: Coasting in first 30% of corner
- **Root Cause**: Lack of commitment to turn-in
- **Fix**: Trust the line, commit earlier
- **Mental Cue**: "Turn-in is a decision, not a negotiation"

**Mid-Corner Coasting (Searching)**
- **Symptom**: Coasting in middle 40% of corner
- **Root Cause**: Uncertain about line or apex
- **Fix**: Lock in the line through practice, use reference points
- **Mental Cue**: "The line is set, just execute"

**Exit Coasting (Late Throttle)**
- **Symptom**: Coasting in last 30% of corner
- **Root Cause**: Waiting too long to apply throttle
- **Fix**: Progressive throttle at apex, not after
- **Mental Cue**: "Throttle is part of the corner, not what comes after"

**Transition Coasting (Gap)**
- **Symptom**: Coasting between corners
- **Root Cause**: Dead time between brake release and throttle
- **Fix**: Minimize the gap - brake → maintenance throttle → full throttle
- **Mental Cue**: "Fill the dead space"

## Real-World Example: Week 01

From the coaching notes:

> **Pattern Discovered:** Coasting elimination was the big unlock. Not braking later, not more corner speed – just filling the dead time between brake and throttle.

**The Numbers:**
| Metric | Event #1 | Event #13 | Improvement |
|--------|----------|-----------|-------------|
| Coasting | 12.2% | 1.7% | −10.5% |
| Best Lap | 51.438s | 50.985s | −0.453s |
| Consistency (σ) | 5.22s | 0.26s | −4.96s |

**The Insight:**

If you had run the coasting analysis on Event #1, it would have shown:
- "Estimated time cost: ~0.6s"
- "Top priority: T1-T3 transitions"
- "Primary issue: Late throttle application"

By Event #13, coasting was nearly eliminated (1.7%), and lap time improved by 0.453s. The coasting analysis would have **predicted this gain** and **guided the focus** to the right areas.

## Advanced Usage

### Custom Corner Definitions

For more accurate analysis, you can define corners manually in a track-specific config:

```toml
# config.toml
[tracks.summit_point_jefferson]
corners = [
    { name = "T1", start = 0.02, end = 0.12 },
    { name = "T2", start = 0.18, end = 0.28 },
    { name = "T3", start = 0.35, end = 0.48 },
    # ... etc
]
```

(This feature is not yet implemented but is planned for future versions.)

### Batch Analysis

Analyze all events in a week:

```bash
for file in weeks/week01/data/processed/*.csv; do
    echo "Analyzing $file"
    make analyze-coasting FILE="$file" >> week01_coasting_report.txt
done
```

### Trend Analysis

Track coasting improvement over time:

```bash
# Create a simple trend report
echo "Event,Coasting%,TimeCost" > coasting_trend.csv
for file in weeks/week01/events/*/telemetry.csv; do
    event=$(basename $(dirname $file))
    # Run analysis and parse output
    make analyze-coasting FILE="$file" | grep "Coasting:" | \
        awk -v e=$event '{print e "," $2 "," $5}' >> coasting_trend.csv
done
```

## Troubleshooting

### "No corners detected"

**Cause:** Lateral G data missing or below threshold

**Solution:**
- Check that `LatAccel` column exists in telemetry
- Try lowering corner detection threshold (edit `detect_corners()` function)
- Manually define corners in config (future feature)

### "All corners show 0% coasting"

**Cause:** This is actually good! It means you're filling the transitions well.

**Validation:**
- Check the raw telemetry to confirm
- Compare to earlier laps - did you eliminate coasting over time?
- If this is your first lap, you might be driving very smoothly already

### "Time cost estimates seem off"

**Cause:** The time cost model is simplified and approximate.

**Solution:**
- Use time cost for **relative comparison** (which zones are worse?)
- Don't treat absolute numbers as precise predictions
- Focus on the **ranking** of zones, not exact seconds

## Scientific Background

Coasting elimination is a key principle in momentum car driving:

**Momentum Driving:**
- Maintain speed through corners by minimizing speed loss
- Smooth, progressive inputs
- Minimize "dead time" between brake and throttle

**The Physics:**
- Coasting = no longitudinal force
- Car is neither accelerating nor decelerating
- In a momentum car, this is wasted time
- Goal: Brake → (brief maintenance throttle) → Progressive acceleration

**The Psychology:**
- Coasting often indicates **hesitation** or **uncertainty**
- Entry coasting = lack of commitment
- Mid-corner coasting = searching for line
- Exit coasting = lack of confidence in traction

**The Data:**
- Week 01 showed 10.5% coasting reduction = 0.453s lap time improvement
- This validates the "coasting elimination = lap time gain" hypothesis
- The coasting analysis system makes this insight **visible** and **actionable**

## Future Enhancements

Planned features:

1. **Track-Specific Corner Definitions**: Load corner boundaries from config
2. **Comparison Mode**: Compare two laps side-by-side
3. **Trend Visualization**: Show coasting improvement over time
4. **Reference Lap Overlay**: Compare to optimal/reference lap
5. **Automated Recommendations**: AI-generated coaching based on patterns
6. **Integration with VRS**: Compare coasting to fast drivers

## Summary

The Coasting Analysis System transforms a simple percentage into a powerful learning tool:

**Before:**
```
Coasting: 7.5%
```

**After:**
```
Coasting: 7.5% (0.152s cost)
Top Priority:
  1. T3 exit (0.087s) - Apply throttle earlier
  2. T6 mid (0.042s) - Trust the line
  3. T1 entry (0.023s) - Commit earlier

Action: Focus on T3 exit in next session
Hypothesis: Earlier throttle will save 0.08s
```

This is the difference between **data** and **insight**.

---

**Key Principle:**

> "Coasting elimination was the big unlock. Not braking later, not more corner speed – just filling the dead time between brake and throttle."  
> — Coaching Notes, Week 01

The Coasting Analysis System makes this insight **visible**, **measurable**, and **actionable** for every session.
