"""Filtering utilities for lap-time analysis."""

import pandas as pd

from core.models import FilterMetadata


def apply_tukey_filter(
    df: pd.DataFrame, column: str = "Lap time"
) -> tuple[pd.DataFrame, FilterMetadata]:
    """Filter outlier laps using Tukey (IQR) bounds."""
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

    filter_applied = True
    if filtered_df.empty:
        filtered_df = df.copy()
        removed_df = df.iloc[0:0]
        filter_applied = False

    metadata: FilterMetadata = {
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
