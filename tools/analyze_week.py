#!/usr/bin/env python3
"""
Week Context Analysis Utility
Returns JSON with week-level context for Cursor coaching decisions.

Usage:
    python tools/analyze_week.py weeks/week02
    python tools/analyze_week.py weeks/week02 --json  # Pretty JSON
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from data_loader import load_event_csv


def load_week_metadata(week_path: Path) -> dict:
    """Load week metadata from README frontmatter."""
    readme_path = week_path / "README.md"
    
    if not readme_path.exists():
        return {}
    
    content = readme_path.read_text()
    
    # Extract YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
                return metadata or {}
            except yaml.YAMLError:
                pass
    
    return {}


def analyze_week(week_path: Path) -> dict:
    """Analyze all events in a week and return context."""
    
    if not week_path.exists():
        return {"error": f"Week directory not found: {week_path}"}
    
    # Load metadata
    metadata = load_week_metadata(week_path)
    
    week_number = metadata.get("week", week_path.name.replace("week", "").replace("0", ""))
    track = metadata.get("track", "Unknown")
    
    # Find all event CSVs in processed data
    data_path = week_path / "data" / "processed"
    
    if not data_path.exists():
        data_path = week_path / "data"
    
    if not data_path.exists():
        return {
            "week": week_number,
            "track": track,
            "events": 0,
            "error": "No data directory found",
        }
    
    # Load all event CSVs
    csv_files = sorted(data_path.glob("*.csv"))
    
    # Filter out telemetry files (contain lap ID in filename)
    event_csvs = [
        f for f in csv_files 
        if "export" in f.name.lower() and "01K" not in f.name
    ]
    
    if not event_csvs:
        return {
            "week": week_number,
            "track": track,
            "events": 0,
            "best_lap": None,
            "improvement": 0.0,
        }
    
    # Analyze each event
    events = []
    all_best_laps = []
    
    for csv_file in event_csvs:
        try:
            df = load_event_csv(csv_file, exclude_first_lap=True)
            if df.empty:
                continue
            
            lap_times = df["Lap time"].values
            best_lap = float(np.min(lap_times))
            sigma = float(np.std(lap_times))
            
            all_best_laps.append(best_lap)
            
            events.append({
                "file": csv_file.name,
                "laps": len(lap_times),
                "best_lap": best_lap,
                "sigma": sigma,
            })
        except Exception as e:
            continue
    
    if not events:
        return {
            "week": week_number,
            "track": track,
            "events": 0,
            "error": "No valid event data found",
        }
    
    # Calculate week statistics
    best_lap_overall = float(np.min(all_best_laps))
    first_event_best = events[0]["best_lap"]
    improvement = first_event_best - best_lap_overall
    
    avg_consistency = float(np.mean([e["sigma"] for e in events]))
    total_laps = sum(e["laps"] for e in events)
    
    return {
        "week": week_number,
        "track": track,
        "events": len(events),
        "total_laps": total_laps,
        "best_lap": best_lap_overall,
        "first_event_best": first_event_best,
        "improvement": improvement,
        "avg_consistency": avg_consistency,
        "event_details": events,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze week context for Cursor coaching"
    )
    parser.add_argument("week_path", type=Path, help="Path to week directory (e.g., weeks/week02)")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output pretty-printed JSON (default is compact)",
    )
    
    args = parser.parse_args()
    
    if not args.week_path.exists():
        print(json.dumps({"error": f"Week directory not found: {args.week_path}"}))
        sys.exit(1)
    
    analysis = analyze_week(args.week_path)
    
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(json.dumps(analysis))


if __name__ == "__main__":
    main()
