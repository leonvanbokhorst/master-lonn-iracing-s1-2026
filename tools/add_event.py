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
from visualize_telemetry import load_telemetry, create_telemetry_visualization, compute_coasting_zones


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


def parse_event_stats(md_path: Path) -> dict:
    """Extract stats from an event markdown file."""
    if not md_path.exists():
        return {}
        
    content = md_path.read_text()
    stats = {}
    
    # Extract Laps
    laps_match = re.search(r'\|\s*\*\*Laps\*\*\s*\|\s*(\d+)\s*\|', content)
    if laps_match:
        stats['laps'] = int(laps_match.group(1))
        
    # Extract Best Lap
    best_match = re.search(r'\|\s*\*\*Best Lap\*\*\s*\|\s*([\d\.]+)', content)
    if best_match:
        stats['best'] = float(best_match.group(1))
        
    # Extract Sigma
    sigma_match = re.search(r'\|\s*\*\*Consistency \(σ\)\*\*\s*\|\s*([\d\.]+)', content)
    if sigma_match:
        stats['sigma'] = float(sigma_match.group(1))
        
    return stats


def create_event_page(
    event_num: int,
    week: str,
    info: dict,
    events_dir: Path,
    telemetry_stats: dict | None = None
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

## Lap Times

![Lap Progression](../images/event-{{event_num_pad}}-laptimes.png)

{{#if telemetry}}
## Telemetry Analysis

![Telemetry](../images/event-{{event_num_pad}}-telemetry.png)

### Pedal Usage

- Full throttle: {{throttle_pct}}%
- Braking: {{brake_pct}}%
- Coasting: {{coast_pct}}%
{{/if}}

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
    content = content.replace('{{event_num_pad}}', f"{event_num:02d}")
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
    if telemetry_stats:
        content = content.replace('{{#if telemetry}}', '')
        content = content.replace('{{/if}}', '')
        content = content.replace('{{throttle_pct}}', f"{telemetry_stats['throttle_pct']:.1f}")
        content = content.replace('{{brake_pct}}', f"{telemetry_stats['brake_pct']:.1f}")
        content = content.replace('{{coast_pct}}', f"{telemetry_stats['coast_pct']:.1f}")
    else:
        # Remove telemetry section
        content = re.sub(r'\{\{#if telemetry\}\}.*?\{\{/if\}\}', '', content, flags=re.DOTALL)
    
    # Cleanup other placeholders if present (simple regex)
    content = re.sub(r'\{\{.*?\}\}', '', content)

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
    
    # Preserve existing content
    if readme_path.exists():
        content = readme_path.read_text()
        
        # 1. Preserve Notes from existing table
        for e in events:
             # Look for | N | ... | ... | ... | ... | ... | NOTES | ... |
             row_match = re.search(r'\|\s*' + str(e['num']) + r'\s*\|.*?\|.*?\|.*?\|.*?\|.*?\|\s*(.*?)\s*\|', content)
             if row_match:
                 e['notes'] = row_match.group(1).strip()
                 # Rebuild the row with preserved notes
                 table_rows[events.index(e)] = (
                    f"| {e['num']} | {e['date']} | {e['type']} | {e['laps']} | "
                    f"{e['best']:.3f}s | {e['sigma']:.2f}s | {e['notes']} | [→](events/{e['filename']}) |"
                 )
        events_table = '\n'.join(table_rows)
        
        # 2. Update the Events table in place
        # We look for the table block:
        # | # | ...
        # |---| ...
        # ... rows ...
        # (until blank line or next header)
        
        # Regex to find the table start
        table_start_match = re.search(r'\|\s*#\s*\|\s*Date', content)
        
        if table_start_match:
            # We found a table. Now we need to replace it.
            # Strategy: Split content into [Pre-Table] [Table] [Post-Table]
            # Table usually ends at double newline or next section
            
            start_idx = table_start_match.start()
            
            # Find the end of the table (look for a line that doesn't start with |)
            lines = content[start_idx:].split('\n')
            end_offset = 0
            for i, line in enumerate(lines):
                if i > 1 and not line.strip().startswith('|'): # i>1 to skip header and separator
                    break
                end_offset += len(line) + 1 # +1 for newline
            
            pre_table = content[:start_idx]
            post_table = content[start_idx + end_offset:]
            
            # Build new table
            new_table_header = "| # | Date | Type | Laps | Best | σ | Notes | Details |\n|---|------|------|------|------|---|-------|---------|"
            new_table = f"{new_table_header}\n{events_table}"
            
            content = f"{pre_table}{new_table}{post_table}"
            
        else:
            # No table found? Append it after ## Events?
            if "## Events" in content:
                content = content.replace("## Events", f"## Events\n\n| # | Date | Type | Laps | Best | σ | Notes | Details |\n|---|------|------|------|------|---|-------|---------|\n{events_table}")
            else:
                # Append to end
                content += f"\n\n## Events\n\n| # | Date | Type | Laps | Best | σ | Notes | Details |\n|---|------|------|------|------|---|-------|---------|\n{events_table}"

    else:
        # Create new file (fallback) - this shouldn't happen for existing weeks if workflow followed
        intent = "Write your intent here..."
        reflection = """- Track craft takeaways: ...
- Brake bias learnings: ...
- Driver mindset notes: ..."""
        
        # Summary stats
        summary = "_No events yet._"
        if events:
            valid_events = [e for e in events if isinstance(e['best'], (int, float)) and e['best'] > 0]
            if valid_events:
                best_lap = min(e['best'] for e in valid_events)
                first_lap = valid_events[0]['best']
                last_sigma = valid_events[-1]['sigma']
                improvement = first_lap - best_lap
                summary = f"""- **Events:** {len(events)}
- **Best Lap:** {best_lap:.3f}s
- **Improvement:** {improvement:+.3f}s (from {first_lap:.3f}s)
- **Latest σ:** {last_sigma:.2f}s"""

        content = f"""---
week: {week}
---

# Week {week}

## Events

| # | Date | Type | Laps | Best | σ | Notes | Details |
|---|------|------|------|------|---|-------|---------|
{events_table}

## Summary

{summary}

## Reflection

{reflection}
"""
    
    # 3. Update Summary section if it exists
    if events:
        valid_events = [e for e in events if isinstance(e['best'], (int, float)) and e['best'] > 0]
        if valid_events:
            best_lap = min(e['best'] for e in valid_events)
            first_lap = valid_events[0]['best']
            last_sigma = valid_events[-1]['sigma']
            improvement = first_lap - best_lap
            
            new_summary = f"""- **Events:** {len(events)}
- **Best Lap:** {best_lap:.3f}s
- **Improvement:** {improvement:+.3f}s (from {first_lap:.3f}s)
- **Latest σ:** {last_sigma:.2f}s"""
            
            # Replace existing summary block
            # Look for ## Summary followed by content until next ## or EOF
            summary_pattern = r'(## Summary\n\n)([\s\S]*?)(?=\n## |\Z)'
            if re.search(summary_pattern, content):
                content = re.sub(summary_pattern, f"\\1{new_summary}\n", content)
            else:
                # Add if missing
                pass # If it's missing, we leave it. The user might have deleted it.

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
    else:
        # If file exists, we still want to process it, maybe it was updated
        pass
    
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
    telemetry_stats = None
    if args.telemetry and args.telemetry.exists():
        print(f"   Processing telemetry...")
        # Copy telemetry
        telem_dest = data_dir / args.telemetry.name
        if not telem_dest.exists():
            shutil.copy(args.telemetry, telem_dest)
        
        if not args.no_viz:
            # Generate telemetry visualization
            telem_viz_path = images_dir / f"event-{event_num:02d}-telemetry.png"
            telem_df = load_telemetry(args.telemetry)
            
            # Calculate stats for the template
            throttle_threshold = 0.05
            brake_threshold = 0.01
            full_throttle_pct = (telem_df['Throttle'] > 0.95).sum() / len(telem_df) * 100
            braking_pct = (telem_df['Brake'] > brake_threshold).sum() / len(telem_df) * 100
            coasting_pct = ((telem_df['Throttle'] < throttle_threshold) & (telem_df['Brake'] < brake_threshold)).sum() / len(telem_df) * 100
            
            telemetry_stats = {
                'throttle_pct': full_throttle_pct,
                'brake_pct': braking_pct,
                'coast_pct': coasting_pct
            }
            
            create_telemetry_visualization(
                telem_df, 
                title=f"Event #{event_num} Telemetry – Best Lap: {info['best']:.3f}s", 
                output_path=telem_viz_path
            )

    
    # Create event page
    print(f"   Creating event page...")
    event_path = create_event_page(event_num, args.week, info, events_dir, telemetry_stats)
    info['filename'] = event_path.name
    
    # Load all events for week README
    all_events = []
    for event_file in sorted(events_dir.glob("*.md")):
        match = re.match(r'(\d+)-(\d{4}-\d{2}-\d{2})-(.+)\.md', event_file.name)
        if match:
            num, date, type_slug = match.groups()
            num = int(num)
            
            # Get stats
            if num == event_num:
                # Use current info
                laps = info['laps']
                best = info['best']
                sigma = info['sigma']
            else:
                # Parse from file
                stats = parse_event_stats(event_file)
                laps = stats.get('laps', '?')
                best = stats.get('best', 0.0)
                sigma = stats.get('sigma', 0.0)

            all_events.append({
                'num': num,
                'date': date,
                'type': type_slug.replace('-', ' '),
                'laps': laps,
                'best': best,
                'sigma': sigma,
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
