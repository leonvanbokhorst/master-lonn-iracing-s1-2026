"""TypedDict-based models shared across CLI tools and visualizations."""

from __future__ import annotations

from typing import TypedDict


class EventStats(TypedDict):
    """Core statistics derived from an event CSV."""

    laps: int
    best: float
    optimal: float
    sigma: float
    settled: float
    clean_pct: float
    date: str
    type: str


class EventInfo(EventStats, total=False):
    """Extended event information used by templates and README tables."""

    num: int
    filename: str
    filter_summary: str
    notes: str
    next_event: str
    garage_event_id: str
    filter_metadata: FilterMetadata | None


class WeekEventEntry(TypedDict, total=False):
    """Row structure for week README stats tables."""

    num: int
    date: str
    type: str
    laps: int | str
    best: float
    sigma: float
    filename: str
    notes: str


class FilterMetadata(TypedDict, total=False):
    """Metadata returned by Tukey filtering."""

    applied: bool
    median: float
    q1: float
    q3: float
    iqr: float
    lower_bound: float | None
    upper_bound: float | None
    total_count: int
    kept_count: int
    removed_count: int
    removed_laps: list[int]


class TelemetryStats(TypedDict):
    """Aggregate telemetry statistics for template rendering."""

    throttle_pct: float
    brake_pct: float
    coast_pct: float
