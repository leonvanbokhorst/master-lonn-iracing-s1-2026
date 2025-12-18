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
    max_lap_time: float = 120.0,
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


def apply_tukey_filter(
    df: pd.DataFrame, column: str = "Lap time"
) -> tuple[pd.DataFrame, dict[str, float | int | list]]:
    """Filter outlier laps using Tukey (IQR) bounds.

    Returns the filtered dataframe along with metadata describing the bounds.
    """
    if column not in df.columns or df.empty:
        return df.copy(), {
            "applied": False,
            "total_count": len(df),
            "kept_count": len(df),
            "removed_count": 0,
            "removed_laps": [],
        }

    series = df[column].dropna()
    if series.empty:
        return df.copy(), {
            "applied": False,
            "total_count": len(df),
            "kept_count": len(df),
            "removed_count": 0,
            "removed_laps": [],
        }

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    median = series.median()
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    in_bounds = (df[column] >= lower_bound) & (df[column] <= upper_bound)
    filtered_df = df[in_bounds].copy()
    removed_df = df[~in_bounds].copy()

    # Guard against over-filtering (e.g., identical lap times)
    filter_applied = True
    if filtered_df.empty:
        filtered_df = df.copy()
        removed_df = df.iloc[0:0]
        filter_applied = False

    metadata: dict[str, float | int | list] = {
        "applied": filter_applied,
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "lower_bound": float(lower_bound) if filter_applied else None,
        "upper_bound": float(upper_bound) if filter_applied else None,
        "total_count": int(len(df)),
        "kept_count": int(len(filtered_df)),
        "removed_count": int(len(removed_df)),
        "removed_laps": removed_df["Lap"].tolist() if "Lap" in removed_df.columns else [],
    }

    return filtered_df, metadata

