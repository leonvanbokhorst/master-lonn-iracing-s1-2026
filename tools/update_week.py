#!/usr/bin/env python3
"""
Week File Updater
Reads Garage 61 CSV exports and updates the week markdown file.

Usage:
    uv run python tools/update_week.py results/week01/ weeks/week01-summit-point-raceway.md
    
This will:
1. Generate/update the preparation sessions table
2. Create the week progress visualization
3. Add a longitudinal summary section
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Import from our other tools
from visualize_week import load_week_events, create_week_visualization
from data_loader import format_lap_time


def format_event_row(event_num: int, df: pd.DataFrame, info: dict) -> str:
    """Format a single event as a markdown table row."""
    date_str = info['start_time'].strftime('%Y%m%d')
    event_type = 'ai' if info['type'] == 'Race' else 'solo'
    
    # Determine focus based on event characteristics
    if info['settled_std'] < 0.5:
        focus = "race consistency"
    elif info['settled_std'] < 1.5:
        focus = "band consolidation"
    elif event_num == 1:
        focus = "baseline exploration"
    else:
        focus = "consistency building"
    
    # Build notes
    notes_parts = []
    notes_parts.append(f"{info['laps']} laps")
    notes_parts.append(f"best **{format_lap_time(info['best'])}**")
    
    if 'optimal' in info:
        notes_parts.append(f"optimal {format_lap_time(info['optimal'])}")
    
    # Add band info
    notes_parts.append(f"σ={info['settled_std']:.2f}s")
    
    # Clean lap percentage
    if info['clean_pct'] < 100:
        notes_parts.append(f"{info['clean_pct']:.0f}% clean")
    
    notes = ", ".join(notes_parts)
    
    return f"| {date_str} | {event_type} | {focus} | {notes} |"


def generate_events_table(events: list[tuple[pd.DataFrame, dict]]) -> str:
    """Generate the full preparation events markdown table."""
    lines = [
        "| date     | event   | focus                | notes |",
        "| -------- | ------- | -------------------- | ----- |",
    ]
    
    for i, (df, info) in enumerate(events):
        lines.append(format_event_row(i + 1, df, info))
    
    return "\n".join(lines)


def generate_progress_summary(events: list[tuple[pd.DataFrame, dict]]) -> str:
    """Generate the longitudinal progress summary markdown section."""
    
    if len(events) < 2:
        return ""
    
    lines = [
        "### Week Progress Summary",
        "",
        "![Week Progress](../images/week01/week-progress.png)",
        "",
        "| #   | Date        | Type     | Laps | Best    | Settled | σ     |",
        "| --- | ----------- | -------- | ---- | ------- | ------- | ----- |",
    ]
    
    for i, (df, info) in enumerate(events):
        date_str = info['start_time'].strftime('%m/%d %H:%M')
        type_str = "AI" if info['type'] == 'Race' else "Practice"
        best_fmt = format_lap_time(info['best'])
        settled_fmt = format_lap_time(info['settled_mean'])
        lines.append(
            f"| {i+1}   | {date_str} | {type_str:<8} | {info['laps']:<4} | "
            f"{best_fmt} | {settled_fmt} | {info['settled_std']:.2f}s |"
        )
    
    # Add improvement summary
    first = events[0][1]
    last = events[-1][1]
    
    best_improvement = first['best'] - last['best']
    std_improvement = first['settled_std'] - last['settled_std']
    
    first_best_fmt = format_lap_time(first['best'])
    last_best_fmt = format_lap_time(last['best'])
    lines.extend([
        "",
        "**Progress:**",
        "",
        f"- Best lap: {first_best_fmt} → {last_best_fmt} ({best_improvement:+.3f}s)",
        f"- Consistency: σ {first['settled_std']:.2f}s → σ {last['settled_std']:.2f}s ({std_improvement:+.2f}s tighter)",
    ])
    
    # Add sector info if available
    if 'optimal' in last:
        gap = last['best'] - last['optimal']
        lines.append(f"- Gap to optimal: {gap:.3f}s")
    
    lines.append("")
    
    return "\n".join(lines)


def update_week_file(
    week_dir: Path, 
    week_file: Path,
    min_lap_time: float = 48.0,
    max_lap_time: float = 90.0,
) -> None:
    """Update the week markdown file with session data."""
    
    # Load events
    print(f"Loading events from {week_dir}...")
    events = load_week_events(week_dir)
    print(f"Found {len(events)} events")
    
    if len(events) == 0:
        print("❌ No valid events found!")
        return
    
    # Generate visualization - images are in week_dir/../images/
    # week_dir is e.g., weeks/week01/data/ so parent.name gives "week01"
    week_name = week_dir.parent.name
    images_dir = week_dir.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_image = images_dir / "week-progress.png"
    
    n_events = len(events)
    first_date = events[0][1]['start_time'].strftime('%Y-%m-%d')
    last_date = events[-1][1]['start_time'].strftime('%Y-%m-%d')
    title = f"{week_name.upper()} Progress – {n_events} Events\n{first_date} → {last_date}"
    
    print(f"Generating visualization...")
    create_week_visualization(events, title=title, output_path=output_image)
    
    # Read existing week file
    if not week_file.exists():
        print(f"❌ Week file not found: {week_file}")
        return
    
    content = week_file.read_text()
    
    # Generate new sections
    events_table = generate_events_table(events)
    progress_summary = generate_progress_summary(events)
    
    # NOTE: We do NOT auto-update the Preparation Sessions table!
    # That table is human-curated with narrative notes, VRS links, etc.
    # The auto-generated data goes into the Week Progress Summary only.
    
    # Update or add the progress summary
    # Look for existing Week Progress Summary section
    progress_pattern = r'### Week Progress Summary\n.*?(?=\n### |\n## |\Z)'
    
    if re.search(progress_pattern, content, re.DOTALL):
        # Replace existing summary
        content = re.sub(progress_pattern, progress_summary, content, flags=re.DOTALL)
        print("✅ Updated Week Progress Summary")
    else:
        # Add new summary before "## Official Races" or at end
        if "## Official Races" in content:
            content = content.replace(
                "## Official Races",
                progress_summary + "\n---\n\n## Official Races"
            )
            print("✅ Added Week Progress Summary")
        else:
            content += "\n\n---\n\n" + progress_summary
            print("✅ Added Week Progress Summary at end")
    
    # Write updated file
    week_file.write_text(content)
    print(f"✅ Updated {week_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("WEEK UPDATE COMPLETE")
    print("="*60)
    print(f"Events: {len(events)}")
    best_overall = min(info['best'] for _, info in events)
    print(f"Best lap: {format_lap_time(best_overall)}")
    print(f"Latest σ: {events[-1][1]['settled_std']:.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Update week file from Garage 61 CSVs")
    parser.add_argument("week_dir", type=Path, help="Path to week results directory")
    parser.add_argument("week_file", type=Path, help="Path to week markdown file")
    parser.add_argument("--min-lap", type=float, default=48.0, help="Minimum valid lap time")
    parser.add_argument("--max-lap", type=float, default=90.0, help="Maximum valid lap time")
    
    args = parser.parse_args()
    
    update_week_file(
        args.week_dir, 
        args.week_file,
        min_lap_time=args.min_lap,
        max_lap_time=args.max_lap,
    )


if __name__ == "__main__":
    main()

