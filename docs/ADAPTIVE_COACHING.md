# Adaptive Coaching System Documentation

## Overview

The **Adaptive Coaching System** transforms the iRacing repository from a static analysis tool into an intelligent, Cursor-driven coaching workflow that:

1. **Analyzes** event data to understand performance patterns
2. **Selects** only relevant visualization tools based on learning needs
3. **Generates** focused, actionable coaching with specific next steps

## Philosophy

> **"Analyze to understand, visualize to teach"**

Instead of generating all visualizations for every event, the system intelligently picks 2-3 tools that address the specific learning opportunities in each event.

---

## Architecture

### Components

1. **Analysis Utilities** - Extract insights from event data
   - `analyze_event.py` - Returns JSON with comprehensive event metrics
   - `analyze_week.py` - Returns JSON with week-level context

2. **Modular Visualization Tools** - Independently callable, focused charts
   - `viz_lap_progression.py` - Baseline lap time chart (always useful)
   - `viz_sector_loss.py` - Sector-by-sector time loss analysis
   - `viz_pace_trend.py` - Smoothed pace analysis with consistency corridor

3. **Cursor Integration** - AI-driven decision making
   - `.cursorrules` - Workflow instructions and decision logic for Cursor
   - Cursor analyzes data, selects tools, generates coaching

---

## Workflow

### Old Way (Week 01 - Static)

```bash
make add-event WEEK=01 FILE=export.csv TELEMETRY=lap.csv
```

**Result**: Runs ALL tools automatically → 4+ visualizations always generated

**Problems**:
- Information overload
- Can't identify what matters
- Wasted processing time
- No intelligent analysis

### New Way (Week 02+ - Adaptive)

```bash
# User tells Cursor: "Analyze my Week 02 Event 1"
```

**Cursor's Process**:

1. **Analyze data**:
   ```bash
   uv run python tools/analyze_event.py "event.csv" --json
   ```

2. **Identify patterns**:
   - σ = 1.11 (moderate variance)
   - Sector 2 has 16.25s loss (3x more than others!)
   - Pace trend: improving
   - Event type: solo practice

3. **Select tools** (only 2-3 relevant ones):
   ```bash
   uv run python tools/viz_lap_progression.py ...
   uv run python tools/viz_sector_loss.py ...
   uv run python tools/viz_pace_trend.py ...
   ```

4. **Generate coaching**:
   - Focus: Sector 2 consistency
   - Goal: Get S2 average under 36.0s
   - Next session: 10 laps focused on S2 only

**Result**: 3 relevant visualizations + focused coaching

---

## Analysis Utilities

### analyze_event.py

Returns comprehensive JSON analysis of a single event.

**Usage**:
```bash
uv run python tools/analyze_event.py "path/to/event.csv" --json
```

**Output**:
```json
{
  "event_type": "solo",
  "laps": {
    "total": 18,
    "clean": 17,
    "clean_percentage": 94.4
  },
  "best_lap": {
    "lap_number": 18,
    "time": 90.290
  },
  "consistency": {
    "sigma": 1.11,
    "variance_level": "moderate",
    "mean": 91.79,
    "median": 91.73
  },
  "sectors": {
    "Sector 1": {
      "best": 26.23,
      "average": 26.56,
      "total_loss": 5.88,
      "consistency_sigma": 0.23
    },
    "Sector 2": {
      "best": 30.85,
      "average": 31.75,
      "total_loss": 16.25,
      "consistency_sigma": 0.63
    }
  },
  "pace_trend": {
    "trend": "improving",
    "early_avg": 93.04,
    "late_avg": 90.74,
    "improvement": 2.30
  },
  "theoretical_optimal": {
    "time": 89.99,
    "delta_to_best": -0.30
  }
}
```

**Key Metrics**:
- `consistency.sigma` - Standard deviation of lap times
- `consistency.variance_level` - Classified as excellent/good/moderate/high
- `sectors[].total_loss` - Total time lost in sector vs best
- `pace_trend.trend` - improving/stable/declining
- `theoretical_optimal` - Best possible lap from best sectors

### analyze_week.py

Returns week-level context for understanding progression.

**Usage**:
```bash
uv run python tools/analyze_week.py "weeks/week02" --json
```

**Output**:
```json
{
  "week": "02",
  "track": "Rudskogen Motorsenter",
  "events": 1,
  "total_laps": 18,
  "best_lap": 90.29,
  "improvement": 0.0,
  "avg_consistency": 1.11,
  "event_details": [...]
}
```

---

## Visualization Tools

All visualization tools follow the same interface:

```bash
python tools/viz_[TOOL].py "input.csv" "output.png" --title "Title"
```

### viz_lap_progression.py

**Purpose**: Baseline lap time chart - shows overall pace and fastest lap

**When to use**: ALWAYS (baseline visualization)

