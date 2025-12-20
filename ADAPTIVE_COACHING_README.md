# 🤖 Adaptive Coaching System

## What Changed?

The iRacing repository has been **overhauled** from a static analysis tool into an **intelligent, Cursor-driven adaptive coaching system**.

### Before (Week 01)
```bash
make add-event WEEK=01 FILE=export.csv
```
→ Runs ALL tools automatically → 4+ visualizations always generated → Information overload

### After (Week 02+)
```
Tell Cursor: "Analyze my Week 02 Event 1"
```
→ Cursor analyzes data → Selects 2-3 relevant tools → Generates focused coaching → Clear action items

---

## Quick Start

### 1. Export Data from Garage 61
- Session CSV (lap times, sectors)
- Fastest lap telemetry CSV (optional)

### 2. Tell Cursor to Analyze
```
"Analyze my Week [XX] Event [N]"
```

### 3. Cursor Does the Rest
Cursor will:
1. Run `analyze_event.py` to get JSON metrics
2. Identify patterns (consistency issues, sector problems, pace trends)
3. Select 2-3 relevant visualization tools
4. Generate visualizations
5. Create event markdown with focused coaching
6. Update week README

---

## New Tools

### Analysis Utilities

#### `analyze_event.py`
Returns comprehensive JSON analysis of event data.

```bash
uv run python tools/analyze_event.py "path/to/event.csv" --json
```

**Output includes**:
- Event type (solo/race/time_trial)
- Consistency metrics (σ, variance level)
- Sector analysis (time loss, consistency)
- Pace trend (improving/stable/declining)
- Theoretical optimal lap time

#### `analyze_week.py`
Returns week-level context.

```bash
uv run python tools/analyze_week.py "weeks/week02" --json
```

### Visualization Tools (Modular)

All tools follow the same interface:
```bash
python tools/viz_[TOOL].py "input.csv" "output.png" --title "Title"
```

#### `viz_lap_progression.py`
Baseline lap time chart - **always useful**.

```bash
uv run python tools/viz_lap_progression.py \
  "event.csv" "output.png" --title "Event #1"
```

#### `viz_sector_loss.py`
Sector-by-sector time loss analysis - **for sector-specific issues**.

```bash
uv run python tools/viz_sector_loss.py \
  "event.csv" "output.png" --title "Event #1 Sector Loss"
```

#### `viz_pace_trend.py`
Smoothed pace analysis with consistency corridor - **for consistency issues**.

```bash
uv run python tools/viz_pace_trend.py \
  "event.csv" "output.png" --title "Event #1 Pace Trend"
```

---

## How Cursor Decides

Cursor uses pattern recognition to select tools:

### Pattern: High Variance (σ > 1.5)
**Tools**: lap_progression + sector_loss + pace_trend
**Focus**: Identify problem sector, improve consistency

### Pattern: Sector-Specific Issue (one sector has 2-3x more loss)
**Tools**: lap_progression + sector_loss
**Focus**: Fix the problem sector

### Pattern: Good Consistency (σ < 0.8)
**Tools**: lap_progression only
**Focus**: Celebrate, find next challenge

### Pattern: Improving Trend
**Tools**: lap_progression + sector_loss
**Focus**: Acknowledge progress, identify next step

---

## Example: Week 02 Event 1

### Analysis Data
```json
{
  "consistency": {"sigma": 1.11, "variance_level": "moderate"},
  "sectors": {
    "Sector 1": {"total_loss": 5.88},
    "Sector 2": {"total_loss": 16.25},  // ← 3x more!
    "Sector 3": {"total_loss": 5.20},
    "Sector 4": {"total_loss": 4.93}
  },
  "pace_trend": {"trend": "improving", "improvement": 2.30}
}
```

### Cursor's Decision
- **Pattern**: Moderate σ + clear Sector 2 issue + improving trend
- **Tools**: lap_progression + sector_loss + pace_trend
- **Focus**: Sector 2 consistency

### Generated Coaching
```markdown
## Coaching Focus

**Sector 2 is costing you 16.25 seconds total** - that's 3x more than 
any other sector. This is the "Angst" hill section.

### Focus Areas:
1. **Sector 2 consistency** - Best 30.85s, avg 31.75s (0.9s variance)
2. **Commitment on exit** - Theoretical optimal shows 0.3s available
3. **Pace trend is positive** - Improved 2.3s early to late laps

### Next Session:
- 10 laps focused ONLY on Sector 2
- Find consistent brake marker before blind crest
- Goal: S2 average under 31.0s (currently 31.75s)
```

---

## Files Created

