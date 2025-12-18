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
import sys
from pathlib import Path
import pandas as pd
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import EventInfo, FilterMetadata, TelemetryStats, WeekEventEntry
from data import apply_tukey_filter, extract_event_info, load_event_csv
from tools.io.markdown import create_event_page, parse_event_stats, update_week_readme

# Import our visualization tools
from visualize_event import create_event_visualization
from visualize_week import load_week_events, create_week_visualization
from visualize_telemetry import load_telemetry, create_telemetry_visualization
from config import pedals


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


def format_filter_summary(metadata: FilterMetadata | None) -> tuple[str, str | None]:
    """Return human-readable summary + note for Tukey filtering."""
    if not metadata:
        return "", None

    lower = metadata.get("lower_bound")
    upper = metadata.get("upper_bound")
    median = metadata.get("median")
    removed = metadata.get("removed_count", 0)
    total = metadata.get("total_count", 0)
    kept = metadata.get("kept_count", 0)
    if lower is None or upper is None or median is None:
        return "", None

    summary = (
        f"> Tukey filter applied: kept {kept}/{total} laps "
        f"(median {median:.3f}s, bounds {lower:.3f}s–{upper:.3f}s, "
        f"removed {removed}).\n"
    )
    note = (
        f"Tukey filter {lower:.3f}s–{upper:.3f}s "
        f"(median {median:.3f}s, removed {removed})"
    )
    return summary, note


 


def compute_telemetry_stats(telem_df: pd.DataFrame) -> TelemetryStats:
    """Compute basic telemetry stats (pedal usage)."""
    pedals_cfg = pedals()
    throttle_threshold = pedals_cfg.throttle_on
    brake_inactive_threshold = pedals_cfg.brake_on
    coast_accel_threshold = pedals_cfg.coast_long_accel

    throttle = telem_df["Throttle"]
    brake = telem_df["Brake"]

    full_throttle_pct = (throttle > pedals_cfg.throttle_full).sum() / len(throttle) * 100
    braking_pct = (brake > brake_inactive_threshold).sum() / len(brake) * 100

    coast_mask = (throttle < throttle_threshold) & (brake < brake_inactive_threshold)
    if "LongAccel" in telem_df.columns:
        coast_mask &= telem_df["LongAccel"].abs() < coast_accel_threshold

    coasting_pct = coast_mask.sum() / len(telem_df) * 100
    return {
        "throttle_pct": full_throttle_pct,
        "brake_pct": braking_pct,
        "coast_pct": coasting_pct,
    }


def main():
    parser = argparse.ArgumentParser(description="Add event to week structure")
    parser.add_argument("week", type=str, help="Week number (e.g., 01)")
    parser.add_argument("csv_file", type=Path, help="Path to Garage61 CSV export")
    parser.add_argument("--telemetry", "-t", type=Path, help="Optional single-lap telemetry CSV")
    parser.add_argument("--no-viz", action="store_true", help="Skip visualization generation")
    parser.add_argument(
        "--tukey-filter",
        action="store_true",
        help="Drop lap-time outliers using Tukey (IQR) bounds before analysis",
    )
    parser.add_argument(
        "--garage-event-id",
        "-g",
        type=str,
        help="Garage 61 event ID for backlinking the session page",
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.csv_file.exists():
        print(f"❌ CSV file not found: {args.csv_file}")
        return 1
    
    # Setup paths - everything lives under weeks/weekXX/
    project_root = Path(__file__).parent.parent
    week_dir = project_root / "weeks" / f"week{args.week}"
    data_dir = week_dir / "data" / "processed"
    images_dir = week_dir / "images"
    events_dir = week_dir / "events"
    
    # Create directories
    data_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Adding event to week {args.week}...")
    
    dest_csv = data_dir / args.csv_file.name
    
    print(f"   Analyzing event data...")
    df = load_event_csv(args.csv_file)
    filter_metadata: FilterMetadata | None = None
    if args.tukey_filter:
        df, filter_metadata = apply_tukey_filter(df)
    
    # Persist the processed (possibly filtered) data for downstream tools
    df.to_csv(dest_csv, index=False)
    print(f"   Saved processed CSV to data/{dest_csv.name}")
    info = extract_event_info(df, args.csv_file)
    if args.garage_event_id:
        info["garage_event_id"] = args.garage_event_id
    
    # Determine event number
    event_num = get_next_event_number(events_dir)
    info['num'] = event_num
    
    print(f"   Event #{event_num}: {info['laps']} laps, best {info['best']:.3f}s")
    
    # Format filter summary for downstream consumers
    filter_summary, filter_note = format_filter_summary(filter_metadata)
    info["filter_summary"] = filter_summary
    if filter_note:
        info["notes"] = filter_note

    # Generate event visualization
    if not args.no_viz:
        print(f"   Generating event visualization...")
        event_viz_path = images_dir / f"event-{event_num:02d}-laptimes.png"
        create_event_visualization(df, title=f"Event #{event_num} – {info['date']}", 
                                   output_path=event_viz_path,
                                   filter_metadata=filter_metadata)
    
    # Handle telemetry if provided
    telemetry_stats: TelemetryStats | None = None
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
            
            # Calculate stats for the template using helper
            telemetry_stats = compute_telemetry_stats(telem_df)
            
            create_telemetry_visualization(
                telem_df, 
                title=f"Event #{event_num} Telemetry – Best Lap: {info['best']:.3f}s", 
                output_path=telem_viz_path
            )

    
    # Create event page
    print(f"   Creating event page...")
    info["filter_metadata"] = filter_metadata
    event_path = create_event_page(event_num, args.week, info, events_dir, telemetry_stats)
    info['filename'] = event_path.name
    
    # Load all events for week README
    all_events: list[WeekEventEntry] = []
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
                # Parse from file using new helper
                stats = parse_event_stats(event_file)
                laps = stats.get('laps', '?')
                best = stats.get('best', 0.0)
                sigma = stats.get('sigma', 0.0)

            entry: WeekEventEntry = {
                'num': num,
                'date': date,
                'type': type_slug.replace('-', ' '),
                'laps': laps,
                'best': best,
                'sigma': sigma,
                'filename': event_file.name,
            }
            if num == event_num and info.get("notes"):
                entry["notes"] = info["notes"]
            all_events.append(entry)
    
    # Re-sort by number
    all_events.sort(key=lambda x: x['num'])
    
    # Update week README
    print(f"   Updating week README...")
    update_week_readme(args.week, week_dir.parent, all_events)
    
    # Regenerate week visualization
    if not args.no_viz:
        print(f"   Regenerating week visualization...")
        # Point to the processed data directory
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