**Example**:
```bash
uv run python tools/viz_lap_progression.py \
  "weeks/week02/data/processed/event.csv" \
  "weeks/week02/images/event-01-laptimes.png" \
  --title "Event #1"
```

**Shows**:
- Individual lap times as connected points
- Fastest lap highlighted with star
- Dirty/off-track laps marked with X
- Mean lap time as dashed line

### viz_sector_loss.py

**Purpose**: Shows time lost in each sector compared to best sector time

**When to use**:
- One sector has 2-3x more loss than others (clear problem area)
- Moderate to high variance (σ > 1.0)
- Driver needs to know WHERE to focus

**Example**:
```bash
uv run python tools/viz_sector_loss.py \
  "weeks/week02/data/processed/event.csv" \
  "weeks/week02/images/event-01-sectors.png" \
  --title "Event #1 Sector Loss"
```

**Shows**:
- Smoothed line for each sector showing loss per lap
- Total loss displayed in legend
- Scatter points show individual lap variance

### viz_pace_trend.py

**Purpose**: Smoothed pace analysis with 5-lap consistency corridor

**When to use**:
- High variance (σ > 1.5) - shows consistency issues
- Improving/declining trends - shows learning curve
- Need to understand pace evolution over session

**Example**:
```bash
uv run python tools/viz_pace_trend.py \
  "weeks/week02/data/processed/event.csv" \
  "weeks/week02/images/event-01-pace.png" \
  --title "Event #1 Pace Trend"
```

**Shows**:
- Individual laps as scatter points
- 5-lap pace range as shaded corridor
- Smoothed trend line through middle
- Settled pace line (last third average)

---

## Decision Logic

### Tool Selection Based on Patterns

#### Pattern: High Variance (σ > 1.5)

**Interpretation**: Unstable technique, inconsistent execution

**Tools**:
- `viz_lap_progression` (baseline)
- `viz_sector_loss` (find problem area)
- `viz_pace_trend` (show consistency issues)

**Coaching Focus**:
- Identify which sector has most variance
- Set consistency goal (reduce σ)
- Focus on repeatable technique

#### Pattern: Sector-Specific Issue

**Interpretation**: One sector has 2-3x more loss than others

**Tools**:
- `viz_lap_progression` (baseline)
- `viz_sector_loss` (highlight problem sector)

**Coaching Focus**:
- Name the problem sector
- Reference specific data (e.g., "16.25s total loss")
- Set sector-specific goal (e.g., "S2 average under 36.0s")

#### Pattern: Good Consistency (σ < 0.8)

**Interpretation**: Technique is stable, ready for next challenge

**Tools**:
- `viz_lap_progression` (baseline only)

**Coaching Focus**:
- Celebrate consistency achievement
- Identify next performance step
- Consider setup changes or line optimization

#### Pattern: Improving Trend

**Interpretation**: Driver is learning, building confidence

**Tools**:
- `viz_lap_progression` (baseline)
- `viz_sector_loss` (show where to focus next)

**Coaching Focus**:
- Acknowledge improvement (with data)
- Identify remaining opportunities
- Set next milestone

---

## Coaching Guidelines

### Be Specific

❌ **Bad**: "Sector 2 was slow"
✅ **Good**: "Sector 2 cost you 16.25s total - that's 3x more than any other sector"

### Be Actionable

❌ **Bad**: "Try to be smoother"
✅ **Good**: "Find one consistent brake marker before the blind crest"

### Be Concise

❌ **Bad**: 5+ focus areas
✅ **Good**: 2-3 specific focus areas

### Set Measurable Goals

❌ **Bad**: "Practice more"
✅ **Good**: "Next session: 10 laps focused on S2, goal average under 36.0s"

### Reference Data

❌ **Bad**: "Your consistency improved"
✅ **Good**: "σ dropped from 2.3s (early) to 0.8s (late) - 3x improvement"

---

## Example: Complete Event Analysis

### Input Data

Event: Week 02, Event 1 (solo practice)
- 18 laps
- Best: 90.29s
- σ: 1.11s
- Sector 2: 16.25s total loss

### Cursor's Analysis

```json
{
  "consistency": {"sigma": 1.11, "variance_level": "moderate"},
  "sectors": {
    "Sector 1": {"total_loss": 5.88},
    "Sector 2": {"total_loss": 16.25},  // ← 3x more!
    "Sector 3": {"total_loss": 5.20},
    "Sector 4": {"total_loss": 4.93}
  },
  "pace_trend": {"trend": "improving"}
}
```

### Tool Selection

**Decision**: Moderate σ + clear sector issue + improving trend

**Tools to run**:
1. `viz_lap_progression.py` (baseline)
2. `viz_sector_loss.py` (highlight S2 problem)
3. `viz_pace_trend.py` (show improvement)

