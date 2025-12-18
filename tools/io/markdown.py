"""Markdown helpers for event + week content generation."""

from __future__ import annotations

from pathlib import Path
import re

from core.models import EventInfo, TelemetryStats, WeekEventEntry

from .templates import load_template

FALLBACK_EVENT_TEMPLATE = """---
event: {{event_num}}
week: {{week}}
date: "{{date}}"
type: "{{type}}"
---

# Event #{{event_num}} – {{date}} – {{type}}

[← Back to Week](../README.md)

## Quick Stats

| Metric | Value |
|--------|-------|
| **Laps** | {{laps}} |
| **Best Lap** | {{best}}s |
| **Settled Pace** | {{settled}}s |
| **Consistency (σ)** | {{sigma}}s |
| **Clean Laps** | {{clean_pct}}% |

## Lap Times

![Lap Progression](../images/event-{{event_num_pad}}-laptimes.png)

{{#if telemetry}}
## Telemetry Analysis

![Telemetry](../images/event-{{event_num_pad}}-telemetry.png)

### Pedal Usage

- Full throttle: {{throttle_pct}}%
- Braking: {{brake_pct}}%
- Coasting: {{coast_pct}}%
{{/if}}

## Debrief

**The Facts:**
- _What happened objectively?_

**The Feelings:**
- _How did it feel?_

**Focus for Next Event:**
1. _..._
"""

METRIC_KEY_MAP = {
    "laps": "laps",
    "best lap": "best",
    "consistency (σ)": "sigma",
}


def render_template(template: str, context: dict[str, str]) -> str:
    """Basic template renderer supporting {{var}} replacement."""

    def repl(match: re.Match) -> str:
        name = match.group(1).strip()
        return str(context.get(name, match.group(0)))

    return re.sub(r"\{\{(.*?)\}\}", repl, template)


def create_event_page(
    event_num: int,
    week: str,
    info: EventInfo,
    events_dir: Path,
    telemetry_stats: TelemetryStats | None = None,
) -> Path:
    """Render and write the per-event markdown page."""
    template = load_template("event-page.md", default=FALLBACK_EVENT_TEMPLATE)

    ctx = {
        "event_num": str(event_num),
        "event_num_pad": f"{event_num:02d}",
        "week": week,
        "date": info["date"],
        "type": info["type"],
        "laps": str(info["laps"]),
        "best": f"{info['best']:.3f}",
        "optimal": f"{info['optimal']:.3f}",
        "settled": f"{info['settled']:.3f}",
        "sigma": f"{info['sigma']:.2f}",
        "clean_pct": f"{info['clean_pct']:.0f}",
        "filter_summary": info.get("filter_summary", ""),
        "garage_link": "",
        "next_event_nav": "",
    }

    garage_event_id = info.get("garage_event_id")
    if garage_event_id:
        ctx["garage_link"] = (
            f" | **[Garage 61 Event Page](https://garage61.net/app/event/{garage_event_id})**"
        )

    next_event = info.get("next_event")
    if next_event:
        ctx["next_event_nav"] = f" | [Next Event →](./{next_event}.md)"

    if telemetry_stats:
        ctx.update(
            {
                "throttle_pct": f"{telemetry_stats['throttle_pct']:.1f}",
                "brake_pct": f"{telemetry_stats['brake_pct']:.1f}",
                "coast_pct": f"{telemetry_stats['coast_pct']:.1f}",
            }
        )
        template = template.replace("{{#if telemetry}}", "").replace("{{/if}}", "")
    else:
        template = re.sub(r"\{\{#if telemetry\}\}.*?\{\{/if\}\}", "", template, flags=re.DOTALL)

    content = render_template(template, ctx)
    type_slug = info["type"].replace(" ", "-")
    event_filename = f"{event_num:02d}-{info['date']}-{type_slug}.md"
    event_path = events_dir / event_filename
    event_path.write_text(content)
    return event_path


def parse_event_stats(md_path: Path) -> dict:
    """Extract stats from an event markdown file."""
    if not md_path.exists():
        return {}

    content = md_path.read_text()
    stats: dict[str, float | int] = {}
    row_re = re.compile(r"\|\s*([^|]+?)\s*\|\s*([0-9.]+)")

    for label_raw, value_raw in row_re.findall(content):
        label_norm = label_raw.replace("*", "").strip().lower()
        key = METRIC_KEY_MAP.get(label_norm)
        if not key:
            continue
        try:
            value = float(value_raw)
            stats[key] = int(value) if key == "laps" else value
        except ValueError:
            continue

    return stats


