#!/usr/bin/env python3
"""
Event Analysis Utility
Returns JSON analysis of event data for Cursor to use in adaptive coaching.

Usage:
    python tools/analyze_event.py path/to/event.csv
    python tools/analyze_event.py path/to/event.csv --fastest-lap path/to/fastest.csv
    python tools/analyze_event.py path/to/event.csv --json  # Pretty JSON output
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import load_event_csv


def detect_event_type(csv_path: Path) -> str:
    """Detect event type from filename."""
    name = csv_path.name.lower()
    if "race" in name and "ai" not in name and "offline" not in name:
        return "race"
    elif "time trial" in name or "tt" in name:
        return "time_trial"
    elif "qualifying" in name or "qual" in name:
        return "qualifying"
    else:
        return "solo"


def analyze_consistency(lap_times: np.ndarray) -> dict:
    """Analyze lap time consistency."""
    if len(lap_times) < 3:
        return {
            "sigma": float(np.std(lap_times)),
            "variance_level": "insufficient_data",
            "coefficient_of_variation": 0.0,
        }
    
    sigma = float(np.std(lap_times))
    mean_time = float(np.mean(lap_times))
    cv = (sigma / mean_time) * 100  # Coefficient of variation as percentage
    
    # Classify variance level
    if sigma < 0.5:
        level = "excellent"
    elif sigma < 1.0:
        level = "good"
    elif sigma < 2.0:
        level = "moderate"
    else:
        level = "high"
    
    return {
        "sigma": sigma,
        "variance_level": level,
        "coefficient_of_variation": cv,
        "mean": mean_time,
        "median": float(np.median(lap_times)),
        "range": float(np.max(lap_times) - np.min(lap_times)),
    }


def analyze_sectors(df: pd.DataFrame) -> dict:
    """Analyze sector performance."""
    sector_cols = [col for col in df.columns if col.lower().startswith("sector ")]
    
    if not sector_cols:
        return {}
    
    sectors = {}
    for col in sector_cols:
        sector_times = df[col].dropna()
        if len(sector_times) == 0:
            continue
        
        best = float(sector_times.min())
        avg = float(sector_times.mean())
        worst = float(sector_times.max())
        total_loss = float(np.sum(sector_times - best))
        
        sectors[col] = {
            "best": best,
            "average": avg,
            "worst": worst,
            "loss_per_lap": avg - best,
            "total_loss": total_loss,
            "consistency_sigma": float(np.std(sector_times)),
        }
    
    return sectors


def analyze_pace_trend(lap_times: np.ndarray, laps: np.ndarray) -> dict:
    """Analyze pace trend over the session."""
    if len(lap_times) < 5:
        return {"trend": "insufficient_data"}
    
    # Split into thirds
    n = len(lap_times)
    early = lap_times[:n//3]
    middle = lap_times[n//3:2*n//3]
    late = lap_times[2*n//3:]
    
    early_avg = float(np.mean(early))
    middle_avg = float(np.mean(middle))
    late_avg = float(np.mean(late))
    
    # Determine trend
    if late_avg < early_avg - 0.5:
        trend = "improving"
    elif late_avg > early_avg + 0.5:
        trend = "declining"
    else:
        trend = "stable"
    
    # Phase consistency
    phase_consistency = {
        "early_sigma": float(np.std(early)),
        "middle_sigma": float(np.std(middle)),
        "late_sigma": float(np.std(late)),
    }
    
    return {
        "trend": trend,
        "early_avg": early_avg,
        "middle_avg": middle_avg,
        "late_avg": late_avg,
        "improvement": early_avg - late_avg,
        "phase_consistency": phase_consistency,
    }


def compare_with_fastest(df: pd.DataFrame, fastest_df: pd.DataFrame) -> dict:
    """Compare event with fastest lap telemetry."""
    # Get best lap from event
    best_lap_idx = df["Lap time"].idxmin()
    best_lap_time = float(df.loc[best_lap_idx, "Lap time"])
    
    # Get fastest lap time (assuming single lap in telemetry file)
    if "Lap time" in fastest_df.columns:
        fastest_time = float(fastest_df["Lap time"].iloc[0])
    else:
        # Try to calculate from sectors
        sector_cols = [col for col in fastest_df.columns if col.lower().startswith("sector ")]
        if sector_cols:
            fastest_time = float(fastest_df[sector_cols].iloc[0].sum())
        else:
            return {"available": False}
    
    delta = best_lap_time - fastest_time
    
    # Sector comparison
    sector_deltas = []
    sector_cols = [col for col in df.columns if col.lower().startswith("sector ")]
    if sector_cols and all(col in fastest_df.columns for col in sector_cols):
        for col in sector_cols:
            event_sector = float(df.loc[best_lap_idx, col])
            fastest_sector = float(fastest_df[col].iloc[0])
            sector_deltas.append({
                "sector": col,
                "delta": event_sector - fastest_sector,
                "event_time": event_sector,
                "fastest_time": fastest_sector,
            })
    
    return {
        "available": True,
        "delta": delta,
        "best_lap_time": best_lap_time,
        "fastest_lap_time": fastest_time,
        "sector_deltas": sector_deltas,
    }


def analyze_event(csv_path: Path, fastest_lap_path: Path | None = None) -> dict:
    """Main analysis function that returns comprehensive event analysis."""
    
    # Load data
    df = load_event_csv(csv_path, exclude_first_lap=True)
    
    if df.empty:
        return {"error": "No valid laps found in CSV"}
    
    # Basic metrics
    laps = df["Lap"].values
    lap_times = df["Lap time"].values
    clean = df["Clean"].values if "Clean" in df.columns else np.ones(len(laps))
    
    best_lap_idx = np.argmin(lap_times)
    best_lap = int(laps[best_lap_idx])
    best_time = float(lap_times[best_lap_idx])
    
    clean_laps = np.sum(clean == 1)
    dirty_laps = np.sum(clean == 0)
    clean_pct = (clean_laps / len(laps)) * 100
    
    # Detect event type
    event_type = detect_event_type(csv_path)
    
    # Consistency analysis
    consistency = analyze_consistency(lap_times)
    
    # Sector analysis
    sectors = analyze_sectors(df)
    
    # Pace trend
    pace_trend = analyze_pace_trend(lap_times, laps)
    
    # Comparison with fastest lap
    comparison = {"available": False}
    if fastest_lap_path and fastest_lap_path.exists():
        fastest_df = load_event_csv(fastest_lap_path, exclude_first_lap=False)
        if not fastest_df.empty:
            comparison = compare_with_fastest(df, fastest_df)
    
    # Calculate theoretical optimal (best sectors)
    theoretical_optimal = None
    if sectors:
        optimal_time = sum(s["best"] for s in sectors.values())
        theoretical_optimal = {
            "time": optimal_time,
            "delta_to_best": optimal_time - best_time,
        }
    
    # Build analysis result
    analysis = {
        "file": csv_path.name,
        "event_type": event_type,
        "laps": {
            "total": int(len(laps)),
            "clean": int(clean_laps),
            "dirty": int(dirty_laps),
            "clean_percentage": clean_pct,
        },
        "best_lap": {
            "lap_number": best_lap,
            "time": best_time,
        },
        "consistency": consistency,
        "sectors": sectors,
        "pace_trend": pace_trend,
        "theoretical_optimal": theoretical_optimal,
        "comparison_to_fastest": comparison,
    }
    
    # Add incidents if available
    if "Incidents" in df.columns:
        total_incidents = int(df["Incidents"].sum())
        analysis["incidents"] = total_incidents
    
    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Analyze iRacing event data and return JSON for Cursor coaching"
    )
    parser.add_argument("csv_file", type=Path, help="Path to event CSV file")
    parser.add_argument(
        "--fastest-lap",
        type=Path,
        help="Path to fastest lap telemetry CSV for comparison",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output pretty-printed JSON (default is compact)",
    )
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(json.dumps({"error": f"File not found: {args.csv_file}"}))
        sys.exit(1)
    
    analysis = analyze_event(args.csv_file, args.fastest_lap)
    
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(json.dumps(analysis))


if __name__ == "__main__":
    main()
