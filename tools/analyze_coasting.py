#!/usr/bin/env python3
"""
Coasting Impact Analysis Engine
================================

Transforms coasting data from a passive metric into an actionable learning tool.

Provides:
- Corner-by-corner coasting breakdown
- Time cost analysis per zone
- Root cause classification (entry/mid/exit)
- Specific recommendations for improvement
- Trend analysis over time

Usage:
    python tools/analyze_coasting.py <telemetry_file>
    python tools/analyze_coasting.py weeks/week01/events/06-2025-12-13-ai-race/telemetry.csv

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict
from config import pedals, COLORS

@dataclass
class CoastingZone:
    """Represents a single coasting zone with analysis."""
    start_pct: float
    end_pct: float
    duration_sec: float
    time_cost_sec: float
    corner_name: str
    phase: str  # 'entry', 'mid', 'exit', 'transition'
    severity: str  # 'minor', 'moderate', 'severe'
    recommendation: str


@dataclass
class CornerAnalysis:
    """Analysis of coasting in a single corner."""
    name: str
    start_pct: float
    end_pct: float
    coasting_pct: float
    time_cost_sec: float
    zones: List[CoastingZone]
    primary_issue: str  # 'entry_hesitation', 'mid_searching', 'exit_late_throttle', 'clean'


def detect_corners(df: pd.DataFrame, min_corner_length: float = 0.05) -> List[Tuple[str, float, float]]:
    """
    Detect corners from telemetry data using lateral G-force and speed changes.
    
    Args:
        df: Telemetry dataframe
        min_corner_length: Minimum corner length as fraction of lap (0.05 = 5%)
    
    Returns:
        List of (corner_name, start_pct, end_pct) tuples
    """
    # Normalize column names (handle both TrackPct and LapDistPct)
    if 'LapDistPct' in df.columns and 'TrackPct' not in df.columns:
        df = df.rename(columns={'LapDistPct': 'TrackPct'})
    
    # For now, use a simple heuristic based on speed and lateral G
    # In future, could load corner definitions from track-specific config
    
    # Calculate rolling average lateral G (smoothed)
    if 'LatAccel' in df.columns:
        lat_g = df['LatAccel'].abs() / 9.81
        lat_g_smooth = lat_g.rolling(window=10, center=True).mean()
    else:
        # Fallback: use speed changes
        speed = df['Speed']
        speed_change = speed.diff().abs()
        lat_g_smooth = speed_change.rolling(window=10, center=True).mean()
        lat_g_smooth = lat_g_smooth / lat_g_smooth.max()  # Normalize
    
    # Detect corner zones where lateral G > threshold
    corner_threshold = 0.3  # 0.3g lateral
    in_corner = lat_g_smooth > corner_threshold
    
    # Find corner boundaries
    corners = []
    corner_start = None
    corner_num = 1
    
    for i, is_corner in enumerate(in_corner):
        track_pct = df['TrackPct'].iloc[i]
        
        if is_corner and corner_start is None:
            corner_start = track_pct
        elif not is_corner and corner_start is not None:
            corner_end = track_pct
            corner_length = corner_end - corner_start
            
            # Only add if long enough
            if corner_length >= min_corner_length:
                corners.append((f"T{corner_num}", corner_start, corner_end))
                corner_num += 1
            
            corner_start = None
    
    # Handle corner that wraps around lap end
    if corner_start is not None:
        corners.append((f"T{corner_num}", corner_start, 1.0))
    
    return corners


def classify_coasting_phase(zone_start: float, zone_end: float, 
                            corner_start: float, corner_end: float) -> str:
    """
    Classify where in the corner the coasting occurs.
    
    Args:
        zone_start, zone_end: Coasting zone boundaries
        corner_start, corner_end: Corner boundaries
    
    Returns:
        'entry', 'mid', 'exit', or 'transition'
    """
    corner_length = corner_end - corner_start
    zone_mid = (zone_start + zone_end) / 2
    
    # Relative position within corner (0 = entry, 1 = exit)
    if corner_length > 0:
        relative_pos = (zone_mid - corner_start) / corner_length
    else:
        relative_pos = 0.5
    
    if relative_pos < 0.3:
        return 'entry'
    elif relative_pos < 0.7:
        return 'mid'
    else:
        return 'exit'


def estimate_time_cost(duration_sec: float, avg_speed_loss: float) -> float:
    """
    Estimate time cost of coasting zone.
    
    Simplified model: time_cost ≈ duration × speed_loss_factor
    
    Args:
        duration_sec: Duration of coasting
        avg_speed_loss: Average speed loss during coasting (m/s)
    
    Returns:
        Estimated time cost in seconds
    """
    # Rough estimate: each m/s of speed loss costs ~0.01s per second of coasting
    # This is a simplified model; real impact depends on track, corner, etc.
    return duration_sec * avg_speed_loss * 0.01


def generate_recommendation(zone: CoastingZone) -> str:
    """
    Generate specific recommendation based on coasting zone analysis.
    
    Args:
        zone: CoastingZone object
    
    Returns:
        Actionable recommendation string
    """
    if zone.phase == 'entry':
        return f"Commit to turn-in earlier - you're hesitating before {zone.corner_name}"
    elif zone.phase == 'mid':
        return f"Trust the line through {zone.corner_name} - you're searching mid-corner"
    elif zone.phase == 'exit':
        return f"Apply throttle earlier at {zone.corner_name} exit - smooth and progressive"
    else:
        return f"Fill the transition gap - brake release to throttle application"


def analyze_coasting_zones(df: pd.DataFrame) -> Tuple[List[CoastingZone], List[CornerAnalysis]]:
    """
    Analyze coasting zones and provide detailed breakdown.
    
    Args:
        df: Telemetry dataframe
    
    Returns:
        (coasting_zones, corner_analyses)
    """
    # Normalize column names
    if 'LapDistPct' in df.columns and 'TrackPct' not in df.columns:
        df = df.rename(columns={'LapDistPct': 'TrackPct'})
    
    pedals_cfg = pedals()
    
    # Detect coasting zones
    coasting_mask = (
        (df['Throttle'] < pedals_cfg.throttle_on) & 
        (df['Brake'] < pedals_cfg.brake_on)
    )
    
    if 'LongAccel' in df.columns:
        coasting_mask &= df['LongAccel'].abs() < pedals_cfg.coast_long_accel
    
    # Detect corners
    corners = detect_corners(df)
    
    if not corners:
        # Fallback: treat whole lap as one "corner"
        corners = [("Full Lap", 0.0, 1.0)]
    
    # Find coasting zones
    zones = []
    in_coast = False
    coast_start_idx = None
    
    for i, is_coasting in enumerate(coasting_mask):
        if is_coasting and not in_coast:
            coast_start_idx = i
            in_coast = True
        elif not is_coasting and in_coast:
            coast_end_idx = i
            
            # Calculate zone properties
            zone_df = df.iloc[coast_start_idx:coast_end_idx]
            start_pct = df['TrackPct'].iloc[coast_start_idx]
            end_pct = df['TrackPct'].iloc[coast_end_idx]
            
            # Duration (assuming 60Hz sample rate)
            duration_sec = len(zone_df) / 60.0
            
            # Only include zones > 0.1s (filter noise)
            if duration_sec > 0.1:
                # Find which corner this zone belongs to
                zone_mid = (start_pct + end_pct) / 2
                corner_name = "Straight"
                corner_start = 0.0
                corner_end = 1.0
                
                for c_name, c_start, c_end in corners:
                    if c_start <= zone_mid <= c_end:
                        corner_name = c_name
                        corner_start = c_start
                        corner_end = c_end
                        break
                
                # Classify phase
                phase = classify_coasting_phase(start_pct, end_pct, corner_start, corner_end)
                
                # Estimate time cost
                if 'Speed' in df.columns and len(zone_df) > 1:
                    speed_before = df['Speed'].iloc[max(0, coast_start_idx - 5):coast_start_idx].mean()
                    speed_during = zone_df['Speed'].mean()
                    speed_loss = max(0, speed_before - speed_during)
                else:
                    speed_loss = 2.0  # Default estimate
                
                time_cost = estimate_time_cost(duration_sec, speed_loss)
                
                # Classify severity
                if time_cost > 0.05:
                    severity = 'severe'
                elif time_cost > 0.02:
                    severity = 'moderate'
                else:
                    severity = 'minor'
                
                zone = CoastingZone(
                    start_pct=start_pct,
                    end_pct=end_pct,
                    duration_sec=duration_sec,
                    time_cost_sec=time_cost,
                    corner_name=corner_name,
                    phase=phase,
                    severity=severity,
                    recommendation=""
                )
                
                zone.recommendation = generate_recommendation(zone)
                zones.append(zone)
            
            in_coast = False
    
    # Aggregate by corner
    corner_analyses = []
    for corner_name, corner_start, corner_end in corners:
        corner_zones = [z for z in zones if z.corner_name == corner_name]
        
        if corner_zones:
            total_coast_duration = sum(z.duration_sec for z in corner_zones)
            total_time_cost = sum(z.time_cost_sec for z in corner_zones)
            
            # Calculate coasting % for this corner
            corner_mask = (df['TrackPct'] >= corner_start) & (df['TrackPct'] <= corner_end)
            corner_df = df[corner_mask]
            
            if len(corner_df) > 0:
                corner_coast_mask = coasting_mask[corner_mask]
                coasting_pct = corner_coast_mask.sum() / len(corner_coast_mask) * 100
            else:
                coasting_pct = 0.0
            
            # Determine primary issue
            if not corner_zones:
                primary_issue = 'clean'
            else:
                # Find most common phase
                phases = [z.phase for z in corner_zones]
                most_common_phase = max(set(phases), key=phases.count)
                
                if most_common_phase == 'entry':
                    primary_issue = 'entry_hesitation'
                elif most_common_phase == 'mid':
                    primary_issue = 'mid_searching'
                elif most_common_phase == 'exit':
                    primary_issue = 'exit_late_throttle'
                else:
                    primary_issue = 'transition_gap'
            
            corner_analyses.append(CornerAnalysis(
                name=corner_name,
                start_pct=corner_start,
                end_pct=corner_end,
                coasting_pct=coasting_pct,
                time_cost_sec=total_time_cost,
                zones=corner_zones,
                primary_issue=primary_issue
            ))
        else:
            # Clean corner (no coasting)
            corner_analyses.append(CornerAnalysis(
                name=corner_name,
                start_pct=corner_start,
                end_pct=corner_end,
                coasting_pct=0.0,
                time_cost_sec=0.0,
                zones=[],
                primary_issue='clean'
            ))
    
    return zones, corner_analyses


def print_analysis_report(zones: List[CoastingZone], corner_analyses: List[CornerAnalysis],
                         total_coasting_pct: float, lap_time: float) -> None:
    """
    Print comprehensive coasting analysis report.
    
    Args:
        zones: List of coasting zones
        corner_analyses: List of corner analyses
        total_coasting_pct: Overall coasting percentage
        lap_time: Lap time in seconds
    """
    print("\n" + "="*70)
    print("COASTING IMPACT ANALYSIS")
    print("="*70)
    
    # Overall summary
    total_time_cost = sum(z.time_cost_sec for z in zones)
    
    print(f"\n📊 Overall Summary:")
    print(f"   Coasting: {total_coasting_pct:.1f}% of lap")
    print(f"   Estimated time cost: {total_time_cost:.3f}s")
    print(f"   Potential lap time: {lap_time - total_time_cost:.3f}s (−{total_time_cost:.3f}s)")
    print(f"   Number of coasting zones: {len(zones)}")
    
    # Corner breakdown
    print(f"\n🎯 Corner-by-Corner Breakdown:")
    print(f"   {'Corner':<10} {'Coasting %':<12} {'Time Cost':<12} {'Primary Issue'}")
    print(f"   {'-'*10} {'-'*12} {'-'*12} {'-'*30}")
    
    # Sort by time cost (highest first)
    sorted_corners = sorted(corner_analyses, key=lambda c: c.time_cost_sec, reverse=True)
    
    for corner in sorted_corners:
        issue_str = corner.primary_issue.replace('_', ' ').title()
        if corner.primary_issue == 'clean':
            issue_str = "✅ Clean"
        
        print(f"   {corner.name:<10} {corner.coasting_pct:>6.1f}%      "
              f"{corner.time_cost_sec:>6.3f}s      {issue_str}")
    
    # Top 3 priority zones
    severe_zones = [z for z in zones if z.severity in ['severe', 'moderate']]
    severe_zones.sort(key=lambda z: z.time_cost_sec, reverse=True)
    
    if severe_zones:
        print(f"\n🔥 Top Priority Zones (highest impact):")
        for i, zone in enumerate(severe_zones[:3], 1):
            print(f"\n   {i}. {zone.corner_name} {zone.phase}")
            print(f"      Time cost: {zone.time_cost_sec:.3f}s")
            print(f"      💡 {zone.recommendation}")
    else:
        print(f"\n✅ Excellent! No significant coasting zones detected.")
    
    # Progress indicators
    if total_coasting_pct < 2.0:
        print(f"\n🏆 Outstanding! Coasting under 2% - you're filling the transitions well.")
    elif total_coasting_pct < 5.0:
        print(f"\n👍 Good progress! Coasting under 5% - keep refining the priority zones.")
    elif total_coasting_pct < 10.0:
        print(f"\n📈 Making progress. Focus on eliminating the top 3 priority zones.")
    else:
        print(f"\n🎯 Significant opportunity here. Coasting elimination is your biggest unlock.")
    
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python tools/analyze_coasting.py <telemetry_file>")
        print("\nExample:")
        print("  python tools/analyze_coasting.py weeks/week01/events/06-2025-12-13-ai-race/telemetry.csv")
        sys.exit(1)
    
    telemetry_file = Path(sys.argv[1])
    
    if not telemetry_file.exists():
        print(f"❌ Error: File not found: {telemetry_file}")
        sys.exit(1)
    
    print(f"\n📊 Analyzing coasting in: {telemetry_file.name}")
    
    # Load telemetry
    df = pd.read_csv(telemetry_file)
    
    # Normalize column names
    if 'LapDistPct' in df.columns and 'TrackPct' not in df.columns:
        df = df.rename(columns={'LapDistPct': 'TrackPct'})
    
    # Calculate overall coasting %
    pedals_cfg = pedals()
    coasting_mask = (
        (df['Throttle'] < pedals_cfg.throttle_on) & 
        (df['Brake'] < pedals_cfg.brake_on)
    )
    if 'LongAccel' in df.columns:
        coasting_mask &= df['LongAccel'].abs() < pedals_cfg.coast_long_accel
    
    total_coasting_pct = coasting_mask.sum() / len(df) * 100
    
    # Get lap time (estimate from telemetry length and average speed)
    if 'Speed' in df.columns:
        avg_speed = df['Speed'].mean()
        # Rough estimate: lap_time ≈ samples / sample_rate
        lap_time = len(df) / 60.0  # Assuming 60Hz
    else:
        lap_time = 51.0  # Default estimate
    
    # Analyze
    zones, corner_analyses = analyze_coasting_zones(df)
    
    # Print report
    print_analysis_report(zones, corner_analyses, total_coasting_pct, lap_time)


if __name__ == "__main__":
    main()
