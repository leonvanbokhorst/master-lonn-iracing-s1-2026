#!/usr/bin/env python3
"""
Generate a time-trial report and update the weekly summary.

Usage:

    uv run python tools/generate_tt_report.py \\
        --week 01 \\
        --json weeks/week01/data/iracing/eventresult-XXXX.json

The script will:

1. Parse the Time Trial event result JSON (from Garage61 or the iRacing API).
2. Write a markdown report into `weeks/<week>/time-trials/`.
3. Update the `## Time Trial Highlights` table inside `weeks/<week>/README.md`.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence
import re


@dataclass
class TimeTrialResult:
    tt_id: int
    week: str
    track: str
    config: Optional[str]
    start_time: datetime
    end_time: datetime
    laps_completed: int
    best_lap: float
    avg_lap: Optional[float]
    best_avg: Optional[float]
    best_avg_laps: int
    best_avg_start: Optional[int]
    incidents: int
    tt_points: Optional[int]
    tt_rating_before: Optional[int]
    tt_rating_after: Optional[int]
    sof: Optional[int]
    weather_temp_c: Optional[float]
    weather_desc: Optional[str]
    wind_desc: Optional[str]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ms_to_seconds(value: int | float | None) -> Optional[float]:
    if value is None:
        return None
    if value < 0:
        return None
    return float(value) / 10000.0


def format_laptime(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    return f"{seconds:.3f}s"


def format_duration(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def parse_time_trial(data: dict, *, week: str, cust_id: Optional[int]) -> TimeTrialResult:
    meta = data["data"]
    if meta.get("event_type_name") != "Time Trial":
        raise ValueError("Provided event result is not a Time Trial.")

    session = meta["session_results"][0]
    results: Sequence[dict] = session.get("results", [])
    if not results:
        raise ValueError("No results found in Time Trial file.")

    if cust_id:
        entry = next(
            (res for res in results if res.get("cust_id") == cust_id),
            None,
        )
        if not entry:
            raise ValueError(f"No result found for cust_id {cust_id}.")
    else:
        entry = results[0]

    start_time = datetime.fromisoformat(meta["start_time"].replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(meta["end_time"].replace("Z", "+00:00"))
    weather = meta.get("weather", {})
    temp_raw = weather.get("temp_value")
    temp_units = weather.get("temp_units")
    temp_c = None
    if isinstance(temp_raw, (int, float)):
        if temp_units == 0:
            # Fahrenheit => Celsius
            temp_c = (temp_raw - 32) * 5.0 / 9.0
        else:
            temp_c = float(temp_raw)

    wind_val = weather.get("wind_value")
    wind_units = weather.get("wind_units")
    wind_desc = None
    if isinstance(wind_val, (int, float)) and wind_val >= 0:
        unit_str = "mph" if wind_units == 0 else "kph"
        wind_desc = f"{wind_val:.1f} {unit_str}"

    sof_candidates = [
        meta.get("event_strength_of_field"),
        meta.get("car_classes", [{}])[0].get("strength_of_field"),
    ]
    sof_value = None
    for candidate in sof_candidates:
        if isinstance(candidate, (int, float)) and candidate > 0:
            sof_value = int(candidate)
            break

    return TimeTrialResult(
        tt_id=meta["subsession_id"],
        week=week,
        track=meta["track"].get("track_name"),
        config=meta["track"].get("config_name"),
        start_time=start_time,
        end_time=end_time,
        laps_completed=entry.get("laps_complete", 0),
        best_lap=ms_to_seconds(entry.get("best_lap_time")) or 0.0,
        avg_lap=ms_to_seconds(entry.get("average_lap")),
        best_avg=ms_to_seconds(entry.get("best_nlaps_time")),
        best_avg_laps=meta.get("num_laps_for_solo_average", 0),
        best_avg_start=entry.get("best_nlaps_num"),
        incidents=entry.get("incidents", 0),
        tt_points=entry.get("champ_points"),
        tt_rating_before=entry.get("old_ttrating"),
        tt_rating_after=entry.get("new_ttrating"),
        weather_temp_c=temp_c,
        weather_desc=_SKY_MAP.get(weather.get("skies")),
        wind_desc=wind_desc,
        sof=sof_value,
    )


_SKY_MAP = {
    0: "Clear",
    1: "Partly Cloudy",
    2: "Mostly Cloudy",
    3: "Overcast",
}


def build_report_content(result: TimeTrialResult, avg_label: str) -> str:
    cfg = f" ({result.config})" if result.config else ""
    weather_bits = []
    if result.weather_temp_c is not None:
        weather_bits.append(f"{result.weather_temp_c:.1f}°C")
    if result.weather_desc:
        weather_bits.append(result.weather_desc)
    if result.wind_desc:
        weather_bits.append(f"Wind {result.wind_desc}")

    weather_line = " · ".join(weather_bits) if weather_bits else "—"
    duration = format_duration(result.end_time - result.start_time)
    date_str = result.start_time.strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"---",
        f'week: "{result.week}"',
        f"time_trial_id: {result.tt_id}",
        f'date: "{result.start_time.date()}"',
        f"track: \"{result.track}\"",
        f"config: \"{result.config or ''}\"",
        f"---",
        "",
        f"# Time Trial – {result.track}{cfg}",
        "",
        f"**Session:** {date_str} · {duration}",
        f"**Weather:** {weather_line}",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Laps completed | {result.laps_completed} |",
        f"| Laps used for average | {avg_label} |",
        f"| Best lap | {format_laptime(result.best_lap)} |",
        f"| TT average | {format_laptime(result.best_avg)} |",
        f"| Overall average | {format_laptime(result.avg_lap)} |",
        f"| Strength of Field | {result.sof if result.sof is not None else '—'} |",
        f"| TT rating | {format_rating(result.tt_rating_before, result.tt_rating_after)} |",
        f"| TT points | {result.tt_points if result.tt_points is not None else '—'} |",
        f"| Incidents | {result.incidents}x |",
        "",
    ]
    return "\n".join(lines)


def format_rating(before: Optional[int], after: Optional[int]) -> str:
    if before is None and after is None:
        return "—"
    before = before or 0
    after = after or before
    delta = after - before
    sign = "+" if delta >= 0 else ""
    return f"{before} → {after} ({sign}{delta})"


def write_report(result: TimeTrialResult, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    slug = result.start_time.strftime("%Y%m%d-%H%M")
    path = folder / f"tt-{slug}.md"
    start_lap = result.best_avg_start
    laps_used = result.best_avg_laps or 0
    avg_label = (
        f"{laps_used} laps"
        if start_lap is None or start_lap < 0
        else f"{laps_used} laps (laps {start_lap}–{start_lap + laps_used - 1})"
    )
    content = build_report_content(result, avg_label)
    path.write_text(content, encoding="utf-8")
    return path


TT_SECTION = "## Time Trial Highlights"
TT_HEADER = (
    "| Date (UTC) | Track | Best lap | TT avg | Laps | TT pts | Report |\n"
    "| --- | --- | --- | --- | --- | --- | --- |"
)


def update_week_readme(readme_path: Path, result: TimeTrialResult, report_path: Path) -> None:
    """Upsert the time-trial summary row keyed by high-resolution start time."""
    content = readme_path.read_text(encoding="utf-8")
    if TT_SECTION not in content:
        content = content.rstrip() + f"\n\n{TT_SECTION}\n\n{TT_HEADER}\n"

    pattern = re.compile(r"(## Time Trial Highlights\n)(.*?)(?=\n## |\Z)", re.DOTALL)
    match = pattern.search(content)
    if not match:
        raise RuntimeError("Could not locate '## Time Trial Highlights' section.")

    header = match.group(1)
    body = match.group(2)
    lines = [line for line in body.strip("\n").splitlines() if line.strip()]

    data_lines = lines[2:] if len(lines) >= 2 else []
    key_pattern = re.compile(r"<!--\s*key:(.+?)\s*-->")
    row_map: dict[str, str] = {}
    for line in data_lines:
        key_match = key_pattern.search(line)
        if key_match:
            row_map[key_match.group(1).strip()] = line
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if cells:
            row_map[cells[0]] = line

    display_date = result.start_time.strftime("%Y-%m-%d %H:%M")
    row_key = result.start_time.strftime("%Y-%m-%d %H:%M:%S")
    link = report_path.relative_to(readme_path.parent).as_posix()
    legacy_key = display_date
    if legacy_key in row_map:
        del row_map[legacy_key]
    row_map[row_key] = (
        f"| {display_date} | "
        f"{result.track} {f'({result.config})' if result.config else ''} | "
        f"{format_laptime(result.best_lap)} | "
        f"{format_laptime(result.best_avg)} | "
        f"{result.laps_completed} | "
        f"{result.tt_points if result.tt_points is not None else '—'} | "
        f"[Report]({link}) | <!-- key:{row_key} -->"
    )

    sorted_rows = [row_map[key] for key in sorted(row_map.keys(), reverse=True)]
    new_body = "\n".join([TT_HEADER, *sorted_rows]) + "\n\n"
    new_content = content[: match.start(2)] + new_body + content[match.end(2) :]
    readme_path.write_text(new_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Time Trial report.")
    parser.add_argument("--week", required=True, help="Week identifier, e.g. 01")
    parser.add_argument("--json", required=True, help="Path to eventresult JSON file")
    parser.add_argument("--cust-id", type=int, help="Target customer ID (optional)")
    args = parser.parse_args()

    data = load_json(Path(args.json))
    result = parse_time_trial(data, week=args.week, cust_id=args.cust_id)
    week_dir = Path(f"weeks/week{args.week}")
    tt_dir = week_dir / "time-trials"
    report_path = write_report(result, tt_dir)
    update_week_readme(week_dir / "README.md", result, report_path)
    print(f"✅ Time Trial report written to {report_path}")


if __name__ == "__main__":
    main()

