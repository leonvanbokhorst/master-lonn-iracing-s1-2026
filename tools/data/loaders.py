"""CSV loading helpers for Garage 61 exports."""

from pathlib import Path

import pandas as pd


def load_event_csv(
    csv_path: Path,
    min_lap_time: float = 48.0,
    max_lap_time: float = 120.0,
    exclude_first_lap: bool = True,
) -> pd.DataFrame:
    """Load and clean a Garage 61 CSV export."""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # Filter out incomplete laps, outliers, and optionally first lap (standing start)
    min_lap = 1 if exclude_first_lap else 0
    df = df[df["Lap"] > min_lap].copy()
    df = df[(df["Lap time"] >= min_lap_time) & (df["Lap time"] <= max_lap_time)].copy()

    # Parse timestamp
    if "Started at" in df.columns:
        df["timestamp"] = pd.to_datetime(df["Started at"])

    # Convert sector times (Sector 1 ... Sector N) to float
    sector_cols = [col for col in df.columns if col.lower().startswith("sector ")]
    for sector in sector_cols:
        df[sector] = pd.to_numeric(df[sector], errors="coerce")

    return df


def load_event_csv_with_metadata(
    csv_path: Path,
    min_lap_time: float = 48.0,
    max_lap_time: float = 120.0,
    exclude_first_lap: bool = True,
) -> pd.DataFrame:
    """Load event CSV with additional metadata columns for week visualization."""
    df = load_event_csv(csv_path, min_lap_time, max_lap_time, exclude_first_lap)

    # Get session start time
    if "timestamp" in df.columns:
        df["event_start"] = df["timestamp"].min()

    # Add source file
    df["source_file"] = csv_path.name

    return df
