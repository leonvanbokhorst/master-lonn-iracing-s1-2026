#!/usr/bin/env python3
"""Helper to spin up templated weekly notes for the 2026 FF1600 season.

Usage example:

    uv run python tools/create_week.py --week 1
    uv run python tools/create_week.py --week 2 --track "Brands Hatch Indy" --start 2025-12-17 --end 2025-12-23

The script copies `tools/week_template.md`, fills in metadata, and writes the new
file to `weeks/weekXX-track-slug.md`. It leaves brake bias blank so you can fill
it once a baseline emerges.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import unicodedata

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "tools" / "week_template.md"
WEEKS_DIR = REPO_ROOT / "weeks"
TRACK_DATA_PATH = REPO_ROOT / "tools" / "tracks.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a weekly logbook file.")
    parser.add_argument("--week", type=int, required=True, help="iRacing week number (1-based).")
    parser.add_argument(
        "--track",
        type=str,
        help="Track name override. Defaults to schedule lookup when available.",
    )
    parser.add_argument(
        "--season",
        type=str,
        default="2026 Season 1",
        help="Season label stored in the weekly metadata.",
    )
    parser.add_argument(
        "--series",
        type=str,
        default="Ray FF1600 Rookie Fixed",
        help="Series label stored in the weekly metadata.",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="",
        help="Optional ISO date (YYYY-MM-DD) for when the iRacing week opens.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="",
        help="Optional ISO date (YYYY-MM-DD) for when the iRacing week closes.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing file if present.",
    )
    return parser.parse_args()


def load_track_library() -> Dict[int, Dict[str, Any]]:
    if not TRACK_DATA_PATH.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.exit(
            "tracks.yaml found but PyYAML is missing. Install it with `uv add pyyaml` "
            "or remove tracks.yaml to skip schedule autoloading."
        )

    data = yaml.safe_load(TRACK_DATA_PATH.read_text(encoding="utf-8"))  # type: ignore
    if not data or "weeks" not in data:
        return {}

    library: Dict[int, Dict[str, Any]] = {}
    for entry in data["weeks"]:
        try:
            week_num = int(entry["week"])
        except (KeyError, TypeError, ValueError):
            continue
        library[week_num] = entry
    return library


def slugify(value: str) -> str:
    """Make a filesystem-friendly slug from the track name."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    value = ascii_only.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def load_template() -> str:
    if not TEMPLATE_PATH.exists():
        sys.exit(f"Template not found at {TEMPLATE_PATH}. Did you move or rename it?")
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def render_content(
    template: str,
    *,
    week: int,
    track: str,
    layout: str,
    season: str,
    series: str,
    start: str,
    end: str,
    race_length_minutes: Optional[int],
    special_event: Optional[Dict[str, Any]],
    conditions: Optional[Dict[str, Any]],
) -> str:
    formatted_week = f"{week:02d}"
    track_heading = f"{track} – {layout}" if layout else track
    replacements = {
        'week: 00': f"week: {formatted_week}",
        'track: "TBD"': f'track: "{track}"',
        'layout: ""': f'layout: "{layout}"' if layout else 'layout: ""',
        'season: "2026 Season 1"': f'season: "{season}"',
        'series: "Ray FF1600 Rookie Fixed"': f'series: "{series}"',
        'race_length_minutes: ""': f"race_length_minutes: {race_length_minutes}" if race_length_minutes else 'race_length_minutes: ""',
        'start: ""': f'start: "{start}"' if start else 'start: ""',
        'end: ""': f'end: "{end}"' if end else 'end: ""',
        "{{week}}": formatted_week,
        "{{track_heading}}": track_heading,
        "{{track}}": track,
        "{{layout}}": layout,
    }

    content = template
    for needle, replacement in replacements.items():
        content = content.replace(needle, replacement)

    if special_event:
        for key, value in special_event.items():
            placeholder = f'special_event_{key}: ""'
            if placeholder in content and value:
                content = content.replace(placeholder, f'special_event_{key}: "{value}"')
    if conditions:
        for key, value in conditions.items():
            placeholder = f'conditions_{key}: ""'
            if placeholder in content and value not in (None, ""):
                content = content.replace(placeholder, f'conditions_{key}: "{value}"')
    return content


def determine_filename(week: int, track: str) -> Path:
    slug = slugify(track)
    slug_part = f"-{slug}" if slug else ""
    filename = f"week{week:02d}{slug_part}.md"
    return WEEKS_DIR / filename


def main() -> None:
    args = parse_args()
    if args.week < 1:
        sys.exit("Week number must be >= 1.")

    track_library = load_track_library()
    track_entry = track_library.get(args.week)

    track_name = args.track or (track_entry.get("track") if track_entry else None)
    if not track_name:
        sys.exit("Track name missing. Supply --track or populate tools/tracks.yaml.")
    layout = (track_entry or {}).get("layout", "") if track_entry else ""
    race_length_minutes = (track_entry or {}).get("race_length_minutes")

    start_source: Any = args.start or ((track_entry or {}).get("start_date") if track_entry else "")
    if isinstance(start_source, (dt.date, dt.datetime)):
        start = start_source.date().isoformat() if isinstance(start_source, dt.datetime) else start_source.isoformat()
    else:
        start = str(start_source) if start_source else ""

    end_source: Any = args.end or (track_entry.get("end_date") if track_entry else "")
    if isinstance(end_source, (dt.date, dt.datetime)):
        end = end_source.date().isoformat() if isinstance(end_source, dt.datetime) else end_source.isoformat()
    else:
        end = str(end_source) if end_source else ""

    if not end and start:
        try:
            start_date = dt.date.fromisoformat(start)
            end = (start_date + dt.timedelta(days=6)).isoformat()
        except ValueError:
            end = ""

    special_event = None
    if track_entry and isinstance(track_entry.get("special_event"), dict):
        special_event = track_entry["special_event"]
    conditions = None
    if track_entry and isinstance(track_entry.get("conditions"), dict):
        conditions = track_entry["conditions"]

    template = load_template()
    content = render_content(
        template,
        week=args.week,
        track=track_name,
        layout=layout,
        season=args.season,
        series=args.series,
        start=start,
        end=end,
        race_length_minutes=race_length_minutes if isinstance(race_length_minutes, int) else None,
        special_event=special_event,
        conditions=conditions,
    )

    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = determine_filename(args.week, track_name)

    if target_path.exists() and not args.force:
        sys.exit(f"{target_path.relative_to(REPO_ROOT)} already exists. Use --force to overwrite.")

    target_path.write_text(content, encoding="utf-8")
    rel_path = target_path.relative_to(REPO_ROOT)
    print(f"Wrote {rel_path}")


if __name__ == "__main__":
    main()

