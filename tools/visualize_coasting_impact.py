#!/usr/bin/env python3
"""
Coasting Impact Visualization
==============================

Creates learning-focused visualizations that show WHERE coasting happens,
HOW MUCH it costs, and WHAT TO DO about it.

Generates:
- Hotspot map (track map with coasting zones sized by impact)
- Corner breakdown chart
- Time cost analysis
- Trend analysis (if multiple events provided)
- Priority recommendations

Usage:
    python tools/visualize_coasting_impact.py <telemetry_file> [output_file]
    python tools/visualize_coasting_impact.py weeks/week01/events/06-2025-12-13-ai-race/telemetry.csv

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from matplotlib.patches import Circle, Patch, FancyBboxPatch
from matplotlib.lines import Line2D
from analyze_coasting import analyze_coasting_zones, detect_corners
from config import pedals, COLORS


def create_coasting_impact_visualization(telemetry_file: Path, output_file: Path) -> None:
    """
    Create comprehensive coasting impact visualization.
    
    Args:
        telemetry_file: Path to telemetry CSV
        output_file: Path to save visualization
    """
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
    
    # Analyze coasting
    zones, corner_analyses = analyze_coasting_zones(df)
    
    # Set style
    sns.set_style("whitegrid")
    
    # Create figure
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Title
    total_time_cost = sum(z.time_cost_sec for z in zones)
    fig.suptitle(f"Coasting Impact Analysis - {telemetry_file.parent.name}", 
                fontsize=16, fontweight='bold')
    
    # 1. Track map with coasting hotspots (top left, 2x2)
    ax1 = fig.add_subplot(gs[0:2, 0:2])
    plot_hotspot_map(ax1, df, zones, coasting_mask)
    
    # 2. Corner breakdown chart (top right)
    ax2 = fig.add_subplot(gs[0, 2])
    plot_corner_breakdown(ax2, corner_analyses)
    
    # 3. Time cost analysis (middle right)
    ax3 = fig.add_subplot(gs[1, 2])
    plot_time_cost_analysis(ax3, zones, total_time_cost)
    
    # 4. Coasting phase distribution (bottom left)
    ax4 = fig.add_subplot(gs[2, 0])
    plot_phase_distribution(ax4, zones)
    
    # 5. Severity breakdown (bottom middle)
    ax5 = fig.add_subplot(gs[2, 1])
    plot_severity_breakdown(ax5, zones)
    
    # 6. Priority recommendations (bottom right)
    ax6 = fig.add_subplot(gs[2, 2])
    plot_priority_recommendations(ax6, zones, corner_analyses)
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualization saved to {output_file}")
    plt.close()


def plot_hotspot_map(ax, df: pd.DataFrame, zones, coasting_mask) -> None:
    """
    Plot track map with coasting zones sized by time cost impact.
    
    Args:
        ax: Matplotlib axis
        df: Telemetry dataframe
        zones: List of CoastingZone objects
        coasting_mask: Boolean array of coasting samples
    """
    ax.set_facecolor('#FAFAFA')
    
    # Plot track outline (all points, light gray)
    ax.plot(df['Lon'], df['Lat'], color='#E5E7EB', linewidth=8, alpha=0.5, zorder=1)
    
    # Plot coasting zones with size proportional to time cost
    if zones:
        for zone in zones:
            # Find samples in this zone
            zone_mask = (df['TrackPct'] >= zone.start_pct) & (df['TrackPct'] <= zone.end_pct)
            zone_df = df[zone_mask]
            
            if len(zone_df) > 0:
                # Color by severity
                if zone.severity == 'severe':
                    color = '#EF4444'  # Red
                    alpha = 0.9
                    linewidth = 6
                elif zone.severity == 'moderate':
                    color = '#F59E0B'  # Orange
                    alpha = 0.7
                    linewidth = 4
                else:
                    color = '#94A3B8'  # Gray
                    alpha = 0.5
                    linewidth = 2
                
                ax.plot(zone_df['Lon'], zone_df['Lat'], 
                       color=color, linewidth=linewidth, alpha=alpha, 
                       solid_capstyle='round', zorder=2)
    
    # Mark start/finish
    ax.scatter(df['Lon'].iloc[0], df['Lat'].iloc[0], 
              s=200, c='#10B981', marker='s', edgecolor='white', linewidth=2,
              zorder=10, label='Start/Finish')
    
    ax.set_aspect('equal')
    ax.set_title('Coasting Hotspot Map', fontsize=12, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Legend
    legend_elements = [
        Line2D([0], [0], color='#EF4444', linewidth=4, label='Severe (>0.05s)'),
        Line2D([0], [0], color='#F59E0B', linewidth=4, label='Moderate (>0.02s)'),
        Line2D([0], [0], color='#94A3B8', linewidth=4, label='Minor (<0.02s)'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.95)


def plot_corner_breakdown(ax, corner_analyses) -> None:
    """
    Plot bar chart of coasting % by corner.
    
    Args:
        ax: Matplotlib axis
        corner_analyses: List of CornerAnalysis objects
    """
    # Sort by coasting % (highest first)
    sorted_corners = sorted(corner_analyses, key=lambda c: c.coasting_pct, reverse=True)
    
    corner_names = [c.name for c in sorted_corners]
    coasting_pcts = [c.coasting_pct for c in sorted_corners]
    
    # Color by severity
    colors = []
    for pct in coasting_pcts:
        if pct > 15:
            colors.append('#EF4444')  # Red
        elif pct > 5:
            colors.append('#F59E0B')  # Orange
        elif pct > 0:
            colors.append('#94A3B8')  # Gray
        else:
            colors.append('#10B981')  # Green (clean)
    
    bars = ax.barh(corner_names, coasting_pcts, color=colors, alpha=0.8, edgecolor='black')
    
    ax.set_xlabel("Coasting %")
    ax.set_ylabel("Corner")
    ax.set_title("Coasting by Corner", fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, pct) in enumerate(zip(bars, coasting_pcts)):
        if pct > 0:
            ax.text(pct + 0.5, i, f'{pct:.1f}%', va='center', fontsize=8)


def plot_time_cost_analysis(ax, zones, total_time_cost: float) -> None:
    """
    Plot time cost breakdown by zone.
    
    Args:
        ax: Matplotlib axis
        zones: List of CoastingZone objects
        total_time_cost: Total estimated time cost
    """
    if not zones:
        ax.text(0.5, 0.5, "No coasting zones detected\n✅ Excellent!", 
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title("Time Cost Analysis", fontsize=11, fontweight='bold')
        ax.axis('off')
        return
    
    # Group by corner
    corner_costs = {}
    for zone in zones:
        if zone.corner_name not in corner_costs:
            corner_costs[zone.corner_name] = 0.0
        corner_costs[zone.corner_name] += zone.time_cost_sec
    
    # Sort by cost
    sorted_corners = sorted(corner_costs.items(), key=lambda x: x[1], reverse=True)
    corner_names = [c[0] for c in sorted_corners]
    costs = [c[1] for c in sorted_corners]
    
    # Color by cost
    colors = []
    for cost in costs:
        if cost > 0.05:
            colors.append('#EF4444')
        elif cost > 0.02:
            colors.append('#F59E0B')
        else:
            colors.append('#94A3B8')
    
    bars = ax.barh(corner_names, costs, color=colors, alpha=0.8, edgecolor='black')
    
    ax.set_xlabel("Time Cost (seconds)")
    ax.set_ylabel("Corner")
    ax.set_title(f"Time Cost by Corner (Total: {total_time_cost:.3f}s)", 
                fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, cost) in enumerate(zip(bars, costs)):
        ax.text(cost + 0.005, i, f'{cost:.3f}s', va='center', fontsize=8)


def plot_phase_distribution(ax, zones) -> None:
    """
    Plot pie chart of coasting by phase (entry/mid/exit).
    
    Args:
        ax: Matplotlib axis
        zones: List of CoastingZone objects
    """
    if not zones:
        ax.text(0.5, 0.5, "No coasting zones", ha='center', va='center', 
               transform=ax.transAxes, fontsize=12)
        ax.set_title("Coasting Phase Distribution", fontsize=11, fontweight='bold')
        ax.axis('off')
        return
    
    # Count by phase
    phase_counts = {}
    for zone in zones:
        phase = zone.phase.title()
        if phase not in phase_counts:
            phase_counts[phase] = 0
        phase_counts[phase] += zone.duration_sec
    
    phases = list(phase_counts.keys())
    durations = list(phase_counts.values())
    
    # Colors
    phase_colors = {
        'Entry': '#EF4444',
        'Mid': '#F59E0B',
        'Exit': '#10B981',
        'Transition': '#94A3B8'
    }
    colors = [phase_colors.get(p, '#94A3B8') for p in phases]
    
    ax.pie(durations, labels=phases, autopct='%1.1f%%', colors=colors, 
          startangle=90, textprops={'fontsize': 9})
    ax.set_title("Coasting Phase Distribution", fontsize=11, fontweight='bold')


def plot_severity_breakdown(ax, zones) -> None:
    """
    Plot bar chart of zones by severity.
    
    Args:
        ax: Matplotlib axis
        zones: List of CoastingZone objects
    """
    if not zones:
        ax.text(0.5, 0.5, "No coasting zones", ha='center', va='center', 
               transform=ax.transAxes, fontsize=12)
        ax.set_title("Severity Breakdown", fontsize=11, fontweight='bold')
        ax.axis('off')
        return
    
    # Count by severity
    severity_counts = {'Minor': 0, 'Moderate': 0, 'Severe': 0}
    for zone in zones:
        severity_counts[zone.severity.title()] += 1
    
    severities = list(severity_counts.keys())
    counts = list(severity_counts.values())
    
    colors = ['#94A3B8', '#F59E0B', '#EF4444']
    
    bars = ax.bar(severities, counts, color=colors, alpha=0.8, edgecolor='black')
    
    ax.set_ylabel("Number of Zones")
    ax.set_title("Severity Breakdown", fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(count)}', ha='center', va='bottom', fontsize=10)


def plot_priority_recommendations(ax, zones, corner_analyses) -> None:
    """
    Display top 3 priority recommendations.
    
    Args:
        ax: Matplotlib axis
        zones: List of CoastingZone objects
        corner_analyses: List of CornerAnalysis objects
    """
    ax.axis('off')
    ax.set_title("Priority Recommendations", fontsize=11, fontweight='bold', pad=10)
    
    # Get top 3 corners by time cost
    sorted_corners = sorted(corner_analyses, key=lambda c: c.time_cost_sec, reverse=True)
    top_corners = [c for c in sorted_corners if c.time_cost_sec > 0][:3]
    
    if not top_corners:
        ax.text(0.5, 0.5, "✅ No significant coasting!\nExcellent transition work.", 
               ha='center', va='center', transform=ax.transAxes, 
               fontsize=12, fontweight='bold', color='#10B981')
        return
    
    y_pos = 0.9
    for i, corner in enumerate(top_corners, 1):
        # Get the most significant zone in this corner
        corner_zones = [z for z in zones if z.corner_name == corner.name]
        if corner_zones:
            main_zone = max(corner_zones, key=lambda z: z.time_cost_sec)
            
            # Priority number
            ax.text(0.05, y_pos, f"{i}.", fontsize=14, fontweight='bold',
                   transform=ax.transAxes)
            
            # Corner and cost
            ax.text(0.15, y_pos, f"{corner.name} {main_zone.phase}", 
                   fontsize=11, fontweight='bold', transform=ax.transAxes)
            ax.text(0.15, y_pos - 0.06, f"Cost: {corner.time_cost_sec:.3f}s", 
                   fontsize=9, color='#6B7280', transform=ax.transAxes)
            
            # Recommendation (wrapped)
            recommendation = main_zone.recommendation
            if len(recommendation) > 50:
                # Simple word wrap
                words = recommendation.split()
                lines = []
                current_line = []
                for word in words:
                    current_line.append(word)
                    if len(' '.join(current_line)) > 45:
                        lines.append(' '.join(current_line))
                        current_line = []
                if current_line:
                    lines.append(' '.join(current_line))
                
                for j, line in enumerate(lines):
                    ax.text(0.15, y_pos - 0.12 - (j * 0.05), f"💡 {line}" if j == 0 else f"   {line}", 
                           fontsize=9, transform=ax.transAxes, style='italic')
            else:
                ax.text(0.15, y_pos - 0.12, f"💡 {recommendation}", 
                       fontsize=9, transform=ax.transAxes, style='italic')
            
            y_pos -= 0.28


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python tools/visualize_coasting_impact.py <telemetry_file> [output_file]")
        print("\nExample:")
        print("  python tools/visualize_coasting_impact.py weeks/week01/events/06-2025-12-13-ai-race/telemetry.csv")
        sys.exit(1)
    
    telemetry_file = Path(sys.argv[1])
    
    if not telemetry_file.exists():
        print(f"❌ Error: File not found: {telemetry_file}")
        sys.exit(1)
    
    # Determine output file
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = telemetry_file.parent / "coasting_impact.png"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 Creating coasting impact visualization...")
    print(f"   Input: {telemetry_file}")
    print(f"   Output: {output_file}")
    
    create_coasting_impact_visualization(telemetry_file, output_file)


if __name__ == "__main__":
    main()
