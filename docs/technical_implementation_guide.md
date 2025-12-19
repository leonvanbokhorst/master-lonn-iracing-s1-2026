# Technical Implementation Guide: Learning Science Enhancements for Master Lonn's iRacing System

**Version:** 1.0  
**Date:** December 19, 2025  
**Author:** Manus AI

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Enhancement 1: Mental Rehearsal Protocol](#2-enhancement-1-mental-rehearsal-protocol)
3. [Enhancement 2: Visual Scanning Training](#3-enhancement-2-visual-scanning-training)
4. [Enhancement 3: Situation Anticipation Drills](#4-enhancement-3-situation-anticipation-drills)
5. [Enhancement 4: Interleaved Practice Sessions](#5-enhancement-4-interleaved-practice-sessions)
6. [Enhancement 5: Spaced Repetition System](#6-enhancement-5-spaced-repetition-system)
7. [Enhancement 6: Hypothesis Testing Framework](#7-enhancement-6-hypothesis-testing-framework)
8. [Enhancement 7: Cross-Session Pattern Dashboard](#8-enhancement-7-cross-session-pattern-dashboard)
9. [Enhancement 8: Adaptive Coaching Persona](#9-enhancement-8-adaptive-coaching-persona)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. System Architecture Overview

### 1.1 Current Architecture

The existing system follows a clean, modular architecture built on Python 3.11, using the following structure:

```
master-lonn-iracing-s1-2026/
├── weeks/                  # Weekly logs with event data
│   └── weekXX/
│       ├── README.md       # Week summary
│       ├── events/         # Individual event markdown files
│       ├── data/           # CSV telemetry exports
│       └── images/         # Generated visualizations
├── tracks/                 # Track dossiers
├── coaching/               # AI coaching memory
├── tools/                  # Python automation scripts
│   ├── config.py           # Configuration loader
│   ├── add_event.py        # Event ingestion
│   ├── visualize_*.py      # Visualization generators
│   └── templates/          # Markdown templates
├── config.toml             # Central configuration
├── Makefile                # Workflow commands
└── pyproject.toml          # Python dependencies
```

**Key Technologies:**
- **Python 3.11** with pandas, matplotlib, seaborn
- **TOML** for configuration
- **Markdown** for documentation
- **Makefile** for workflow automation
- **uv** for Python package management
- **Garage61** as external telemetry source

### 1.2 Design Principles for Enhancements

All enhancements must follow these principles:

1. **Minimal Friction:** Add features without disrupting existing workflows
2. **Data Persistence:** Use flat files (TOML/JSON/CSV) for simplicity and Git compatibility
3. **Incremental Adoption:** Features are opt-in, not mandatory
4. **Visualization-First:** Make patterns visible through charts
5. **CLI-Driven:** Extend Makefile with new commands
6. **Template-Based:** Use Jinja2-style templates for consistency

---

## 2. Enhancement 1: Mental Rehearsal Protocol

### 2.1 Objective

Add structured mental rehearsal tracking to event workflow, enabling pre-session visualization and post-session mental replay.

### 2.2 Data Schema

**File:** `weeks/weekXX/events/XX-date-type.md` (extended frontmatter)

```yaml
---
event: 12
week: "01"
date: "2025-12-16"
type: "race"
mental_rehearsal:
  pre_session: true
  duration_minutes: 5
  focus: "T1-T3 transition flow, visual references"
  confidence_rating: 4  # 1-5 scale
  post_session: true
  corrections_rehearsed: ["T6 brake release", "Final corner throttle pickup"]
---
```

### 2.3 Configuration

**File:** `config.toml` (new section)

```toml
[mental_rehearsal]
# Enable mental rehearsal tracking
enabled = true

# Prompt for pre-session rehearsal
pre_session_prompt = true

# Minimum recommended duration (minutes)
min_duration = 3

# Confidence rating scale
confidence_scale = [1, 2, 3, 4, 5]
confidence_labels = ["Very Low", "Low", "Moderate", "High", "Very High"]
```

### 2.4 Implementation: CLI Tool

**File:** `tools/mental_rehearsal.py`

```python
"""
Mental Rehearsal Tool
Guides driver through pre/post-session mental rehearsal protocol.

Usage:
    uv run python tools/mental_rehearsal.py pre --week 01 --event 12
    uv run python tools/mental_rehearsal.py post --week 01 --event 12
"""

import argparse
from pathlib import Path
from datetime import datetime
import yaml
from typing import Literal

def pre_session_rehearsal(week: str, event: int) -> dict:
    """Interactive pre-session mental rehearsal."""
    print("\n🧠 PRE-SESSION MENTAL REHEARSAL")
    print("=" * 50)
    print("Take 3-5 minutes to mentally drive a lap.")
    print("Focus on visual references and transition feelings.\n")
    
    duration = int(input("Duration (minutes): ") or "5")
    focus = input("What are you focusing on? (e.g., 'T1-T3 flow'): ")
    
    print("\nConfidence scale:")
    print("1=Very Low, 2=Low, 3=Moderate, 4=High, 5=Very High")
    confidence = int(input("How confident do you feel? (1-5): ") or "3")
    
    return {
        "pre_session": True,
        "duration_minutes": duration,
        "focus": focus,
        "confidence_rating": confidence,
        "timestamp": datetime.now().isoformat()
    }

def post_session_rehearsal(week: str, event: int) -> dict:
    """Interactive post-session mental replay."""
    print("\n🧠 POST-SESSION MENTAL REPLAY")
    print("=" * 50)
    print("Mentally rehearse any mistakes or corrections 3-5 times.\n")
    
    corrections = []
    while True:
        correction = input("What needs correction? (empty to finish): ")
        if not correction:
            break
        corrections.append(correction)
    
    return {
        "post_session": True,
        "corrections_rehearsed": corrections,
        "timestamp": datetime.now().isoformat()
    }

def update_event_frontmatter(event_file: Path, rehearsal_data: dict):
    """Update event markdown file with rehearsal data."""
    content = event_file.read_text()
    
    # Parse frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
    else:
        frontmatter = {}
        body = content
    
    # Add/update mental_rehearsal section
    if "mental_rehearsal" not in frontmatter:
        frontmatter["mental_rehearsal"] = {}
    
    frontmatter["mental_rehearsal"].update(rehearsal_data)
    
    # Write back
    new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---{body}"
    event_file.write_text(new_content)
    
    print(f"\n✅ Updated {event_file.name}")

def main():
    parser = argparse.ArgumentParser(description="Mental Rehearsal Protocol")
    parser.add_argument("mode", choices=["pre", "post"], help="Pre or post session")
    parser.add_argument("--week", required=True, help="Week number (e.g., 01)")
    parser.add_argument("--event", type=int, required=True, help="Event number")
    
    args = parser.parse_args()
    
    # Find event file
    week_dir = Path(f"weeks/week{args.week}")
    event_files = list(week_dir.glob(f"events/{args.event:02d}-*.md"))
    
    if not event_files:
        print(f"❌ Event file not found for week {args.week}, event {args.event}")
        return
    
    event_file = event_files[0]
    
    # Run rehearsal
    if args.mode == "pre":
        data = pre_session_rehearsal(args.week, args.event)
    else:
        data = post_session_rehearsal(args.week, args.event)
    
    # Update file
    update_event_frontmatter(event_file, data)

if __name__ == "__main__":
    main()
```

### 2.5 Makefile Integration

**File:** `Makefile` (add new targets)

```makefile
# Mental rehearsal workflow
# Usage: make rehearsal-pre WEEK=01 EVENT=12
rehearsal-pre:
	@if [ -z "$(WEEK)" ] || [ -z "$(EVENT)" ]; then \
		echo "❌ Usage: make rehearsal-pre WEEK=01 EVENT=12"; exit 1; \
	fi
	uv run python tools/mental_rehearsal.py pre --week $(WEEK) --event $(EVENT)

# Usage: make rehearsal-post WEEK=01 EVENT=12
rehearsal-post:
	@if [ -z "$(WEEK)" ] || [ -z "$(EVENT)" ]; then \
		echo "❌ Usage: make rehearsal-post WEEK=01 EVENT=12"; exit 1; \
	fi
	uv run python tools/mental_rehearsal.py post --week $(WEEK) --event $(EVENT)
```

### 2.6 Visualization: Rehearsal Impact

**File:** `tools/visualize_rehearsal_impact.py`

```python
"""
Visualize correlation between mental rehearsal and performance.

Usage:
    uv run python tools/visualize_rehearsal_impact.py --week 01
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import yaml

def extract_rehearsal_data(week_dir: Path) -> pd.DataFrame:
    """Extract mental rehearsal data from all events in a week."""
    events = []
    
    for event_file in sorted(week_dir.glob("events/*.md")):
        content = event_file.read_text()
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1])
            
            rehearsal = frontmatter.get("mental_rehearsal", {})
            
            events.append({
                "event": frontmatter.get("event"),
                "pre_session": rehearsal.get("pre_session", False),
                "confidence": rehearsal.get("confidence_rating"),
                "post_session": rehearsal.get("post_session", False),
            })
    
    return pd.DataFrame(events)

def create_rehearsal_visualization(week_dir: Path, output_path: Path):
    """Create visualization showing rehearsal impact on performance."""
    # Load rehearsal data
    rehearsal_df = extract_rehearsal_data(week_dir)
    
    # Load performance data from week CSV
    data_dir = week_dir / "data" / "processed"
    csv_files = sorted(data_dir.glob("*.csv"))
    
    performance_data = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        event_num = int(csv_file.stem.split("-")[0])
        
        performance_data.append({
            "event": event_num,
            "best_lap": df["LapTime"].min(),
            "consistency": df["LapTime"].std(),
        })
    
    perf_df = pd.DataFrame(performance_data)
    
    # Merge
    merged = pd.merge(rehearsal_df, perf_df, on="event", how="inner")
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Confidence vs Consistency
    with_rehearsal = merged[merged["pre_session"] == True]
    without_rehearsal = merged[merged["pre_session"] == False]
    
    ax1.scatter(with_rehearsal["confidence"], with_rehearsal["consistency"], 
                label="With Pre-Rehearsal", s=100, alpha=0.7)
    ax1.scatter(without_rehearsal.index, without_rehearsal["consistency"], 
                label="Without Pre-Rehearsal", s=100, alpha=0.7, marker="x")
    ax1.set_xlabel("Confidence Rating")
    ax1.set_ylabel("Consistency (σ seconds)")
    ax1.set_title("Mental Rehearsal Confidence vs Performance")
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Rehearsal adoption over time
    ax2.plot(merged["event"], merged["pre_session"].astype(int), 
             marker="o", label="Pre-Session Rehearsal")
    ax2.plot(merged["event"], merged["post_session"].astype(int), 
             marker="s", label="Post-Session Replay")
    ax2.set_xlabel("Event Number")
    ax2.set_ylabel("Rehearsal Performed (1=Yes, 0=No)")
    ax2.set_title("Mental Rehearsal Adoption")
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✅ Saved rehearsal visualization to {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True, help="Week number (e.g., 01)")
    args = parser.parse_args()
    
    week_dir = Path(f"weeks/week{args.week}")
    output_path = week_dir / "images" / "mental-rehearsal-impact.png"
    
    create_rehearsal_visualization(week_dir, output_path)

if __name__ == "__main__":
    main()
```

---

## 3. Enhancement 2: Visual Scanning Training

### 3.1 Objective

Document and train systematic visual scanning patterns for each track, reducing variance in "searching sectors."

### 3.2 Data Schema

**File:** `tracks/track-{name}.md` (new section)

```markdown
## Visual Scanning Pattern

> Documented sequence of visual references for optimal eye movement.

| Corner | Entry Reference | Apex Reference | Exit Reference | Next Corner Preview |
|--------|----------------|----------------|----------------|---------------------|
| T1     | Dotted line start | Inside curb edge | Track-out point | T2 turn-in cone |
| T2     | Shadow on tarmac | Apex curb | Exit rumble strip | T3 entry |
| T3     | Tree on left | Inside grass edge | Track edge | Esses entry |

### Eye Movement Drill

**Lap 1-5:** Verbally narrate where your eyes are looking (out loud or mentally)
**Lap 6-10:** Check-in every 3rd corner: "Where are my eyes?"
**Lap 11+:** Let it flow naturally, note any "searching" moments

### Common Mistakes

- ❌ Looking directly in front of car (too late)
- ❌ Fixating on apex before turn-in (missing exit reference)
- ✅ Eyes 2 corners ahead while hands execute current corner
```

### 3.3 Implementation: Visual Reference Mapper

**File:** `tools/map_visual_references.py`

```python
"""
Interactive tool to map visual references for a track.

Usage:
    uv run python tools/map_visual_references.py --track jefferson
"""

import argparse
from pathlib import Path
import yaml

def interactive_reference_mapping(track_name: str):
    """Guide user through documenting visual references."""
    print(f"\n👁️  VISUAL REFERENCE MAPPING: {track_name}")
    print("=" * 60)
    print("For each corner, document what you look at for:")
    print("  - Entry (where to start turn-in)")
    print("  - Apex (where to hit the apex)")
    print("  - Exit (where to track out)")
    print("  - Next (preview of next corner)\n")
    
    corners = []
    corner_num = 1
    
    while True:
        print(f"\n--- Corner T{corner_num} ---")
        name = input(f"Corner name (or 'done' to finish): ")
        
        if name.lower() == "done":
            break
        
        entry_ref = input("  Entry reference: ")
        apex_ref = input("  Apex reference: ")
        exit_ref = input("  Exit reference: ")
        next_ref = input("  Next corner preview: ")
        
        corners.append({
            "corner": name or f"T{corner_num}",
            "entry": entry_ref,
            "apex": apex_ref,
            "exit": exit_ref,
            "next": next_ref
        })
        
        corner_num += 1
    
    return corners

def generate_visual_scanning_markdown(track_name: str, corners: list) -> str:
    """Generate markdown section for track dossier."""
    md = "## Visual Scanning Pattern\n\n"
    md += "> Documented sequence of visual references for optimal eye movement.\n\n"
    
    # Table
    md += "| Corner | Entry Reference | Apex Reference | Exit Reference | Next Corner Preview |\n"
    md += "|--------|----------------|----------------|----------------|---------------------|\n"
    
    for corner in corners:
        md += f"| {corner['corner']} | {corner['entry']} | {corner['apex']} | {corner['exit']} | {corner['next']} |\n"
    
    md += "\n### Eye Movement Drill\n\n"
    md += "**Lap 1-5:** Verbally narrate where your eyes are looking (out loud or mentally)\n"
    md += "**Lap 6-10:** Check-in every 3rd corner: \"Where are my eyes?\"\n"
    md += "**Lap 11+:** Let it flow naturally, note any 'searching' moments\n\n"
    
    md += "### Common Mistakes\n\n"
    md += "- ❌ Looking directly in front of car (too late)\n"
    md += "- ❌ Fixating on apex before turn-in (missing exit reference)\n"
    md += "- ✅ Eyes 2 corners ahead while hands execute current corner\n"
    
    return md

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", required=True, help="Track name (e.g., jefferson)")
    args = parser.parse_args()
    
    corners = interactive_reference_mapping(args.track)
    
    if not corners:
        print("No corners documented.")
        return
    
    markdown = generate_visual_scanning_markdown(args.track, corners)
    
    # Find track file
    track_files = list(Path("tracks").glob(f"*{args.track}*.md"))
    
    if track_files:
        track_file = track_files[0]
        print(f"\n📄 Add this to {track_file.name}:\n")
        print(markdown)
        
        if input("\nAppend to file? (y/n): ").lower() == "y":
            with open(track_file, "a") as f:
                f.write("\n\n---\n\n")
                f.write(markdown)
            print(f"✅ Updated {track_file.name}")
    else:
        print(f"\n❌ Track file not found for '{args.track}'")
        print("Generated markdown:\n")
        print(markdown)

if __name__ == "__main__":
    main()
```

### 3.4 Event Debrief Integration

**File:** `tools/templates/event-page.md` (add section)

```markdown
## Visual Scanning Notes

**Eye discipline rating:** {{eye_discipline_rating}}/5
- 1 = Constantly searching, eyes too close
- 5 = Smooth scanning, 2 corners ahead

**Moments of visual searching:**
- {{visual_search_moments}}

**What worked:**
- {{visual_success}}
```

---

## 4. Enhancement 3: Situation Anticipation Drills

### 4.1 Objective

Build anticipatory racecraft by documenting race scenarios, planned responses, and post-race pattern analysis.

### 4.2 Data Schema

**File:** `weeks/weekXX/events/XX-date-race.md` (for race events only)

```yaml
---
event: 12
week: "01"
date: "2025-12-16"
type: "race"
race_scenarios:
  pre_race_planning:
    - scenario: "P2 dives inside at T1"
      planned_response: "Give space, repass at T6"
      occurred: true
      response_effective: true
    - scenario: "Lap 1 T1 pile-up ahead"
      planned_response: "Lift early, take outside line"
      occurred: false
      response_effective: null
  post_race_patterns:
    - pattern: "3 cars spun at T1 on lap 1"
      common_factor: "Cold tires + aggressive braking"
      future_strategy: "Brake 5m earlier on lap 1, expect chaos"
---
```

### 4.3 Implementation: Scenario Planner

**File:** `tools/scenario_planner.py`

```python
"""
Race Scenario Planning Tool
Pre-race: Plan likely scenarios and responses
Post-race: Review what happened and extract patterns

Usage:
    uv run python tools/scenario_planner.py pre --week 01 --event 12
    uv run python tools/scenario_planner.py post --week 01 --event 12
"""

import argparse
from pathlib import Path
import yaml
from datetime import datetime

def pre_race_planning():
    """Interactive pre-race scenario planning."""
    print("\n🎯 PRE-RACE SCENARIO PLANNING")
    print("=" * 60)
    print("Think through 3 likely scenarios and your planned response.\n")
    
    scenarios = []
    
    for i in range(3):
        print(f"\n--- Scenario {i+1} ---")
        scenario = input("What might happen? (e.g., 'P2 dives inside at T1'): ")
        if not scenario:
            break
        
        response = input("Your planned response: ")
        
        scenarios.append({
            "scenario": scenario,
            "planned_response": response,
            "occurred": None,  # Will be filled post-race
            "response_effective": None
        })
    
    return scenarios

def post_race_review(pre_race_scenarios: list):
    """Review scenarios and extract patterns."""
    print("\n🔍 POST-RACE SCENARIO REVIEW")
    print("=" * 60)
    
    # Review planned scenarios
    for i, scenario in enumerate(pre_race_scenarios):
        print(f"\n--- Scenario {i+1}: {scenario['scenario']} ---")
        occurred = input("Did this happen? (y/n): ").lower() == "y"
        scenario["occurred"] = occurred
        
        if occurred:
            effective = input("Was your response effective? (y/n): ").lower() == "y"
            scenario["response_effective"] = effective
    
    # Extract new patterns
    print("\n--- Pattern Recognition ---")
    patterns = []
    
    while True:
        pattern = input("\nWhat pattern did you notice? (empty to finish): ")
        if not pattern:
            break
        
        common_factor = input("What was the common factor? ")
        future_strategy = input("Future strategy to handle this: ")
        
        patterns.append({
            "pattern": pattern,
            "common_factor": common_factor,
            "future_strategy": future_strategy,
            "date_observed": datetime.now().strftime("%Y-%m-%d")
        })
    
    return patterns

def update_event_with_scenarios(event_file: Path, scenarios: list, patterns: list = None):
    """Update event file with scenario data."""
    content = event_file.read_text()
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
    else:
        frontmatter = {}
        body = content
    
    # Add scenarios
    if "race_scenarios" not in frontmatter:
        frontmatter["race_scenarios"] = {}
    
    if scenarios:
        frontmatter["race_scenarios"]["pre_race_planning"] = scenarios
    
    if patterns:
        frontmatter["race_scenarios"]["post_race_patterns"] = patterns
    
    # Write back
    new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---{body}"
    event_file.write_text(new_content)
    
    print(f"\n✅ Updated {event_file.name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["pre", "post"])
    parser.add_argument("--week", required=True)
    parser.add_argument("--event", type=int, required=True)
    args = parser.parse_args()
    
    # Find event file
    week_dir = Path(f"weeks/week{args.week}")
    event_files = list(week_dir.glob(f"events/{args.event:02d}-*.md"))
    
    if not event_files:
        print(f"❌ Event file not found")
        return
    
    event_file = event_files[0]
    
    if args.mode == "pre":
        scenarios = pre_race_planning()
        update_event_with_scenarios(event_file, scenarios)
    else:
        # Load existing scenarios
        content = event_file.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1])
            pre_scenarios = frontmatter.get("race_scenarios", {}).get("pre_race_planning", [])
        else:
            pre_scenarios = []
        
        post_race_review(pre_scenarios)
        patterns = post_race_review([])
        
        update_event_with_scenarios(event_file, pre_scenarios, patterns)

if __name__ == "__main__":
    main()
```

### 4.4 Pattern Aggregation Across Season

**File:** `tools/aggregate_race_patterns.py`

```python
"""
Aggregate race patterns across all weeks to identify recurring themes.

Usage:
    uv run python tools/aggregate_race_patterns.py --output coaching/race-patterns.md
"""

import argparse
from pathlib import Path
import yaml
from collections import defaultdict

def extract_all_patterns():
    """Extract patterns from all race events."""
    all_patterns = []
    
    for week_dir in sorted(Path("weeks").glob("week*")):
        for event_file in week_dir.glob("events/*-race.md"):
            content = event_file.read_text()
            
            if content.startswith("---"):
                parts = content.split("---", 2)
                frontmatter = yaml.safe_load(parts[1])
                
                scenarios = frontmatter.get("race_scenarios", {})
                patterns = scenarios.get("post_race_patterns", [])
                
                for pattern in patterns:
                    pattern["week"] = week_dir.name
                    pattern["event"] = frontmatter.get("event")
                    all_patterns.append(pattern)
    
    return all_patterns

def generate_pattern_report(patterns: list) -> str:
    """Generate markdown report of recurring patterns."""
    md = "# Race Pattern Analysis\n\n"
    md += "> Recurring patterns observed across official races.\n\n"
    md += f"**Total patterns documented:** {len(patterns)}\n\n"
    
    # Group by common themes
    pattern_groups = defaultdict(list)
    
    for p in patterns:
        # Simple keyword grouping (could be more sophisticated)
        if "T1" in p["pattern"] or "Turn 1" in p["pattern"]:
            pattern_groups["Turn 1 Incidents"].append(p)
        elif "spin" in p["pattern"].lower():
            pattern_groups["Spin Incidents"].append(p)
        else:
            pattern_groups["Other"].append(p)
    
    for group_name, group_patterns in pattern_groups.items():
        md += f"## {group_name}\n\n"
        md += f"**Frequency:** {len(group_patterns)} occurrences\n\n"
        
        for p in group_patterns:
            md += f"### {p['pattern']}\n\n"
            md += f"- **Common Factor:** {p['common_factor']}\n"
            md += f"- **Strategy:** {p['future_strategy']}\n"
            md += f"- **Observed:** Week {p['week']}, Event {p['event']}\n\n"
    
    return md

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="coaching/race-patterns.md")
    args = parser.parse_args()
    
    patterns = extract_all_patterns()
    report = generate_pattern_report(patterns)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report)
    
    print(f"✅ Generated pattern report: {output_path}")
    print(f"📊 {len(patterns)} patterns documented")

if __name__ == "__main__":
    main()
```

---

## 5. Enhancement 4: Interleaved Practice Sessions

### 5.1 Objective

Structure practice sessions to mix different focus areas, improving long-term retention and adaptability.

### 5.2 Data Schema

**File:** `weeks/weekXX/events/XX-date-type.md`

```yaml
---
event: 5
week: "01"
date: "2025-12-13"
type: "solo"
practice_structure:
  type: "interleaved"  # or "blocked"
  blocks:
    - laps: [1, 2, 3, 4, 5]
      focus: "baseline"
      notes: "Establish rhythm"
    - laps: [6, 7, 8, 9, 10]
      focus: "S1_optimization"
      notes: "T1-T3 transitions"
    - laps: [11, 12, 13, 14, 15]
      focus: "race_simulation"
      notes: "Fuel load, traffic awareness"
    - laps: [16, 17, 18, 19, 20]
      focus: "baseline"
      notes: "Return to rhythm"
---
```

### 5.3 Implementation: Practice Session Planner

**File:** `tools/plan_practice_session.py`

```python
"""
Interleaved Practice Session Planner

Usage:
    uv run python tools/plan_practice_session.py --week 01 --event 5 --total-laps 30
"""

import argparse
from pathlib import Path
import yaml

def generate_interleaved_plan(total_laps: int, focus_areas: list) -> list:
    """Generate interleaved practice blocks."""
    laps_per_block = total_laps // len(focus_areas)
    
    blocks = []
    lap_counter = 1
    
    for focus in focus_areas:
        block_laps = list(range(lap_counter, lap_counter + laps_per_block))
        blocks.append({
            "laps": block_laps,
            "focus": focus["name"],
            "notes": focus["description"]
        })
        lap_counter += laps_per_block
    
    return blocks

def interactive_session_planning():
    """Interactive session planning."""
    print("\n📋 INTERLEAVED PRACTICE SESSION PLANNER")
    print("=" * 60)
    
    total_laps = int(input("Total laps planned: ") or "30")
    
    print("\nCommon focus areas:")
    print("  1. baseline - Establish rhythm")
    print("  2. sector_X - Focus on specific sector")
    print("  3. race_simulation - Race pace with traffic")
    print("  4. consistency - Minimize variance")
    print("  5. qualifying - Single-lap pace\n")
    
    focus_areas = []
    
    while True:
        focus_name = input(f"Focus area {len(focus_areas)+1} (empty to finish): ")
        if not focus_name:
            break
        
        description = input("  Description: ")
        
        focus_areas.append({
            "name": focus_name,
            "description": description
        })
    
    if not focus_areas:
        print("❌ No focus areas defined. Using default interleaved plan.")
        focus_areas = [
            {"name": "baseline", "description": "Establish rhythm"},
            {"name": "sector_focus", "description": "Work on weak sector"},
            {"name": "race_simulation", "description": "Race pace"},
            {"name": "baseline", "description": "Return to rhythm"}
        ]
    
    blocks = generate_interleaved_plan(total_laps, focus_areas)
    
    return {
        "type": "interleaved",
        "blocks": blocks
    }

def display_session_plan(plan: dict):
    """Display the session plan."""
    print("\n📊 SESSION PLAN")
    print("=" * 60)
    
    for i, block in enumerate(plan["blocks"]):
        lap_range = f"{block['laps'][0]}-{block['laps'][-1]}"
        print(f"\nBlock {i+1}: Laps {lap_range}")
        print(f"  Focus: {block['focus']}")
        print(f"  Notes: {block['notes']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--event", type=int, required=True)
    parser.add_argument("--total-laps", type=int, default=30)
    args = parser.parse_args()
    
    plan = interactive_session_planning()
    display_session_plan(plan)
    
    # Save to event file
    week_dir = Path(f"weeks/week{args.week}")
    event_files = list(week_dir.glob(f"events/{args.event:02d}-*.md"))
    
    if event_files:
        event_file = event_files[0]
        
        content = event_file.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2]
        else:
            frontmatter = {}
            body = content
        
        frontmatter["practice_structure"] = plan
        
        new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---{body}"
        event_file.write_text(new_content)
        
        print(f"\n✅ Saved plan to {event_file.name}")

if __name__ == "__main__":
    main()
```

---

## 6. Enhancement 5: Spaced Repetition System

### 6.1 Objective

Implement spaced repetition for track knowledge review to improve long-term retention.

### 6.2 Data Schema

**File:** `coaching/spaced-repetition.yaml`

```yaml
# Spaced Repetition Schedule for Track Knowledge

tracks:
  - name: "Summit Point Jefferson"
    week_learned: 1
    last_reviewed: "2025-12-22"
    next_review: "2025-12-29"  # +7 days
    review_count: 0
    mastery_level: 1  # 1-5 scale
    
  - name: "Rudskogen Motorsenter"
    week_learned: 2
    last_reviewed: null
    next_review: "2025-12-30"
    review_count: 0
    mastery_level: 1

review_intervals:
  level_1: [1, 3, 7]      # Days after learning
  level_2: [7, 14, 28]
  level_3: [14, 28, 56]
  level_4: [28, 56, 112]
  level_5: [56, 112, 224]
```

### 6.3 Implementation: Spaced Repetition Manager

**File:** `tools/spaced_repetition.py`

```python
"""
Spaced Repetition System for Track Knowledge

Usage:
    uv run python tools/spaced_repetition.py check     # Check what needs review
    uv run python tools/spaced_repetition.py review    # Mark track as reviewed
    uv run python tools/spaced_repetition.py add --track "Track Name" --week 01
"""

import argparse
from pathlib import Path
import yaml
from datetime import datetime, timedelta

SPACED_REP_FILE = Path("coaching/spaced-repetition.yaml")

def load_spaced_rep_data():
    """Load spaced repetition data."""
    if not SPACED_REP_FILE.exists():
        return {
            "tracks": [],
            "review_intervals": {
                "level_1": [1, 3, 7],
                "level_2": [7, 14, 28],
                "level_3": [14, 28, 56],
                "level_4": [28, 56, 112],
                "level_5": [56, 112, 224]
            }
        }
    
    return yaml.safe_load(SPACED_REP_FILE.read_text())

def save_spaced_rep_data(data: dict):
    """Save spaced repetition data."""
    SPACED_REP_FILE.parent.mkdir(exist_ok=True)
    SPACED_REP_FILE.write_text(yaml.dump(data, default_flow_style=False))

def check_due_reviews():
    """Check which tracks need review."""
    data = load_spaced_rep_data()
    today = datetime.now().date()
    
    due_tracks = []
    
    for track in data["tracks"]:
        next_review = datetime.strptime(track["next_review"], "%Y-%m-%d").date()
        
        if next_review <= today:
            days_overdue = (today - next_review).days
            due_tracks.append({
                "name": track["name"],
                "days_overdue": days_overdue,
                "mastery_level": track["mastery_level"]
            })
    
    return due_tracks

def display_due_reviews(due_tracks: list):
    """Display tracks that need review."""
    print("\n📚 SPACED REPETITION REVIEW")
    print("=" * 60)
    
    if not due_tracks:
        print("✅ No tracks due for review today!")
        return
    
    print(f"\n{len(due_tracks)} track(s) need review:\n")
    
    for track in due_tracks:
        status = "⚠️ OVERDUE" if track["days_overdue"] > 0 else "📅 DUE TODAY"
        print(f"{status} {track['name']}")
        print(f"  Mastery Level: {track['mastery_level']}/5")
        if track["days_overdue"] > 0:
            print(f"  Overdue by: {track['days_overdue']} days")
        print()

def add_track(track_name: str, week: int):
    """Add a new track to the spaced repetition system."""
    data = load_spaced_rep_data()
    
    # Check if track already exists
    for track in data["tracks"]:
        if track["name"] == track_name:
            print(f"❌ Track '{track_name}' already in system")
            return
    
    today = datetime.now().date()
    first_review = today + timedelta(days=1)
    
    data["tracks"].append({
        "name": track_name,
        "week_learned": week,
        "last_reviewed": None,
        "next_review": first_review.strftime("%Y-%m-%d"),
        "review_count": 0,
        "mastery_level": 1
    })
    
    save_spaced_rep_data(data)
    print(f"✅ Added '{track_name}' to spaced repetition system")
    print(f"📅 First review scheduled for: {first_review}")

def mark_reviewed(track_name: str, mastery_rating: int):
    """Mark a track as reviewed and schedule next review."""
    data = load_spaced_rep_data()
    
    track = None
    for t in data["tracks"]:
        if t["name"].lower() == track_name.lower():
            track = t
            break
    
    if not track:
        print(f"❌ Track '{track_name}' not found")
        return
    
    # Update mastery level
    track["mastery_level"] = mastery_rating
    track["review_count"] += 1
    track["last_reviewed"] = datetime.now().date().strftime("%Y-%m-%d")
    
    # Calculate next review date
    intervals = data["review_intervals"][f"level_{mastery_rating}"]
    interval_index = min(track["review_count"] - 1, len(intervals) - 1)
    days_until_next = intervals[interval_index]
    
    next_review = datetime.now().date() + timedelta(days=days_until_next)
    track["next_review"] = next_review.strftime("%Y-%m-%d")
    
    save_spaced_rep_data(data)
    
    print(f"✅ Marked '{track_name}' as reviewed")
    print(f"📊 Mastery Level: {mastery_rating}/5")
    print(f"📅 Next review: {next_review} ({days_until_next} days)")

def interactive_review():
    """Interactive review session."""
    due_tracks = check_due_reviews()
    
    if not due_tracks:
        print("✅ No tracks due for review!")
        return
    
    display_due_reviews(due_tracks)
    
    print("\nReview each track:")
    print("  - Read the track dossier")
    print("  - Recall key learnings")
    print("  - Rate your mastery (1-5)\n")
    
    for track in due_tracks:
        print(f"\n--- {track['name']} ---")
        
        # Find track file
        track_files = list(Path("tracks").glob(f"*{track['name'].lower().replace(' ', '-')}*.md"))
        
        if track_files:
            print(f"📄 Track dossier: {track_files[0]}")
        
        input("Press Enter when you've reviewed the track...")
        
        mastery = int(input("Mastery rating (1-5): ") or "3")
        mark_reviewed(track["name"], mastery)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check", "review", "add"])
    parser.add_argument("--track", help="Track name (for add command)")
    parser.add_argument("--week", type=int, help="Week number (for add command)")
    args = parser.parse_args()
    
    if args.command == "check":
        due_tracks = check_due_reviews()
        display_due_reviews(due_tracks)
    
    elif args.command == "review":
        interactive_review()
    
    elif args.command == "add":
        if not args.track or not args.week:
            print("❌ Usage: spaced_repetition.py add --track 'Track Name' --week 01")
            return
        add_track(args.track, args.week)

if __name__ == "__main__":
    main()
```

### 6.4 Makefile Integration

```makefile
# Spaced repetition commands
spaced-rep-check:
	uv run python tools/spaced_repetition.py check

spaced-rep-review:
	uv run python tools/spaced_repetition.py review

spaced-rep-add:
	@if [ -z "$(TRACK)" ] || [ -z "$(WEEK)" ]; then \
		echo "❌ Usage: make spaced-rep-add TRACK='Track Name' WEEK=01"; exit 1; \
	fi
	uv run python tools/spaced_repetition.py add --track "$(TRACK)" --week $(WEEK)
```

---

## 7. Enhancement 6: Hypothesis Testing Framework

### 7.1 Objective

Formalize the hypothesis-driven learning approach that proved successful in Week 01.

### 7.2 Data Schema

**File:** `coaching/hypotheses.yaml`

```yaml
hypotheses:
  - id: 1
    title: "Patience Protocol"
    hypothesis: "Following slower cars for 2 laps before passing improves consistency"
    predicted_outcome: "Consistency (σ) will decrease by >50%"
    test_method: "Event #5 impatient, Event #6 patient"
    status: "validated"
    results:
      - event: 5
        week: 1
        metric: "consistency"
        value: 3.44
        notes: "Impatient overtaking"
      - event: 6
        week: 1
        metric: "consistency"
        value: 0.23
        notes: "Patient following"
    conclusion: "Hypothesis validated. 15x improvement in consistency."
    generalization_tests:
      - week: 2
        track: "Rudskogen"
        status: "pending"
    
  - id: 2
    title: "Coasting Transfer"
    hypothesis: "Coasting optimization learned at Jefferson will transfer to new tracks"
    predicted_outcome: "Week 02 Event #1 will show <5% coasting"
    test_method: "Compare coasting % between Week 01 final and Week 02 first event"
    status: "active"
    results: []
```

### 7.3 Implementation: Hypothesis Manager

**File:** `tools/hypothesis_manager.py`

```python
"""
Hypothesis Testing Framework

Usage:
    uv run python tools/hypothesis_manager.py list
    uv run python tools/hypothesis_manager.py add
    uv run python tools/hypothesis_manager.py update --id 2 --week 02 --event 1
    uv run python tools/hypothesis_manager.py report
"""

import argparse
from pathlib import Path
import yaml
from datetime import datetime

HYPOTHESES_FILE = Path("coaching/hypotheses.yaml")

def load_hypotheses():
    """Load hypotheses data."""
    if not HYPOTHESES_FILE.exists():
        return {"hypotheses": []}
    return yaml.safe_load(HYPOTHESES_FILE.read_text())

def save_hypotheses(data: dict):
    """Save hypotheses data."""
    HYPOTHESES_FILE.parent.mkdir(exist_ok=True)
    HYPOTHESES_FILE.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

def list_hypotheses():
    """List all hypotheses."""
    data = load_hypotheses()
    
    print("\n🔬 HYPOTHESIS TRACKER")
    print("=" * 60)
    
    if not data["hypotheses"]:
        print("No hypotheses tracked yet.")
        return
    
    for h in data["hypotheses"]:
        status_icon = {
            "active": "🔄",
            "validated": "✅",
            "refuted": "❌",
            "pending": "⏳"
        }.get(h["status"], "❓")
        
        print(f"\n{status_icon} [{h['id']}] {h['title']}")
        print(f"   Status: {h['status'].upper()}")
        print(f"   Hypothesis: {h['hypothesis']}")
        print(f"   Predicted: {h['predicted_outcome']}")
        
        if h["results"]:
            print(f"   Results: {len(h['results'])} data points")

def add_hypothesis():
    """Interactive hypothesis creation."""
    data = load_hypotheses()
    
    print("\n🔬 NEW HYPOTHESIS")
    print("=" * 60)
    
    title = input("Title (short name): ")
    hypothesis = input("Hypothesis statement: ")
    predicted = input("Predicted outcome: ")
    test_method = input("How will you test this? ")
    
    new_id = max([h["id"] for h in data["hypotheses"]], default=0) + 1
    
    data["hypotheses"].append({
        "id": new_id,
        "title": title,
        "hypothesis": hypothesis,
        "predicted_outcome": predicted,
        "test_method": test_method,
        "status": "active",
        "results": [],
        "created_date": datetime.now().strftime("%Y-%m-%d")
    })
    
    save_hypotheses(data)
    print(f"\n✅ Created hypothesis #{new_id}: {title}")

def update_hypothesis(hyp_id: int, week: int, event: int):
    """Add test result to hypothesis."""
    data = load_hypotheses()
    
    hypothesis = None
    for h in data["hypotheses"]:
        if h["id"] == hyp_id:
            hypothesis = h
            break
    
    if not hypothesis:
        print(f"❌ Hypothesis #{hyp_id} not found")
        return
    
    print(f"\n🔬 UPDATE HYPOTHESIS: {hypothesis['title']}")
    print("=" * 60)
    print(f"Hypothesis: {hypothesis['hypothesis']}")
    print(f"Predicted: {hypothesis['predicted_outcome']}\n")
    
    metric = input("Metric measured (e.g., 'consistency', 'coasting%'): ")
    value = float(input("Value: "))
    notes = input("Notes: ")
    
    hypothesis["results"].append({
        "week": week,
        "event": event,
        "metric": metric,
        "value": value,
        "notes": notes,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    
    # Ask if hypothesis is now validated/refuted
    print("\nBased on this result:")
    print("  1. Keep active (need more data)")
    print("  2. Mark as validated")
    print("  3. Mark as refuted")
    
    choice = input("Choice (1/2/3): ")
    
    if choice == "2":
        hypothesis["status"] = "validated"
        conclusion = input("Conclusion: ")
        hypothesis["conclusion"] = conclusion
    elif choice == "3":
        hypothesis["status"] = "refuted"
        conclusion = input("Why was it refuted? ")
        hypothesis["conclusion"] = conclusion
    
    save_hypotheses(data)
    print(f"\n✅ Updated hypothesis #{hyp_id}")

def generate_report():
    """Generate hypothesis testing report."""
    data = load_hypotheses()
    
    md = "# Hypothesis Testing Report\n\n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # Summary stats
    total = len(data["hypotheses"])
    validated = len([h for h in data["hypotheses"] if h["status"] == "validated"])
    refuted = len([h for h in data["hypotheses"] if h["status"] == "refuted"])
    active = len([h for h in data["hypotheses"] if h["status"] == "active"])
    
    md += "## Summary\n\n"
    md += f"- **Total Hypotheses:** {total}\n"
    md += f"- **Validated:** {validated}\n"
    md += f"- **Refuted:** {refuted}\n"
    md += f"- **Active:** {active}\n\n"
    
    # Detailed hypotheses
    for status in ["validated", "active", "refuted"]:
        hypotheses = [h for h in data["hypotheses"] if h["status"] == status]
        
        if not hypotheses:
            continue
        
        md += f"## {status.capitalize()} Hypotheses\n\n"
        
        for h in hypotheses:
            md += f"### [{h['id']}] {h['title']}\n\n"
            md += f"**Hypothesis:** {h['hypothesis']}\n\n"
            md += f"**Predicted Outcome:** {h['predicted_outcome']}\n\n"
            md += f"**Test Method:** {h['test_method']}\n\n"
            
            if h["results"]:
                md += "**Results:**\n\n"
                md += "| Week | Event | Metric | Value | Notes |\n"
                md += "|------|-------|--------|-------|-------|\n"
                
                for r in h["results"]:
                    md += f"| {r['week']} | {r['event']} | {r['metric']} | {r['value']} | {r['notes']} |\n"
                md += "\n"
            
            if "conclusion" in h:
                md += f"**Conclusion:** {h['conclusion']}\n\n"
            
            md += "---\n\n"
    
    output_path = Path("coaching/hypothesis-report.md")
    output_path.write_text(md)
    
    print(f"✅ Generated report: {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["list", "add", "update", "report"])
    parser.add_argument("--id", type=int, help="Hypothesis ID (for update)")
    parser.add_argument("--week", type=int, help="Week number (for update)")
    parser.add_argument("--event", type=int, help="Event number (for update)")
    args = parser.parse_args()
    
    if args.command == "list":
        list_hypotheses()
    elif args.command == "add":
        add_hypothesis()
    elif args.command == "update":
        if not args.id or not args.week or not args.event:
            print("❌ Usage: hypothesis_manager.py update --id 1 --week 02 --event 1")
            return
        update_hypothesis(args.id, args.week, args.event)
    elif args.command == "report":
        generate_report()

if __name__ == "__main__":
    main()
```

---

## 8. Enhancement 7: Cross-Session Pattern Dashboard

### 8.1 Objective

Create season-level visualizations to identify long-term trends and patterns across all weeks.

### 8.2 Implementation

**File:** `tools/visualize_season.py`

```python
"""
Season-Level Dashboard Generator

Usage:
    uv run python tools/visualize_season.py --output coaching/season-dashboard.png
"""

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def load_all_events():
    """Load all event data across all weeks."""
    all_events = []
    
    for week_dir in sorted(Path("weeks").glob("week*")):
        week_num = int(week_dir.name.replace("week", ""))
        
        data_dir = week_dir / "data" / "processed"
        
        for csv_file in sorted(data_dir.glob("*.csv")):
            df = pd.read_csv(csv_file)
            
            event_num = int(csv_file.stem.split("-")[0])
            
            all_events.append({
                "week": week_num,
                "event": event_num,
                "best_lap": df["LapTime"].min(),
                "consistency": df["LapTime"].std(),
                "laps": len(df),
                "date": csv_file.stem.split("-")[1]
            })
    
    return pd.DataFrame(all_events)

def create_season_dashboard(output_path: Path):
    """Create comprehensive season dashboard."""
    df = load_all_events()
    
    if df.empty:
        print("❌ No event data found")
        return
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Best Lap Progression (normalized by track)
    ax1 = fig.add_subplot(gs[0, :2])
    for week in df["week"].unique():
        week_data = df[df["week"] == week]
        ax1.plot(week_data["event"], week_data["best_lap"], 
                marker="o", label=f"Week {week}")
    ax1.set_xlabel("Event Number (within week)")
    ax1.set_ylabel("Best Lap Time (s)")
    ax1.set_title("Best Lap Progression Across Season")
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. Consistency Evolution
    ax2 = fig.add_subplot(gs[0, 2])
    df["event_global"] = range(len(df))
    ax2.plot(df["event_global"], df["consistency"], marker="o", color="coral")
    ax2.set_xlabel("Event Number (season)")
    ax2.set_ylabel("Consistency (σ seconds)")
    ax2.set_title("Consistency Over Time")
    ax2.grid(alpha=0.3)
    
    # 3. Weekly Best Lap Improvement
    ax3 = fig.add_subplot(gs[1, 0])
    weekly_improvement = []
    for week in df["week"].unique():
        week_data = df[df["week"] == week]
        if len(week_data) > 1:
            improvement = week_data.iloc[0]["best_lap"] - week_data.iloc[-1]["best_lap"]
            weekly_improvement.append({"week": week, "improvement": improvement})
    
    imp_df = pd.DataFrame(weekly_improvement)
    if not imp_df.empty:
        ax3.bar(imp_df["week"], imp_df["improvement"], color="skyblue")
        ax3.set_xlabel("Week")
        ax3.set_ylabel("Improvement (seconds)")
        ax3.set_title("Weekly Lap Time Improvement")
        ax3.grid(axis="y", alpha=0.3)
    
    # 4. Consistency Distribution
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.hist(df["consistency"], bins=15, color="lightgreen", edgecolor="black")
    ax4.axvline(df["consistency"].median(), color="red", linestyle="--", 
                label=f"Median: {df['consistency'].median():.2f}s")
    ax4.set_xlabel("Consistency (σ seconds)")
    ax4.set_ylabel("Frequency")
    ax4.set_title("Consistency Distribution")
    ax4.legend()
    
    # 5. Events per Week
    ax5 = fig.add_subplot(gs[1, 2])
    events_per_week = df.groupby("week").size()
    ax5.bar(events_per_week.index, events_per_week.values, color="mediumpurple")
    ax5.set_xlabel("Week")
    ax5.set_ylabel("Number of Events")
    ax5.set_title("Practice Volume")
    ax5.grid(axis="y", alpha=0.3)
    
    # 6. Season Summary Stats
    ax6 = fig.add_subplot(gs[2, :])
    ax6.axis("off")
    
    summary_text = f"""
    SEASON SUMMARY STATISTICS
    
    Total Events: {len(df)}
    Weeks Completed: {df['week'].nunique()}
    
    Best Lap (Overall): {df['best_lap'].min():.3f}s
    Best Consistency: {df['consistency'].min():.3f}s
    
    Average Consistency: {df['consistency'].mean():.3f}s
    Consistency Improvement: {df['consistency'].iloc[0] - df['consistency'].iloc[-1]:.3f}s
    
    Total Laps: {df['laps'].sum()}
    """
    
    ax6.text(0.1, 0.5, summary_text, fontsize=12, family="monospace",
             verticalalignment="center")
    
    plt.suptitle("iRacing Season Dashboard", fontsize=16, fontweight="bold")
    
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✅ Generated season dashboard: {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="coaching/season-dashboard.png")
    args = parser.parse_args()
    
    create_season_dashboard(Path(args.output))

if __name__ == "__main__":
    main()
```

---

## 9. Enhancement 8: Adaptive Coaching Persona

### 9.1 Objective

Make the AI coach context-aware, adapting tone and focus based on performance trends and driver state.

### 9.2 Data Schema

**File:** `coaching/coaching-context.yaml`

```yaml
# Coaching Context - Updated after each coaching session

current_state:
  performance_trend: "improving"  # improving, plateauing, declining
  recent_consistency: 0.38  # Last event σ
  recent_incidents: 2
  weeks_completed: 1
  
coaching_preferences:
  preferred_tone: "balanced"  # supportive, challenging, technical, balanced
  detail_level: "moderate"  # brief, moderate, detailed
  focus_areas: ["consistency", "racecraft"]
  
coaching_history:
  last_session_date: "2025-12-17"
  last_mode: "celebration"  # celebration, technical, motivation, challenge
  effectiveness_rating: 5  # 1-5, driver rates coaching
  
performance_context:
  consecutive_improvements: 3
  consecutive_setbacks: 0
  best_lap_plateau_events: 0  # Events since last PB
```

### 9.3 Implementation: Adaptive Coach

**File:** `tools/adaptive_coach.py`

```python
"""
Adaptive AI Coaching System

Generates context-aware coaching prompts based on performance trends.

Usage:
    uv run python tools/adaptive_coach.py --week 01 --event 13
"""

import argparse
from pathlib import Path
import yaml
from datetime import datetime

def load_coaching_context():
    """Load current coaching context."""
    context_file = Path("coaching/coaching-context.yaml")
    
    if not context_file.exists():
        return {
            "current_state": {
                "performance_trend": "improving",
                "recent_consistency": None,
                "recent_incidents": 0,
                "weeks_completed": 0
            },
            "coaching_preferences": {
                "preferred_tone": "balanced",
                "detail_level": "moderate",
                "focus_areas": []
            },
            "coaching_history": {
                "last_session_date": None,
                "last_mode": None,
                "effectiveness_rating": None
            },
            "performance_context": {
                "consecutive_improvements": 0,
                "consecutive_setbacks": 0,
                "best_lap_plateau_events": 0
            }
        }
    
    return yaml.safe_load(context_file.read_text())

def save_coaching_context(context: dict):
    """Save coaching context."""
    context_file = Path("coaching/coaching-context.yaml")
    context_file.parent.mkdir(exist_ok=True)
    context_file.write_text(yaml.dump(context, default_flow_style=False))

def analyze_performance_trend(week: int, event: int) -> dict:
    """Analyze recent performance to determine trend."""
    # Load recent events
    week_dir = Path(f"weeks/week{week:02d}")
    data_dir = week_dir / "data" / "processed"
    
    recent_events = sorted(data_dir.glob("*.csv"))[-3:]  # Last 3 events
    
    if len(recent_events) < 2:
        return {"trend": "insufficient_data"}
    
    import pandas as pd
    
    best_laps = []
    consistencies = []
    
    for csv_file in recent_events:
        df = pd.read_csv(csv_file)
        best_laps.append(df["LapTime"].min())
        consistencies.append(df["LapTime"].std())
    
    # Determine trend
    lap_improving = best_laps[-1] < best_laps[0]
    consistency_improving = consistencies[-1] < consistencies[0]
    
    if lap_improving and consistency_improving:
        trend = "improving"
    elif not lap_improving and not consistency_improving:
        trend = "declining"
    else:
        trend = "plateauing"
    
    return {
        "trend": trend,
        "recent_consistency": consistencies[-1],
        "lap_improvement": best_laps[0] - best_laps[-1]
    }

def generate_coaching_prompt(context: dict, performance: dict) -> str:
    """Generate context-aware coaching prompt for LLM."""
    
    # Determine coaching mode
    trend = performance.get("trend", "insufficient_data")
    consistency = performance.get("recent_consistency", 0)
    
    if trend == "improving":
        mode = "celebration"
        tone = "encouraging and proud"
    elif trend == "declining":
        mode = "supportive"
        tone = "honest but supportive"
    elif trend == "plateauing":
        mode = "challenge"
        tone = "thought-provoking"
    else:
        mode = "technical"
        tone = "analytical"
    
    # Build prompt
    prompt = f"""You are Little Padawan, the AI racing coach for Master Lonn.

COACHING CONTEXT:
- Performance Trend: {trend}
- Recent Consistency: {consistency:.2f}s
- Coaching Mode: {mode}
- Preferred Tone: {tone}

COACHING PHILOSOPHY:
- Ask questions, don't prescribe
- Connect data to feeling
- Be honest, even when uncomfortable
- Celebrate real wins, not participation trophies

TASK:
Review the latest event and provide coaching feedback that:
1. Acknowledges what the data shows
2. Asks a reflective question
3. Proposes one hypothesis to test next

Keep it concise (3-4 sentences). Use the tone: {tone}.
"""
    
    return prompt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--event", type=int, required=True)
    args = parser.parse_args()
    
    # Load context
    context = load_coaching_context()
    
    # Analyze performance
    performance = analyze_performance_trend(args.week, args.event)
    
    # Generate prompt
    prompt = generate_coaching_prompt(context, performance)
    
    print("\n🤖 ADAPTIVE COACHING PROMPT")
    print("=" * 60)
    print(prompt)
    print("\n" + "=" * 60)
    print("\nCopy this prompt to your LLM to generate coaching feedback.")
    
    # Update context
    context["current_state"]["performance_trend"] = performance.get("trend")
    context["current_state"]["recent_consistency"] = performance.get("recent_consistency")
    context["coaching_history"]["last_session_date"] = datetime.now().strftime("%Y-%m-%d")
    
    save_coaching_context(context)

if __name__ == "__main__":
    main()
```

---

## 10. Implementation Roadmap

### Phase 1: Immediate (Weeks 2-3)

**Priority:** Low-friction, high-impact enhancements

1. **Mental Rehearsal Protocol**
   - Implement `mental_rehearsal.py`
   - Add Makefile targets
   - Test with Week 02 events
   - **Effort:** 2-3 hours

2. **Hypothesis Testing Framework**
   - Implement `hypothesis_manager.py`
   - Backfill Week 01 patience hypothesis
   - Add coasting transfer hypothesis for Week 02
   - **Effort:** 3-4 hours

3. **Spaced Repetition System**
   - Implement `spaced_repetition.py`
   - Add Jefferson track to system
   - Set up daily check routine
   - **Effort:** 2-3 hours

### Phase 2: Near-term (Weeks 4-6)

**Priority:** Skill-specific training tools

4. **Visual Scanning Training**
   - Implement `map_visual_references.py`
   - Document Jefferson visual pattern
   - Add to event debrief template
   - **Effort:** 3-4 hours

5. **Situation Anticipation Drills**
   - Implement `scenario_planner.py`
   - Use for next official race
   - Start pattern aggregation
   - **Effort:** 4-5 hours

6. **Interleaved Practice**
   - Implement `plan_practice_session.py`
   - Test with one practice session
   - Compare blocked vs interleaved outcomes
   - **Effort:** 2-3 hours

### Phase 3: Mid-season (Weeks 7-9)

**Priority:** Analytics and insights

7. **Season Dashboard**
   - Implement `visualize_season.py`
   - Generate first dashboard after 4-5 weeks
   - Add to weekly review routine
   - **Effort:** 4-5 hours

8. **Adaptive Coaching**
   - Implement `adaptive_coach.py`
   - Test different coaching modes
   - Collect effectiveness ratings
   - **Effort:** 3-4 hours

### Total Implementation Effort

- **Phase 1:** 7-10 hours
- **Phase 2:** 9-12 hours
- **Phase 3:** 7-9 hours
- **Total:** 23-31 hours over 7-9 weeks

### Testing Strategy

Each enhancement should be:
1. **Implemented** in isolation
2. **Tested** with 2-3 events
3. **Evaluated** for impact and friction
4. **Refined** based on feedback
5. **Documented** with examples

### Success Metrics

- **Adoption Rate:** % of events using the feature
- **Time Cost:** Minutes added to workflow
- **Perceived Value:** Driver rating (1-5)
- **Performance Impact:** Correlation with metrics

---

## Conclusion

This technical implementation guide provides complete specifications for integrating advanced learning science principles into Master Lonn's iRacing system. Each enhancement is designed to be:

- **Modular:** Can be implemented independently
- **Low-friction:** Minimal disruption to existing workflow
- **Data-driven:** Produces measurable outcomes
- **Scalable:** Works across entire 12-week season

The phased roadmap ensures sustainable implementation without overwhelming the driver or compromising the core practice of "keep showing up."
