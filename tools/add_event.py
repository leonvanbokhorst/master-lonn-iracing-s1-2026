"""
Add Event Tool
Processes a Garage61 CSV export and adds it to the week structure.

Usage:
    uv run python tools/add_event.py WEEK CSV_FILE [--telemetry TELEMETRY_CSV]
    
Example:
    uv run python tools/add_event.py 01 ~/Downloads/event.csv
    uv run python tools/add_event.py 01 ~/Downloads/event.csv --telemetry ~/Downloads/lap.csv
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import re

# Import our visualization tools
from visualize_event import load_event_csv, create_event_visualization
from visualize_week import load_week_events, create_week_visualization


def detect_event_type(filename: str) -> str:
    """Detect event type from filename."""
    filename_lower = filename.lower()
    if 'race' in filename_lower:
        return 'ai-race' if 'ai' in filename_lower or 'offline' in filename_lower else 'race'
    elif 'qualify' in filename_lower:
        return 'qualifying'
    else:
        return 'solo'


def get_next_event_number(events_dir: Path) -> int:
    """Get the next event number for this week."""
    existing = list(events_dir.glob("*.md"))
    if not existing:
        return 1
    
    numbers = []
    for f in existing:
        match = re.match(r'(\d+)-', f.name)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers, default=0) + 1


def extract_event_info(df: pd.DataFrame, csv_path: Path) -> dict:
    """Extract event information from dataframe and filename."""
    
    # Basic stats
    info = {
        'laps': len(df),
        'best': df['Lap time'].min(),
        'optimal': df['Optimal'].iloc[0] if 'Optimal' in df.columns else df['Lap time'].min(),
        'sigma': df['Lap time'].std(),
    }
    
    # Settled pace (last 60%)
    settled_start = int(len(df) * 0.4)
    settled_df = df.iloc[settled_start:]
    info['settled'] = settled_df['Lap time'].mean()
    
    # Clean laps
    if 'Valid' in df.columns:
        info['clean_pct'] = (df['Valid'] == True).sum() / len(df) * 100
    else:
        info['clean_pct'] = 100.0
    
    # Try to extract date from filename
    filename = csv_path.name
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if date_match:
        info['date'] = date_match.group(1)
    else:
        # Use file modification time
        mtime = csv_path.stat().st_mtime
        info['date'] = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    
    # Event type
    info['type'] = detect_event_type(filename)
    
    return info


def create_event_page(
    event_num: int,
    week: str,
    info: dict,
    events_dir: Path,
    has_telemetry: bool = False
) -> Path:
    """Create an event markdown page."""
    
    # Read template
    template_path = Path(__file__).parent / "templates" / "event-page.md"
    if template_path.exists():
        template = template_path.read_text()
    else:
        # Fallback simple template
        template = """---
event: {{event_num}}
week: {{week}}
date: "{{date}}"
type: "{{type}}"
---

# Event #{{event_num}} – {{date}} – {{type}}

[← Back to Week](../README.md)

## Quick Stats

| Metric | Value |
|--------|-------|
| **Laps** | {{laps}} |
| **Best Lap** | {{best}}s |
| **Settled Pace** | {{settled}}s |
| **Consistency (σ)** | {{sigma}}s |
| **Clean Laps** | {{clean_pct}}% |

## Debrief

**The Facts:**
- _What happened objectively?_

**The Feelings:**
- _How did it feel?_

