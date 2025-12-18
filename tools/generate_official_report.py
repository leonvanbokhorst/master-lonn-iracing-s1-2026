"""Generate official race report sections from iRacing event result JSON.

This script parses an exported eventresult-*.json file from iRacing,
creates/updates an "Official Race Report" section inside the corresponding
week event markdown, and maintains a summary table inside the week README.

Usage:
    uv run python tools/generate_official_report.py \
        --week 01 --event 12 \
        --json /path/to/eventresult-XXXX.json

Options:
    --event-file  Explicit path to the event markdown. By default the script
                   looks for weeks/week{WEEK}/events/{EVENT:02d}-*.md and picks
                   the first match.
    --readme      Override the week README path. Defaults to
                   weeks/week{WEEK}/README.md.
    --driver-name The display name to match in the JSON results.
    --cust-id     Optional iRacing customer id to match; takes precedence if
                   supplied.

The script is intentionally read-modify-write; ensure your git tree is clean
before running so changes are easy to review.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RaceSummary:
    week: str
    event_number: int
    track: str
    config: str
    start_time: datetime
    sof: int
    field_size: int
    start_position: int
    finish_position: int
    laps_complete: int
    laps_led: int
    best_lap_time: Optional[float]
    best_lap_number: Optional[int]
    average_lap_time: Optional[float]
    incidents: int
    champ_points: int
    old_irating: Optional[int]
    new_irating: Optional[int]
    weather_temp_c: Optional[float]
    weather_condition: Optional[str]
    cautions: int
    caution_laps: int

    @property
    def start_finish_text(self) -> str:
        return f"P{self.start_position}->P{self.finish_position}"

    @property
    def best_avg_text(self) -> str:
        best = f"{self.best_lap_time:.3f}s" if self.best_lap_time else "—"
        avg = f"{self.average_lap_time:.3f}s" if self.average_lap_time else "—"
        return f"{best} / {avg}"

    @property
    def laps_led_text(self) -> str:
        return f"{self.laps_led}/{self.laps_complete}"

    @property
    def irating_delta_text(self) -> str:
        if self.old_irating is None or self.new_irating is None:
            return "—"
        delta = self.new_irating - self.old_irating
        sign = "+" if delta >= 0 else ""
        return f"{self.old_irating} -> {self.new_irating} ({sign}{delta})"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_event_file(week: str, event_number: int) -> Path:
    events_dir = PROJECT_ROOT / f"weeks/week{week}" / "events"
    pattern = f"{event_number:02d}-*.md"
    matches = sorted(events_dir.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No event file matching {pattern} in {events_dir}")
    return matches[0]


def match_driver_result(
    results: Iterable[dict[str, Any]],
    driver_name: str,
    cust_id: Optional[int] = None,
) -> dict[str, Any]:
    if cust_id is not None:
        for row in results:
            if row.get("cust_id") == cust_id:
                return row
    lowered = driver_name.lower()
    for row in results:
        if lowered in row.get("display_name", "").lower():
            return row
    raise ValueError(f"Could not find driver '{driver_name}' in race results")


def shorten_name(full_name: str) -> str:
    parts = full_name.strip().split()
    if not parts:
        return full_name
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


def to_seconds(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return None
    if value <= 0:
        return None
    return value / 10000.0


def parse_summary(
    data: dict[str, Any],
    race_session: dict[str, Any],
    event_number: int,
    week: str,
    driver_name: str,
    cust_id: Optional[int],
) -> tuple[RaceSummary, list[dict[str, Any]], dict[str, Any]]:
    results = list(race_session["results"])
    driver = match_driver_result(results, driver_name, cust_id)

    start_time_raw = data.get("start_time")
    start_dt = None
    if isinstance(start_time_raw, str):
        try:
            if start_time_raw.endswith("Z"):
                start_dt = datetime.fromisoformat(start_time_raw.replace("Z", "+00:00"))
            else:
                start_dt = datetime.fromisoformat(start_time_raw)
        except ValueError:
            start_dt = None
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)

    weather = data.get("weather", {})

    summary = RaceSummary(
        week=week,
        event_number=event_number,
        track=data.get("track", {}).get("track_name", "Unknown track"),
        config=data.get("track", {}).get("config_name")
        or data.get("track", {}).get("track_config_name")
        or "",
        start_time=start_dt.astimezone(timezone.utc),
        sof=int(data.get("event_strength_of_field") or 0),
        field_size=int(data.get("num_drivers") or len(results)),
        start_position=int(driver.get("starting_position", -1)) + 1,
        finish_position=int(driver.get("finish_position", -1)) + 1,
        laps_complete=int(driver.get("laps_complete", data.get("event_laps_complete", 0))),
        laps_led=int(driver.get("laps_lead", 0)),
        best_lap_time=to_seconds(driver.get("best_lap_time")),
        best_lap_number=driver.get("best_lap_num") if driver.get("best_lap_num", -1) > 0 else None,
        average_lap_time=to_seconds(driver.get("average_lap")),
        incidents=int(driver.get("incidents", 0)),
        champ_points=int(driver.get("champ_points", 0)),
        old_irating=driver.get("oldi_rating"),
        new_irating=driver.get("newi_rating"),
        weather_temp_c=weather.get("temp_value"),
        weather_condition=weather.get("weather_type"),
        cautions=int(data.get("num_cautions", 0)),
        caution_laps=int(data.get("num_caution_laps", 0)),
    )
    return summary, results, driver


def build_event_section(
    summary: RaceSummary, results: list[dict[str, Any]], driver_row: dict[str, Any]
) -> str:
    heading = f"## Official Race Report"
    config = f" ({summary.config})" if summary.config else ""
    temp_txt = f"{summary.weather_temp_c:.0f} C" if summary.weather_temp_c is not None else "n/a"
    condition = f" ({summary.weather_condition})" if summary.weather_condition else ""
    meta_line = (
        f"**{summary.track}{config} - {summary.start_time.strftime('%Y-%m-%d %H:%M UTC')}**  "
        f"SOF {summary.sof} | {summary.field_size} drivers | "
        f"Weather {temp_txt}{condition}"
    )
    if summary.cautions:
        meta_line += f" | Cautions {summary.cautions} ({summary.caution_laps} laps)"
    else:
        meta_line += " | Green flag"

    if summary.best_lap_time and summary.best_lap_number:
        best_text = f"{summary.best_lap_time:.3f}s (lap {summary.best_lap_number})"
    elif summary.best_lap_time:
        best_text = f"{summary.best_lap_time:.3f}s"
    else:
        best_text = "—"

    metric_rows = [
        ("Start -> Finish", summary.start_finish_text),
        ("Laps led", summary.laps_led_text),
        ("Best lap", best_text),
        ("Average lap", f"{summary.average_lap_time:.3f}s" if summary.average_lap_time else "—"),
        ("Incidents", f"{summary.incidents}x"),
        ("Champ points", str(summary.champ_points)),
        ("iRating delta", summary.irating_delta_text),
    ]

    table_lines = ["| Metric | Value |", "| --- | --- |"]
    for label, value in metric_rows:
        table_lines.append(f"| {label} | {value} |")

    my_cust = driver_row.get("cust_id")
    rivals: list[dict[str, Any]] = []
    cleaned = sorted(results, key=lambda r: r.get("finish_position", 999))
    for row in cleaned:
        if my_cust is not None and row.get("cust_id") == my_cust:
            continue
        rivals.append(row)
        if len(rivals) == 3:
            break

    rival_lines = []
    for row in rivals:
        name = shorten_name(row.get("display_name", ""))
        best = to_seconds(row.get("best_lap_time"))
        best_txt = f"{best:.3f}s" if best else "—"
        rival_lines.append(
            f"- {name} - P{row.get('finish_position', 0)+1}, best {best_txt}, "
            f"{row.get('incidents', 0)}x inc, {row.get('champ_points', 0)} pts"
        )

    rival_block = "\n".join(rival_lines) if rival_lines else "- n/a"

    return "\n".join(
        [
            heading,
            "",
            meta_line,
            "",
            *table_lines,
            "",
            "**Rival highlights:**",
            rival_block,
            "",
        ]
    )


def replace_or_insert_section(text: str, heading: str, new_section: str) -> str:
    pattern = re.compile(rf"^({re.escape(heading)}\n(?:.+?))(?:\n(?=## )|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    if match:
        start, end = match.span()
        return text[:start] + new_section.rstrip() + "\n\n" + text[end:]
    # Insert before Debrief if present
    debrief_idx = text.find("\n## Debrief")
    if debrief_idx != -1:
        return text[:debrief_idx] + new_section.rstrip() + "\n\n" + text[debrief_idx:]
    # Else append
    if not text.endswith("\n"):
        text += "\n"
    return text + "\n" + new_section.strip() + "\n"


def update_event_page(event_path: Path, section_markdown: str) -> None:
    content = event_path.read_text(encoding="utf-8")
    updated = replace_or_insert_section(content, "## Official Race Report", section_markdown)
    event_path.write_text(updated, encoding="utf-8")


def build_week_row(summary: RaceSummary, event_path: Path) -> tuple[int, str]:
    date_str = summary.start_time.strftime("%Y-%m-%d %H:%M UTC")
    link = event_path.relative_to(PROJECT_ROOT)
    row = (
        f"| {date_str} | {summary.track} | {summary.sof} | {summary.start_finish_text} | "
        f"{summary.laps_led_text} | {summary.incidents}x | {summary.best_avg_text} | "
        f"{summary.champ_points} | [Event #{summary.event_number}]({link.as_posix()}) |"
    )
    return summary.event_number, row


def ensure_week_section(content: str) -> str:
    if "## Official Race Reports" in content:
        return content
    block = (
        "## Official Race Reports\n\n"
        "| Date (UTC) | Track | SOF | Start->Finish | Laps led | Inc | Best / Avg | Pts | Report |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n\n"
    )
    return content.rstrip() + "\n\n" + block


def update_week_readme(readme_path: Path, summary_row: tuple[int, str]) -> None:
    event_no, new_line = summary_row
    content = readme_path.read_text(encoding="utf-8")
    content = ensure_week_section(content)

    section_pattern = re.compile(
        r"(## Official Race Reports\n)(.*?)(?=\n## |\Z)", re.DOTALL
    )
    match = section_pattern.search(content)
    if not match:
        raise RuntimeError("Failed to locate Official Race Reports section")
    header = match.group(1)
    body = match.group(2)
    lines = [line for line in body.strip("\n").splitlines() if line.strip()]

    if not lines:
        data_lines: list[str] = []
    else:
        data_lines = lines[2:]  # skip header/separator

    row_map: dict[int, str] = {}
    for line in data_lines:
        event_match = re.search(r"Event #(\d+)", line)
        if not event_match:
            continue
        row_map[int(event_match.group(1))] = line

    row_map[event_no] = new_line
    rebuilt_rows = [
        "| Date (UTC) | Track | SOF | Start->Finish | Laps led | Inc | Best / Avg | Pts | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for key in sorted(row_map):
        rebuilt_rows.append(row_map[key])

    new_body = "\n" + "\n".join(rebuilt_rows) + "\n\n"
    new_content = content[: match.start(1)] + header + new_body + content[match.end():]
    readme_path.write_text(new_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate official race report sections")
    parser.add_argument("--json", required=True, type=Path, help="Path to eventresult JSON")
    parser.add_argument("--week", required=True, help="Week identifier, e.g. 01")
    parser.add_argument("--event", type=int, required=True, help="Event number within the week")
    parser.add_argument("--event-file", type=Path, help="Explicit event markdown path")
    parser.add_argument("--readme", type=Path, help="Override week README path")
    parser.add_argument("--driver-name", default="Leon", help="Driver name to match in results")
    parser.add_argument("--cust-id", type=int, help="iRacing customer id for the driver")
    args = parser.parse_args()

    json_path: Path = args.json
    data = load_json(json_path)["data"]
    race_session = next(
        (s for s in data.get("session_results", []) if s.get("simsession_type_name") == "Race"),
        None,
    )
    if race_session is None:
        raise ValueError("No race session found inside JSON")

    summary, results, driver_row = parse_summary(
        data,
        race_session,
        event_number=args.event,
        week=args.week,
        driver_name=args.driver_name,
        cust_id=args.cust_id,
    )

    event_path = args.event_file
    if event_path is None:
        event_path = find_event_file(args.week, args.event)
    if not event_path.is_absolute():
        event_path = PROJECT_ROOT / event_path

    section_md = build_event_section(summary, results, driver_row)
    update_event_page(event_path, section_md)

    readme_path = args.readme or (PROJECT_ROOT / f"weeks/week{args.week}" / "README.md")
    if not readme_path.is_absolute():
        readme_path = PROJECT_ROOT / readme_path

    row = build_week_row(summary, event_path)
    update_week_readme(readme_path, row)

    print(f"Updated {event_path.relative_to(PROJECT_ROOT)} and {readme_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()





