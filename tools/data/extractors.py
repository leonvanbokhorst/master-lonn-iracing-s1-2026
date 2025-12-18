"""Data extraction helpers for event metadata/stats."""

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.models import EventInfo


def extract_event_info(df: pd.DataFrame, csv_path: Path) -> EventInfo:
    """Extract event statistics and metadata from a dataframe + filename."""
    info: EventInfo = {
        "laps": len(df),
        "best": df["Lap time"].min(),
        "optimal": df["Optimal"].iloc[0] if "Optimal" in df.columns else df["Lap time"].min(),
        "sigma": df["Lap time"].std(),
    }

    settled_start = int(len(df) * 0.4)
    settled_df = df.iloc[settled_start:]
    info["settled"] = settled_df["Lap time"].mean()

    if "Valid" in df.columns:
        info["clean_pct"] = (df["Valid"] == True).sum() / len(df) * 100  # noqa: E712
    elif "Clean" in df.columns:
        clean_series = pd.to_numeric(df["Clean"], errors="coerce").fillna(0)
        info["clean_pct"] = (clean_series > 0).sum() / len(df) * 100
    else:
        info["clean_pct"] = 100.0

    filename = csv_path.name
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    if date_match:
        info["date"] = date_match.group(1)
    else:
        mtime = csv_path.stat().st_mtime
        info["date"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    info["type"] = _detect_event_type(filename.lower())
    return info


def _detect_event_type(filename_lower: str) -> str:
    if "race" in filename_lower:
        return "ai-race" if "ai" in filename_lower or "offline" in filename_lower else "race"
    if "qualify" in filename_lower:
        return "qualifying"
    return "solo"
