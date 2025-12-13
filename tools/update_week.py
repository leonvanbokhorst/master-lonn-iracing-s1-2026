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
from visualize_week import load_week_sessions, create_week_visualization


def format_session_row(session_num: int, df: pd.DataFrame, info: dict) -> str:
    """Format a single session as a markdown table row."""
    date_str = info['start_time'].strftime('%Y%m%d')
    session_type = 'ai' if info['type'] == 'Race' else 'solo'
    
    # Determine focus based on session characteristics
    if info['settled_std'] < 0.5:
        focus = "race consistency"
    elif info['settled_std'] < 1.5:
        focus = "band consolidation"
    elif session_num == 1:
        focus = "baseline exploration"
    else:
        focus = "consistency building"
    
    # Build notes
    notes_parts = []
    notes_parts.append(f"{info['laps']} laps")
    notes_parts.append(f"best **{info['best']:.3f}**")
    
    if 'optimal' in info:
        notes_parts.append(f"optimal {info['optimal']:.3f}")
    
    # Add band info
    notes_parts.append(f"σ={info['settled_std']:.2f}s")
    
    # Clean lap percentage
    if info['clean_pct'] < 100:
        notes_parts.append(f"{info['clean_pct']:.0f}% clean")
    
    notes = ", ".join(notes_parts)
    
    return f"| {date_str} | {session_type} | {focus} | {notes} |"


def generate_sessions_table(sessions: list[tuple[pd.DataFrame, dict]]) -> str:
    """Generate the full preparation sessions markdown table."""
    lines = [
        "| date     | session | focus                | notes |",
        "| -------- | ------- | -------------------- | ----- |",
    ]
    
    for i, (df, info) in enumerate(sessions):
        lines.append(format_session_row(i + 1, df, info))
    
    return "\n".join(lines)


def generate_progress_summary(sessions: list[tuple[pd.DataFrame, dict]]) -> str:
    """Generate the longitudinal progress summary markdown section."""
    
    if len(sessions) < 2:
        return ""
    
    lines = [
        "### Week Progress Summary",
        "",
        "![Week Progress](../images/week01/week-progress.png)",
        "",
        "| #   | Date        | Type     | Laps | Best    | Settled | σ     |",
        "| --- | ----------- | -------- | ---- | ------- | ------- | ----- |",
    ]
    
    for i, (df, info) in enumerate(sessions):
        date_str = info['start_time'].strftime('%m/%d %H:%M')
        type_str = "AI" if info['type'] == 'Race' else "Practice"
        lines.append(
            f"| {i+1}   | {date_str} | {type_str:<8} | {info['laps']:<4} | "
            f"{info['best']:.3f}s | {info['settled_mean']:.3f}s | {info['settled_std']:.2f}s |"
        )
    
    # Add improvement summary
    first = sessions[0][1]
    last = sessions[-1][1]
    
    best_improvement = first['best'] - last['best']
    std_improvement = first['settled_std'] - last['settled_std']
    
    lines.extend([
        "",
        "**Progress:**",
        "",
        f"- Best lap: {first['best']:.3f}s → {last['best']:.3f}s ({best_improvement:+.3f}s)",
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
    
    # Load sessions
    print(f"Loading sessions from {week_dir}...")
    sessions = load_week_sessions(week_dir)
    print(f"Found {len(sessions)} sessions")
    
    if len(sessions) == 0:
        print("❌ No valid sessions found!")
        return
    
    # Generate visualization
    week_name = week_dir.name
    images_dir = week_dir.parent.parent / "images" / week_name
    images_dir.mkdir(parents=True, exist_ok=True)
    output_image = images_dir / "week-progress.png"
    
    n_sessions = len(sessions)
    first_date = sessions[0][1]['start_time'].strftime('%Y-%m-%d')
    last_date = sessions[-1][1]['start_time'].strftime('%Y-%m-%d')
    title = f"{week_name.upper()} Progress – {n_sessions} Sessions\n{first_date} → {last_date}"
    
    print(f"Generating visualization...")
    create_week_visualization(sessions, title=title, output_path=output_image)
    
    # Read existing week file
    if not week_file.exists():
        print(f"❌ Week file not found: {week_file}")
        return
    
    content = week_file.read_text()
    
    # Generate new sections
    sessions_table = generate_sessions_table(sessions)
    progress_summary = generate_progress_summary(sessions)
    
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
    print(f"Sessions: {len(sessions)}")
    print(f"Best lap: {min(info['best'] for _, info in sessions):.3f}s")
    print(f"Latest σ: {sessions[-1][1]['settled_std']:.2f}s")


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