### Tools
- `tools/analyze_event.py` - Event analysis utility (returns JSON)
- `tools/analyze_week.py` - Week context utility (returns JSON)
- `tools/viz_lap_progression.py` - Lap progression chart
- `tools/viz_sector_loss.py` - Sector loss analysis
- `tools/viz_pace_trend.py` - Pace trend with corridor

### Documentation
- `.cursorrules` - Cursor workflow instructions and decision logic
- `docs/ADAPTIVE_COACHING.md` - Complete system documentation
- `Makefile.adaptive` - Helper commands for manual use
- `ADAPTIVE_COACHING_README.md` - This file

### Design Documents
- `/home/ubuntu/cursor_adaptive_coaching_design.md` - Architecture design

---

## Key Benefits

### For You (Leon)
- **Less noise**: Only see charts that matter
- **Clear focus**: Know exactly what to work on
- **Faster iteration**: 2-3 minutes vs 10+ minutes
- **Measurable goals**: Clear targets for next session

### For the System
- **Intelligent**: Adapts to event context
- **Scalable**: Easy to add new tools
- **Maintainable**: Clean separation of concerns
- **Efficient**: No wasted processing

---

## Coaching Style

The system generates coaching that is:

✅ **Specific** - "Sector 2 cost you 16.25s total" not "S2 was slow"
✅ **Actionable** - "Find one brake marker" not "Try to be smoother"
✅ **Concise** - Max 3 focus points
✅ **Measurable** - "S2 average under 31.0s" not "Practice more"
✅ **Data-driven** - References actual lap numbers and times

---

## Usage with Cursor

### Simple Usage
```
"Analyze my Week 02 Event 1"
```

Cursor handles everything automatically.

### If Cursor Needs Guidance
```
"Use the adaptive coaching workflow - analyze first, then select tools"
```

### For Specific Focus
```
"Analyze Event 1 and focus on sector consistency"
```

---

## Manual Usage (Without Cursor)

If you want to run tools manually:

### 1. Analyze Event
```bash
uv run python tools/analyze_event.py \
  "weeks/week02/data/processed/event.csv" --json
```

### 2. Interpret Results
Look for patterns:
- High σ? → Consistency issue
- One sector with 2-3x more loss? → Focus area
- Improving/declining trend? → Context

### 3. Select Tools
Based on patterns, run 2-3 tools:
```bash
uv run python tools/viz_lap_progression.py "event.csv" "output.png"
uv run python tools/viz_sector_loss.py "event.csv" "output.png"
uv run python tools/viz_pace_trend.py "event.csv" "output.png"
```

### 4. Create Event File
Use the template in `.cursorrules` or `docs/ADAPTIVE_COACHING.md`

---

## Integration with Existing Tools

The adaptive coaching system **complements** existing tools:

### Still Available
- `make compare-laps` - Compare best laps across events
- `make update-week` - Update week visualizations
- `make official-report` - Generate race reports
- `make hypothesis-test` - Hypothesis testing framework
- `make srs-review` - Spaced repetition system

### New Workflow
- Use adaptive coaching for **individual event analysis**
- Use existing tools for **week-level summaries** and **special analyses**

---

## Future Enhancements

Potential additions:

1. **Traffic Analysis** (`viz_traffic.py`)
   - For race events with high incidents
   - Shows lap time impact of traffic

2. **Telemetry Comparison** (`viz_telemetry_compare.py`)
   - Compare current lap with fastest lap
   - Show speed/throttle/brake differences

3. **Theoretical Optimal** (`viz_optimal_lap.py`)
   - Visualize best possible lap
   - Show where time is available

4. **Learning Memory**
   - Track recurring issues across weeks
   - Suggest hypothesis tests based on patterns
   - Integrate with spaced repetition system

---

## Troubleshooting

### Cursor generates all visualizations
**Solution**: Remind Cursor to follow the workflow:
```
"Use the adaptive coaching workflow - analyze first, then select tools"
```

### Generic coaching without data
**Solution**: Ask Cursor to reference the analysis:
```
"Use specific numbers from the analysis JSON in your coaching"
```

### Too many focus areas
**Solution**: Limit the scope:
```
"Keep coaching focused - max 3 specific focus areas"
```

---

## Documentation

- **Complete guide**: `docs/ADAPTIVE_COACHING.md`
- **Cursor instructions**: `.cursorrules`
- **Architecture design**: `/home/ubuntu/cursor_adaptive_coaching_design.md`
- **Helper commands**: `Makefile.adaptive`

---

## Questions?

The system is designed to be intuitive with Cursor. Just tell Cursor what you want to analyze, and it will handle the rest using the adaptive coaching workflow.

For detailed information, see `docs/ADAPTIVE_COACHING.md`.

---

**Ready to use!** Just tell Cursor: `"Analyze my Week 02 Event 1"`