### Generated Coaching

```markdown
## Coaching Focus

**Sector 2 is costing you 16.25 seconds total** - that's 3x more than any 
other sector. This is the "Angst" hill section with extreme elevation.

### Focus Areas:
1. **Sector 2 consistency** - Your best S2 is 30.85s but average is 31.75s. 
   The 0.9s variance suggests unstable brake point through the blind crest.
2. **Commitment on exit** - Check if you're hesitating back on throttle 
   after the hill. The theoretical optimal shows 0.3s still available.
3. **Pace trend is positive** - You improved 2.3s from early to late laps, 
   showing you're learning the track. Keep this momentum.

### Next Session:
- 10 laps focused ONLY on Sector 2
- Find one consistent brake marker before the crest
- Goal: S2 average under 36.0s (currently 36.8s)
```

---

## Integration with Cursor

### .cursorrules File

The `.cursorrules` file contains:
- Complete workflow instructions
- Decision tree for tool selection
- Coaching style guidelines
- Example patterns and responses

Cursor reads this file and follows the workflow automatically when you ask it to analyze events.

### Usage in Cursor

Simply tell Cursor:
```
"Analyze my Week 02 Event 1"
```

Cursor will:
1. Run `analyze_event.py`
2. Interpret the results
3. Select appropriate tools
4. Generate visualizations
5. Create event markdown with focused coaching

---

## Benefits

### For the Driver (Leon)

- **Less noise**: Only see charts that matter
- **Clear focus**: Know exactly what to work on
- **Faster iteration**: Spend less time analyzing, more time driving
- **Measurable goals**: Clear targets for next session

### For the System

- **Intelligent**: Adapts to event context
- **Scalable**: Easy to add new analysis tools
- **Maintainable**: Clear separation of concerns
- **Efficient**: No wasted processing on irrelevant visualizations

---

## Future Enhancements

### Potential Additions

1. **Traffic Analysis Tool** (`viz_traffic.py`)
   - For race events with high incidents
   - Shows lap time impact of traffic

2. **Telemetry Comparison** (`viz_telemetry_compare.py`)
   - Compare current lap with fastest lap
   - Show speed/throttle/brake differences

3. **Theoretical Optimal** (`viz_optimal_lap.py`)
   - Visualize best possible lap from best sectors
   - Show where time is available

4. **Consistency Heatmap** (`viz_consistency_heatmap.py`)
   - Lap-to-lap variance visualization
   - Identify specific laps with issues

### Learning Memory

Track driver progress across weeks:
- Recurring issues detection
- Long-term improvement trends
- Hypothesis testing integration
- Spaced repetition system integration

---

## Troubleshooting

### Issue: Cursor generates all visualizations

**Solution**: Remind Cursor to follow `.cursorrules` workflow:
```
"Use the adaptive coaching workflow - analyze first, then select tools"
```

### Issue: Generic coaching without data

**Solution**: Reference the JSON output from `analyze_event.py`:
```
"Use specific numbers from the analysis JSON in your coaching"
```

### Issue: Too many focus areas

**Solution**: Limit to 2-3 maximum:
```
"Keep coaching focused - max 3 specific focus areas"
```

---

## Comparison: Week 01 vs Week 02+

| Aspect | Week 01 (Static) | Week 02+ (Adaptive) |
|--------|------------------|---------------------|
| **Analysis** | None | JSON metrics first |
| **Tool Selection** | All tools always | 2-3 relevant tools |
| **Visualizations** | 4+ charts | 2-3 focused charts |
| **Coaching** | Manual/generic | AI-driven/specific |
| **Focus** | Unclear | 2-3 actionable points |
| **Goals** | Vague | Measurable targets |
| **Time** | 10+ minutes | 2-3 minutes |

---

## Quick Reference

### Analysis Commands
```bash
# Analyze event
uv run python tools/analyze_event.py "event.csv" --json

# Analyze week
uv run python tools/analyze_week.py "weeks/weekXX" --json
```

### Visualization Commands
```bash
# Lap progression (always)
uv run python tools/viz_lap_progression.py "event.csv" "output.png" --title "Event #N"

# Sector loss (for sector issues)
uv run python tools/viz_sector_loss.py "event.csv" "output.png" --title "Event #N"

# Pace trend (for consistency issues)
uv run python tools/viz_pace_trend.py "event.csv" "output.png" --title "Event #N"
```

### Cursor Usage
```
"Analyze my Week [XX] Event [N]"
```

---

## Conclusion

The Adaptive Coaching System transforms the iRacing repository into an intelligent coaching tool that:

1. **Understands** what happened in each event
2. **Identifies** key learning opportunities
3. **Visualizes** only what matters
4. **Coaches** with specific, actionable guidance

This creates a faster, more focused workflow that helps Leon improve more efficiently.