**Focus for Next Event:**
1. _..._
"""
    
    # Simple template substitution
    content = template
    content = content.replace('{{event_num}}', str(event_num))
    content = content.replace('{{week}}', week)
    content = content.replace('{{date}}', info['date'])
    content = content.replace('{{type}}', info['type'])
    content = content.replace('{{laps}}', str(info['laps']))
    content = content.replace('{{best}}', f"{info['best']:.3f}")
    content = content.replace('{{optimal}}', f"{info['optimal']:.3f}")
    content = content.replace('{{settled}}', f"{info['settled']:.3f}")
    content = content.replace('{{sigma}}', f"{info['sigma']:.2f}")
    content = content.replace('{{clean_pct}}', f"{info['clean_pct']:.0f}")
    
    # Handle conditional telemetry section
    if not has_telemetry:
        # Remove telemetry section
        content = re.sub(r'\{\{#if telemetry\}\}.*?\{\{/if\}\}', '', content, flags=re.DOTALL)
    else:
        content = content.replace('{{#if telemetry}}', '')
        content = content.replace('{{/if}}', '')
    
    # Event filename
    type_slug = info['type'].replace(' ', '-')
    event_filename = f"{event_num:02d}-{info['date']}-{type_slug}.md"
    event_path = events_dir / event_filename
    
    event_path.write_text(content)
    
    return event_path


def update_week_readme(week: str, weeks_dir: Path, events: list[dict]):
    """Update or create the week README."""
    
    week_dir = weeks_dir / f"week{week}"
    readme_path = week_dir / "README.md"
    
    # Build events table
    table_rows = []
    for e in events:
        notes = "_Add notes..._" if not e.get('notes') else e['notes']
        details_link = f"[→](events/{e['filename']})"
        table_rows.append(
            f"| {e['num']} | {e['date']} | {e['type']} | {e['laps']} | "
            f"{e['best']:.3f}s | {e['sigma']:.2f}s | {notes} | {details_link} |"
        )
    
    events_table = '\n'.join(table_rows)
    
    # Check if README exists and preserve some sections
    if readme_path.exists():
        existing = readme_path.read_text()
        
        # Try to preserve intent and reflection sections
        intent_match = re.search(r'>\s*\*\*Intent:\*\*\s*_(.+?)_', existing)
        intent = intent_match.group(1) if intent_match else "Write your intent here..."
        
        # Preserve reflection section
        reflection_match = re.search(r'## Reflection\n\n(.+?)(?=\n---|\Z)', existing, re.DOTALL)
        reflection = reflection_match.group(1).strip() if reflection_match else """- Track craft takeaways: ...
- Brake bias learnings: ...
- Driver mindset notes: ..."""
    else:
        intent = "Write your intent here..."
        reflection = """- Track craft takeaways: ...
- Brake bias learnings: ...
- Driver mindset notes: ..."""
    
    # Summary stats
    if events:
        best_lap = min(e['best'] for e in events)
        first_lap = events[0]['best']
        last_sigma = events[-1]['sigma']
        improvement = first_lap - best_lap
        
        summary = f"""- **Events:** {len(events)}
- **Best Lap:** {best_lap:.3f}s
- **Improvement:** {improvement:+.3f}s (from {first_lap:.3f}s)
- **Latest σ:** {last_sigma:.2f}s"""
    else:
        summary = "_No events yet._"
    
    # Build README content
    content = f"""---
week: {week}
---

# Week {week} – Summit Point Raceway – Jefferson Circuit

> Track dossier: [Summit Point Jefferson Circuit](../../tracks/track-summit-point-jefferson-circuit.md)

> **Intent:** _{intent}_

## Events

| # | Date | Type | Laps | Best | σ | Notes | Details |
|---|------|------|------|------|---|-------|---------|
{events_table}

## Week Progress

![Week Progress](../../images/week{week}/week-progress.png)

## Lap Comparison

![Lap Comparison](../../images/week{week}/lap-comparison.png)

## Summary

{summary}

## Reflection

{reflection}

---

