# Archived Tools

This directory contains tools that have been archived because they are obsolete or replaced by the adaptive coaching system.

## Why Archive Instead of Delete?

These tools are preserved in the archive to:
- Maintain git history and context
- Allow easy restoration if needed
- Document the evolution of the system
- Provide reference for understanding old workflows

## Archived Tools

### visualize_event.py (25KB)
**Archived**: 2024-12-20
**Reason**: Replaced by modular visualization tools
**Replacement**: 
- `viz_lap_progression.py` - Lap time chart
- `viz_sector_loss.py` - Sector analysis
- `viz_pace_trend.py` - Pace trend analysis

**Why it was replaced**: 
Monolithic tool that generated ALL visualizations at once. The adaptive coaching system uses modular tools that Cursor selectively calls based on event patterns.

---

### visualize_week.py (22KB)
**Archived**: 2024-12-20
**Reason**: Redundant with `update_week.py`
**Replacement**: `update_week.py`

**Why it was replaced**: 
The `update_week.py` tool already handles week-level visualization generation as part of the week update workflow.

---

### add_event.py (20KB)
**Archived**: 2024-12-20
**Reason**: Replaced by Cursor-driven adaptive workflow
**Replacement**: Cursor analyzes events and selectively runs tools

**Why it was replaced**: 
Old static workflow that automatically ran all visualization tools. The new adaptive coaching system has Cursor analyze event data first, then intelligently select 2-3 relevant tools based on patterns.

**Old workflow**:
```bash
make add-event WEEK=01 FILE=export.csv
→ Runs ALL tools automatically
```

**New workflow**:
```
"Analyze my Week 02 Event 1"
→ Cursor analyzes → Selects relevant tools → Focused coaching
```

---

### analyze_race.py (19KB)
**Archived**: 2024-12-20
**Reason**: Unused - not referenced in Makefile or other tools
**Replacement**: `generate_official_report.py` and `analyze_event.py`

**Why it was replaced**: 
Functionality is covered by `generate_official_report.py` for race reports and `analyze_event.py` for event analysis.

---

## Restoring Archived Tools

If you need to restore an archived tool:

```bash
# Restore to active tools directory
git mv tools/archive/tool_name.py tools/

# Commit the restoration
git commit -m "Restore tool_name.py from archive"
```

---

## Related Documentation

- **Adaptive Coaching System**: See `docs/ADAPTIVE_COACHING.md`
- **Quick Start**: See `ADAPTIVE_COACHING_README.md`
- **Cursor Integration**: See `.cursorrules`
