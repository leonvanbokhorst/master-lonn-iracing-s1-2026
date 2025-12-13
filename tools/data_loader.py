#!/usr/bin/env python3
"""
Shared data loading utilities for Garage 61 CSV exports.
Centralized to avoid drift between visualization scripts.
"""

from pathlib import Path
import pandas as pd


def load_event_csv(
    csv_path: Path,
    min_lap_time: float = 48.0,
    max_lap_time: float = 90.0,
    exclude_first_lap: bool = True,
) -> pd.DataFrame:
    """Load and clean a Garage 61 CSV export.

    Args:
        csv_path: Path to CSV file
        min_lap_time: Minimum valid lap time (filters incomplete laps)
        max_lap_time: Maximum valid lap time (filters pit/reset laps)
        exclude_first_lap: Exclude lap 1 (standing start, always slow).
                          Set False for rolling start sessions.
    """
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # Filter out incomplete laps, outliers, and optionally first lap (standing start)
    min_lap = 1 if exclude_first_lap else 0
    df = df[df["Lap"] > min_lap].copy()
    df = df[(df["Lap time"] >= min_lap_time) & (df["Lap time"] <= max_lap_time)].copy()

    # Parse timestamp
    if "Started at" in df.columns:
        df["timestamp"] = pd.to_datetime(df["Started at"])

    # Convert sector times to float, handling any issues
    for sector in ["Sector 1", "Sector 2", "Sector 3"]:
        if sector in df.columns:
            df[sector] = pd.to_numeric(df[sector], errors="coerce")

    return df


def load_event_csv_with_metadata(
    csv_path: Path,
    min_lap_time: float = 48.0,
    max_lap_time: float = 90.0,
    exclude_first_lap: bool = True,
) -> pd.DataFrame:
    """Load event CSV with additional metadata columns for week visualization.

    Same as load_event_csv but adds event_start and source_file columns.
    """
    df = load_event_csv(csv_path, min_lap_time, max_lap_time, exclude_first_lap)

    # Get session start time
    if "timestamp" in df.columns:
        df["event_start"] = df["timestamp"].min()

    # Add source file
    df["source_file"] = csv_path.name

    return df