[← Back to Season](../../README.md)
"""
    
    readme_path.write_text(content)
    return readme_path


def main():
    parser = argparse.ArgumentParser(description="Add event to week structure")
    parser.add_argument("week", type=str, help="Week number (e.g., 01)")
    parser.add_argument("csv_file", type=Path, help="Path to Garage61 CSV export")
    parser.add_argument("--telemetry", "-t", type=Path, help="Optional single-lap telemetry CSV")
    parser.add_argument("--no-viz", action="store_true", help="Skip visualization generation")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.csv_file.exists():
        print(f"❌ CSV file not found: {args.csv_file}")
        return 1
    
    # Setup paths - everything lives under weeks/weekXX/
    project_root = Path(__file__).parent.parent
    week_dir = project_root / "weeks" / f"week{args.week}"
    data_dir = week_dir / "data"
    images_dir = week_dir / "images"
    events_dir = week_dir / "events"
    
    # Create directories
    data_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Adding event to week {args.week}...")
    
    # Copy CSV to data/
    dest_csv = data_dir / args.csv_file.name
    if not dest_csv.exists():
        shutil.copy(args.csv_file, dest_csv)
        print(f"   Copied CSV to data/{dest_csv.name}")
    
    # Load and analyze event
    print(f"   Analyzing event data...")
    df = load_event_csv(args.csv_file)
    info = extract_event_info(df, args.csv_file)
    
    # Determine event number
    event_num = get_next_event_number(events_dir)
    info['num'] = event_num
    
    print(f"   Event #{event_num}: {info['laps']} laps, best {info['best']:.3f}s")
    
    # Generate event visualization
    if not args.no_viz:
        print(f"   Generating event visualization...")
        event_viz_path = images_dir / f"event-{event_num:02d}-laptimes.png"
        create_event_visualization(df, title=f"Event #{event_num} – {info['date']}", 
                                   output_path=event_viz_path)
    
    # Handle telemetry if provided
    has_telemetry = False
    if args.telemetry and args.telemetry.exists():
        print(f"   Processing telemetry...")
        # Copy telemetry
        telem_dest = data_dir / args.telemetry.name
        if not telem_dest.exists():
            shutil.copy(args.telemetry, telem_dest)
        has_telemetry = True
        # TODO: Generate telemetry viz
    
    # Create event page
    print(f"   Creating event page...")
    event_path = create_event_page(event_num, args.week, info, events_dir, has_telemetry)
    info['filename'] = event_path.name
    
    # Load all events for week README
    all_events = []
    for event_file in sorted(events_dir.glob("*.md")):
        match = re.match(r'(\d+)-(\d{4}-\d{2}-\d{2})-(.+)\.md', event_file.name)
        if match:
            num, date, type_slug = match.groups()
            # Read basic info from file (would need to parse, simplified here)
            all_events.append({
                'num': int(num),
                'date': date,
                'type': type_slug.replace('-', ' '),
                'laps': info['laps'] if int(num) == event_num else '?',
                'best': info['best'] if int(num) == event_num else 0,
                'sigma': info['sigma'] if int(num) == event_num else 0,
                'filename': event_file.name,
            })
    
    # Re-sort by number
    all_events.sort(key=lambda x: x['num'])
    
    # Update week README
    print(f"   Updating week README...")
    update_week_readme(args.week, week_dir.parent, all_events)
    
    # Regenerate week visualization
    if not args.no_viz:
        print(f"   Regenerating week visualization...")
        events_data = load_week_events(data_dir)
        if events_data:
            week_viz_path = images_dir / "week-progress.png"
            title = f"WEEK{args.week} Progress – {len(events_data)} Events"
            create_week_visualization(events_data, title=title, output_path=week_viz_path)
    
    print(f"\n✅ Event #{event_num} added!")
    print(f"   📄 Event page: weeks/week{args.week}/events/{event_path.name}")
    print(f"   📊 Week README: weeks/week{args.week}/README.md")
    print(f"\n💡 Next steps:")
    print(f"   1. Edit the event debrief: weeks/week{args.week}/events/{event_path.name}")
    print(f"   2. Update week reflection: weeks/week{args.week}/README.md")
    
    return 0


if __name__ == "__main__":
    exit(main())

