#!/usr/bin/env python3
"""
iRacing Race Analysis Tool
Analyzes event result JSON files and generates insightful markdown reports.

Usage:
    uv run python tools/analyze_race.py results/eventresult-XXXXX.json --driver "Your Name"
    uv run python tools/analyze_race.py results/eventresult-XXXXX.json --cust-id 123456
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DriverResult:
    """Parsed driver result from a race session."""
    cust_id: int
    name: str
    start_pos: int
    finish_pos: int
    best_lap_ms: int  # milliseconds, -1 if no lap set
    avg_lap_ms: int   # milliseconds
    incidents: int
    laps_complete: int
    laps_lead: int
    old_irating: int
    new_irating: int
    division: str
    country: str


@dataclass
class RaceMetrics:
    """Calculated metrics for analysis."""
    # Pace
    gap_to_event_best_ms: int
    gap_to_winner_ms: int
    pace_rank: int  # where you'd rank by best lap alone
    
    # Consistency
    consistency_spread_ms: int  # avg - best
    field_avg_spread_ms: float
    consistency_rank: int  # 1 = most consistent
    
    # Incidents
    incidents: int
    field_avg_incidents: float
    incident_rate: float  # per lap
    clean_drivers_count: int
    
    # Context
    total_drivers: int
    drivers_with_better_pace: int
    drivers_with_worse_pace: int


def ms_to_laptime(tenths_ms: int) -> str:
    """Convert iRacing time (10ths of milliseconds) to M:SS.mmm format."""
    if tenths_ms <= 0:
        return "N/A"
    # iRacing stores times as 10ths of milliseconds
    total_seconds = tenths_ms / 10000
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:06.3f}"


def ms_to_delta(tenths_ms: int, prefix: str = "+") -> str:
    """Convert iRacing time delta (10ths of ms) to +X.XXX delta format."""
    if tenths_ms <= 0:
        return "N/A"
    return f"{prefix}{tenths_ms / 10000:.3f}s"


def load_event_result(json_path: Path) -> dict:
    """Load and parse iRacing event result JSON."""
    with open(json_path) as f:
        return json.load(f)


def extract_race_session(data: dict) -> Optional[dict]:
    """Find the RACE session from session_results."""
    event_data = data.get("data", data)
    for session in event_data.get("session_results", []):
        if session.get("simsession_name") == "RACE":
            return session
    return None


def parse_driver_results(race_session: dict) -> list[DriverResult]:
    """Parse all driver results from the race session."""
    drivers = []
    for r in race_session.get("results", []):
        # Handle missing iRating data (rookies without rated races)
        old_ir = r.get("oldi_rating", -1)
        new_ir = r.get("newi_rating", -1)
        
        drivers.append(DriverResult(
            cust_id=r["cust_id"],
            name=r["display_name"],
            start_pos=r.get("starting_position", -1) + 1,  # 0-indexed to 1-indexed
            finish_pos=r.get("finish_position", -1) + 1,
            best_lap_ms=r.get("best_lap_time", -1),
            avg_lap_ms=r.get("average_lap", 0),
            incidents=r.get("incidents", 0),
            laps_complete=r.get("laps_complete", 0),
            laps_lead=r.get("laps_lead", 0),
            old_irating=old_ir if old_ir > 0 else 0,
            new_irating=new_ir if new_ir > 0 else 0,
            division=r.get("division_name", "Unknown"),
            country=r.get("country_code", "??"),
        ))
    return drivers


def find_driver(drivers: list[DriverResult], name: Optional[str] = None, 
                cust_id: Optional[int] = None) -> Optional[DriverResult]:
    """Find target driver by name or customer ID."""
    for d in drivers:
        if cust_id and d.cust_id == cust_id:
            return d
        if name and name.lower() in d.name.lower():
            return d
    return None


def calculate_metrics(target: DriverResult, all_drivers: list[DriverResult],
                     event_best_lap_ms: int) -> RaceMetrics:
    """Calculate all analysis metrics for the target driver."""
    
    # Filter to drivers who set a lap time
    drivers_with_laps = [d for d in all_drivers if d.best_lap_ms > 0]
    
    # Winner is position 1
    winner = next((d for d in all_drivers if d.finish_pos == 1), None)
    winner_best = winner.best_lap_ms if winner and winner.best_lap_ms > 0 else event_best_lap_ms
    
    # Pace analysis
    gap_to_event_best = target.best_lap_ms - event_best_lap_ms if target.best_lap_ms > 0 else -1
    gap_to_winner = target.best_lap_ms - winner_best if target.best_lap_ms > 0 else -1
    
    # Sort by best lap to find pace rank
    sorted_by_pace = sorted(drivers_with_laps, key=lambda d: d.best_lap_ms)
    pace_rank = next((i + 1 for i, d in enumerate(sorted_by_pace) if d.cust_id == target.cust_id), -1)
    
    # Consistency analysis (avg - best)
    target_spread = target.avg_lap_ms - target.best_lap_ms if target.best_lap_ms > 0 else -1
    
    spreads = []
    for d in drivers_with_laps:
        if d.avg_lap_ms > 0 and d.best_lap_ms > 0:
            spreads.append(d.avg_lap_ms - d.best_lap_ms)
    
    field_avg_spread = sum(spreads) / len(spreads) if spreads else 0
    
    # Rank by consistency (lower spread = better)
    sorted_by_consistency = sorted(
        [(d, d.avg_lap_ms - d.best_lap_ms) for d in drivers_with_laps if d.avg_lap_ms > 0],
        key=lambda x: x[1]
    )
    consistency_rank = next(
        (i + 1 for i, (d, _) in enumerate(sorted_by_consistency) if d.cust_id == target.cust_id), 
        -1
    )
    
    # Incident analysis
    total_incidents = sum(d.incidents for d in all_drivers)
    field_avg_incidents = total_incidents / len(all_drivers) if all_drivers else 0
    clean_drivers = sum(1 for d in all_drivers if d.incidents == 0)
    incident_rate = target.incidents / target.laps_complete if target.laps_complete > 0 else 0
    
    # Count drivers with better/worse pace
    better_pace = sum(1 for d in drivers_with_laps if d.best_lap_ms < target.best_lap_ms and d.best_lap_ms > 0)
    worse_pace = sum(1 for d in drivers_with_laps if d.best_lap_ms > target.best_lap_ms)
    
    return RaceMetrics(
        gap_to_event_best_ms=gap_to_event_best,
        gap_to_winner_ms=gap_to_winner,
        pace_rank=pace_rank,
        consistency_spread_ms=target_spread,
        field_avg_spread_ms=field_avg_spread,
        consistency_rank=consistency_rank,
        incidents=target.incidents,
        field_avg_incidents=field_avg_incidents,
        incident_rate=incident_rate,
        clean_drivers_count=clean_drivers,
        total_drivers=len(all_drivers),
        drivers_with_better_pace=better_pace,
        drivers_with_worse_pace=worse_pace,
    )


def generate_report(target: DriverResult, metrics: RaceMetrics, 
                   all_drivers: list[DriverResult], event_data: dict) -> str:
    """Generate the markdown analysis report."""
    
    data = event_data.get("data", event_data)
    track_info = data.get("track", {})
    track_name = f"{track_info.get('track_name', 'Unknown')} - {track_info.get('config_name', '')}"
    event_best = data.get("event_best_lap_time", 0)
    sof = data.get("event_strength_of_field", 0)
    
    # Find winner for comparison
    winner = next((d for d in all_drivers if d.finish_pos == 1), None)
    
    # Calculate position change
    pos_change = target.start_pos - target.finish_pos
    pos_emoji = "🟢" if pos_change > 0 else ("🔴" if pos_change < 0 else "⚪")
    pos_text = f"+{pos_change}" if pos_change > 0 else str(pos_change)
    
    # iRating change
    ir_change = target.new_irating - target.old_irating
    ir_emoji = "📈" if ir_change > 0 else "📉"
    
    # Build report
    lines = [
        f"# Race Analysis: {track_name}",
        "",
        f"**Date**: {data.get('start_time', 'Unknown')[:10]}",
        f"**Series**: {data.get('series_name', 'Unknown')}",
        f"**Field Size**: {metrics.total_drivers} drivers | **SOF**: {sof}",
        "",
        "---",
        "",
        "## Your Results Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Position | P{target.start_pos} → P{target.finish_pos} ({pos_emoji} {pos_text}) |",
        f"| Best Lap | {ms_to_laptime(target.best_lap_ms)} |",
        f"| Avg Lap | {ms_to_laptime(target.avg_lap_ms)} |",
        f"| Laps | {target.laps_complete} |",
        f"| Incidents | {target.incidents}x |",
        f"| iRating | {target.old_irating} → {target.new_irating} ({ir_emoji} {ir_change:+d}) |",
        "",
        "---",
        "",
        "## 🏎️ Pace Analysis",
        "",
    ]
    
    # Pace section
    if target.best_lap_ms > 0:
        lines.extend([
            "| Comparison | Gap |",
            "|------------|-----|",
            f"| vs Event Best ({ms_to_laptime(event_best)}) | {ms_to_delta(metrics.gap_to_event_best_ms)} |",
        ])
        if winner:
            lines.append(f"| vs Winner ({winner.name}) | {ms_to_delta(metrics.gap_to_winner_ms)} |")
        lines.extend([
            "",
            f"**Pace Rank**: {metrics.pace_rank}/{metrics.total_drivers} "
            f"(faster than {metrics.drivers_with_worse_pace} drivers)",
            "",
        ])
        
        # Show top 5 by pace
        sorted_by_pace = sorted([d for d in all_drivers if d.best_lap_ms > 0], key=lambda d: d.best_lap_ms)
        lines.extend([
            "### Fastest Laps in Session",
            "",
            "| Rank | Driver | Best Lap | Finish |",
            "|------|--------|----------|--------|",
        ])
        for i, d in enumerate(sorted_by_pace[:5]):
            marker = " ⬅️ YOU" if d.cust_id == target.cust_id else ""
            lines.append(f"| {i+1} | {d.name} | {ms_to_laptime(d.best_lap_ms)} | P{d.finish_pos}{marker} |")
        
        # Show target if not in top 5
        if metrics.pace_rank > 5:
            lines.append(f"| ... | | | |")
            lines.append(f"| {metrics.pace_rank} | {target.name} | {ms_to_laptime(target.best_lap_ms)} | P{target.finish_pos} ⬅️ YOU |")
        lines.append("")
    else:
        lines.append("*No valid lap time recorded*\n")
    
    # Consistency section
    lines.extend([
        "---",
        "",
        "## 📊 Consistency Analysis",
        "",
    ])
    
    if metrics.consistency_spread_ms > 0:
        spread_vs_field = metrics.consistency_spread_ms - metrics.field_avg_spread_ms
        spread_verdict = "BETTER" if spread_vs_field < 0 else "WORSE"
        spread_emoji = "✅" if spread_vs_field < 0 else "⚠️"
        
        lines.extend([
            f"Your **consistency spread** (avg lap - best lap): **{ms_to_delta(metrics.consistency_spread_ms, '')}**",
            "",
            f"- Field average spread: {metrics.field_avg_spread_ms / 10000:.3f}s",
            f"- {spread_emoji} You are **{abs(spread_vs_field) / 10000:.3f}s {spread_verdict}** than average",
            f"- Consistency Rank: {metrics.consistency_rank}/{metrics.total_drivers}",
            "",
        ])
        
        # Diagnose the problem (times in 10ths of ms, so 15s = 150000)
        if metrics.consistency_spread_ms > 150000:  # More than 15 seconds spread
            lines.extend([
                "### ⚠️ High Spread Detected",
                "",
                "Your average lap is significantly slower than your best. This usually indicates:",
                "- Off-track excursions or spins",
                "- Heavy traffic/battles that cost time",
                "- Incidents requiring recovery time",
                "- Slow out-lap or in-lap included in average",
                "",
            ])
    else:
        lines.append("*Unable to calculate consistency (missing lap data)*\n")
    
    # Incident section
    lines.extend([
        "---",
        "",
        "## 💥 Incident Analysis",
        "",
        f"| Metric | You | Field Avg |",
        f"|--------|-----|-----------|",
        f"| Total Incidents | {target.incidents}x | {metrics.field_avg_incidents:.1f}x |",
        f"| Per Lap | {metrics.incident_rate:.2f}x | - |",
        "",
        f"**Clean drivers this race**: {metrics.clean_drivers_count}/{metrics.total_drivers}",
        "",
    ])
    
    if target.incidents > metrics.field_avg_incidents:
        lines.extend([
            "### Areas to Review",
            "",
            "Your incident count is above average. Consider reviewing:",
            "- Replay footage for contact points",
            "- Brake points into corners (track limits)",
            "- Awareness of cars around you",
            "",
        ])
    elif target.incidents == 0:
        lines.append("🌟 **Clean race!** Great job keeping it tidy.\n")
    
    # Improvement section
    lines.extend([
        "---",
        "",
        "## 🎯 Improvement Focus Areas",
        "",
    ])
    
    # Calculate where time can be found (times are in 10ths of ms)
    if target.best_lap_ms > 0 and event_best > 0:
        time_to_find = (target.best_lap_ms - event_best) / 10000
        
        lines.append("### Time Budget")
        lines.append("")
        lines.append(f"To match the **event best lap**, you need to find **{time_to_find:.3f}s**")
        lines.append("")
        
        # Find driver 1 position ahead
        driver_ahead = next((d for d in all_drivers if d.finish_pos == target.finish_pos - 1), None)
        if driver_ahead and driver_ahead.best_lap_ms > 0:
            gap_to_ahead = (target.best_lap_ms - driver_ahead.best_lap_ms) / 10000
            lines.append(f"To catch **P{driver_ahead.finish_pos}** ({driver_ahead.name}): find **{gap_to_ahead:.3f}s**")
            lines.append("")
    
    # Main recommendation
    lines.append("### Primary Focus")
    lines.append("")
    
    pace_gap = metrics.gap_to_event_best_ms / 10000 if metrics.gap_to_event_best_ms > 0 else 0
    consistency_gap = (metrics.consistency_spread_ms - metrics.field_avg_spread_ms) / 10000 if metrics.consistency_spread_ms > 0 else 0
    
    focus_areas = []
    
    if consistency_gap > 5:  # More than 5 seconds worse than field average
        focus_areas.append(("🔄 CONSISTENCY", "Your spread is high - focus on clean, repeatable laps before chasing pace"))
    
    if target.incidents > metrics.field_avg_incidents * 1.5:
        focus_areas.append(("🛡️ SAFETY", "Reduce incidents - they're costing you positions and time"))
    
    if pace_gap > 2 and consistency_gap <= 5:
        focus_areas.append(("⚡ RAW PACE", "Your consistency is decent - time to push harder and find the limit"))
    
    if not focus_areas:
        focus_areas.append(("✨ MAINTAIN", "Solid race! Keep building on this performance"))
    
    for emoji_title, advice in focus_areas:
        lines.append(f"**{emoji_title}**: {advice}")
        lines.append("")
    
    # Similar iRating comparison
    lines.extend([
        "---",
        "",
        "## 📈 Field Comparison",
        "",
        "### All Drivers by Finish Position",
        "",
        "| Pos | Driver | Best Lap | Avg Lap | Inc | iR Change |",
        "|-----|--------|----------|---------|-----|-----------|",
    ])
    
    sorted_by_finish = sorted(all_drivers, key=lambda d: d.finish_pos)
    for d in sorted_by_finish:
        ir_ch = d.new_irating - d.old_irating if d.new_irating > 0 else 0
        ir_str = f"{ir_ch:+d}" if ir_ch != 0 else "-"
        marker = " ⬅️" if d.cust_id == target.cust_id else ""
        lines.append(
            f"| P{d.finish_pos} | {d.name} | {ms_to_laptime(d.best_lap_ms)} | "
            f"{ms_to_laptime(d.avg_lap_ms)} | {d.incidents}x | {ir_str}{marker} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        f"*Report generated by analyze_race.py*",
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze iRacing race results")
    parser.add_argument("json_file", type=Path, help="Path to event result JSON file")
    parser.add_argument("--driver", type=str, help="Driver name to analyze")
    parser.add_argument("--cust-id", type=int, help="Customer ID to analyze")
    parser.add_argument("--output", type=Path, help="Output file path (default: auto-generated)")
    
    args = parser.parse_args()
    
    if not args.driver and not args.cust_id:
        parser.error("Must specify either --driver or --cust-id")
    
    # Load data
    print(f"Loading {args.json_file}...")
    data = load_event_result(args.json_file)
    
    # Find race session
    race_session = extract_race_session(data)
    if not race_session:
        print("ERROR: No race session found in JSON")
        return 1
    
    # Parse drivers
    all_drivers = parse_driver_results(race_session)
    print(f"Found {len(all_drivers)} drivers in race")
    
    # Find target driver
    target = find_driver(all_drivers, name=args.driver, cust_id=args.cust_id)
    if not target:
        print(f"ERROR: Driver not found. Available drivers:")
        for d in all_drivers:
            print(f"  - {d.name} (ID: {d.cust_id})")
        return 1
    
    print(f"Analyzing: {target.name}")
    
    # Calculate metrics
    event_data = data.get("data", data)
    event_best = event_data.get("event_best_lap_time", 0)
    metrics = calculate_metrics(target, all_drivers, event_best)
    
    # Generate report
    report = generate_report(target, metrics, all_drivers, data)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        subsession_id = event_data.get("subsession_id", "unknown")
        output_path = args.json_file.parent / f"race-analysis-{subsession_id}.md"
    
    # Write report
    output_path.write_text(report)
    print(f"\n✅ Report saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())