def compute_week_summary(events: list[WeekEventEntry]) -> str:
    """Compute summary statistics for the week."""
    if not events:
        return "_No events yet._"

    valid = [
        e
        for e in events
        if isinstance(e.get("best"), (int, float)) and e.get("best", 0) > 0
    ]
    if not valid:
        return "_No events yet._"

    best_lap = min(e["best"] for e in valid)
    first_lap = valid[0]["best"]
    last_sigma = valid[-1]["sigma"]
    improvement = first_lap - best_lap

    return (
        f"- **Events:** {len(events)}\n"
        f"- **Best Lap:** {best_lap:.3f}s\n"
        f"- **Improvement:** {improvement:+.3f}s (from {first_lap:.3f}s)\n"
        f"- **Latest σ:** {last_sigma:.2f}s"
    )


def update_week_readme(week: str, weeks_dir: Path, events: list[WeekEventEntry]) -> Path:
    """Update or create the week README."""
    week_dir = weeks_dir / f"week{week}"
    readme_path = week_dir / "README.md"

    table_rows = []
    for e in events:
        notes = "_Add notes..._" if not e.get("notes") else e["notes"]
        details_link = f"[→](events/{e['filename']})"
        table_rows.append(
            f"| {e['num']} | {e['date']} | {e['type']} | {e['laps']} | "
            f"{e['best']:.3f}s | {e['sigma']:.2f}s | {notes} | {details_link} |"
        )

    events_table = "\n".join(table_rows)
    summary = compute_week_summary(events)

    if readme_path.exists():
        content = readme_path.read_text()
        for e in events:
            row_match = re.search(
                r"\|\s*" + str(e["num"]) + r"\s*\|.*?\|.*?\|.*?\|.*?\|.*?\|\s*(.*?)\s*\|",
                content,
            )
            if row_match and not e.get("notes"):
                e["notes"] = row_match.group(1).strip()
            table_rows[events.index(e)] = (
                f"| {e['num']} | {e['date']} | {e['type']} | {e['laps']} | "
                f"{e['best']:.3f}s | {e['sigma']:.2f}s | "
                f"{e.get('notes', '_Add notes..._')} | [→](events/{e['filename']}) |"
            )
        events_table = "\n".join(table_rows)

        table_start_match = re.search(r"\|\s*#\s*\|\s*Date", content)
        if table_start_match:
            start_idx = table_start_match.start()
            lines = content[start_idx:].split("\n")
            end_offset = 0
            for i, line in enumerate(lines):
                if i > 1 and not line.strip().startswith("|"):
                    break
                end_offset += len(line) + 1

            pre_table = content[:start_idx]
            post_table = content[start_idx + end_offset :]
            new_table_header = (
                "| # | Date | Type | Laps | Best | σ | Notes | Details |\n"
                "|---|------|------|------|------|---|-------|---------|"
            )
            new_table = f"{new_table_header}\n{events_table}\n"
            content = f"{pre_table}{new_table}\n{post_table.lstrip()}"
        else:
            if "## Events" in content:
                content = content.replace(
                    "## Events",
                    "## Events\n\n| # | Date | Type | Laps | Best | σ | Notes | Details |\n"
                    "|---|------|------|------|------|---|-------|---------|\n"
                    f"{events_table}",
                )
            else:
                content += (
                    "\n\n## Events\n\n| # | Date | Type | Laps | Best | σ | Notes | Details |\n"
                    "|---|------|------|------|------|---|-------|---------|\n"
                    f"{events_table}"
                )

        summary_pattern = r"(## Summary\n\n)([\s\S]*?)(?=\n## |\Z)"
        if re.search(summary_pattern, content):
            content = re.sub(summary_pattern, f"\\1{summary}\n", content)
    else:
        intent = "Write your intent here..."
        reflection = (
            "- Track craft takeaways: ...\n"
            "- Brake bias learnings: ...\n"
            "- Driver mindset notes: ..."
        )

        content = (
            f"---\nweek: {week}\n---\n\n# Week {week}\n\n## Events\n\n"
            "| # | Date | Type | Laps | Best | σ | Notes | Details |\n"
            "|---|------|------|------|------|---|-------|---------|\n"
            f"{events_table}\n\n## Summary\n\n{summary}\n\n## Reflection\n\n{reflection}\n"
        )

    readme_path.write_text(content)
    return readme_path
