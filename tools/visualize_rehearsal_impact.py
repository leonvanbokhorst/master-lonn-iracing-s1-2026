#!/usr/bin/env python3
"""
Mental Rehearsal Impact Visualization
======================================

Analyzes and visualizes the correlation between mental rehearsal practice
and performance outcomes across events.

Generates visualizations showing:
- Performance comparison: rehearsal vs. no rehearsal
- Confidence ratings vs. actual performance
- Rehearsal frequency over time
- Correlation analysis

Usage:
    python tools/visualize_rehearsal_impact.py <week_dir> [output_file]

Example:
    python tools/visualize_rehearsal_impact.py weeks/week02
    python tools/visualize_rehearsal_impact.py weeks/week02 analysis/rehearsal_impact.png

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from frontmatter_utils import list_event_files, parse_event_file


def extract_rehearsal_data(week_dir: Path) -> dict:
    """
    Extract mental rehearsal data from all events in a week.
    
    Args:
        week_dir: Path to week directory
    
    Returns:
        Dictionary with extracted data for analysis
    """
    events = list_event_files(week_dir)
    
    data = {
        "event_numbers": [],
        "event_names": [],
        "has_pre_rehearsal": [],
        "has_post_replay": [],
        "confidence_ratings": [],
        "clarity_ratings": [],
        "rehearsal_durations": [],
        "best_laps": [],
        "avg_laps": [],
        "incidents": [],
        "dates": []
    }
    
    for event_file in events:
        frontmatter, body = parse_event_file(event_file)
        
        event_num = frontmatter.get("event", 0)
        data["event_numbers"].append(event_num)
        data["event_names"].append(event_file.stem)
        data["dates"].append(frontmatter.get("date", ""))
        
        # Mental rehearsal data
        rehearsal = frontmatter.get("mental_rehearsal", {})
        
        has_pre = rehearsal.get("pre_session", False)
        has_post = rehearsal.get("post_session", False)
        
        data["has_pre_rehearsal"].append(has_pre)
        data["has_post_replay"].append(has_post)
        
        # Ratings
        confidence = rehearsal.get("confidence_rating") if has_pre else None
        clarity = rehearsal.get("clarity_rating") if has_post else None
        
        data["confidence_ratings"].append(confidence)
        data["clarity_ratings"].append(clarity)
        
        # Duration (pre-session if available, otherwise post-session)
        duration = None
        if has_pre:
            duration = rehearsal.get("duration_minutes")
        elif has_post:
            duration = rehearsal.get("duration_minutes")
        
        data["rehearsal_durations"].append(duration)
        
        # Performance data from body (parse markdown tables if available)
        # For now, we'll extract from summary if present
        best_lap, avg_lap, incidents = extract_performance_from_body(body)
        
        data["best_laps"].append(best_lap)
        data["avg_laps"].append(avg_lap)
        data["incidents"].append(incidents)
    
    return data


def extract_performance_from_body(body: str) -> tuple:
    """
    Extract performance metrics from event body text.
    
    Args:
        body: Event markdown body content
    
    Returns:
        Tuple of (best_lap, avg_lap, incidents)
    """
    # Simple extraction - look for common patterns
    # This is a basic implementation; could be enhanced
    
    best_lap = None
    avg_lap = None
    incidents = None
    
    lines = body.split("\n")
    
    for line in lines:
        line_lower = line.lower()
        
        # Look for best lap
        if "best lap" in line_lower or "fastest lap" in line_lower:
            # Try to extract time (format: 1:23.456)
            import re
            match = re.search(r'(\d+):(\d+\.\d+)', line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                best_lap = minutes * 60 + seconds
        
        # Look for average lap
        if "average lap" in line_lower or "avg lap" in line_lower:
            import re
            match = re.search(r'(\d+):(\d+\.\d+)', line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                avg_lap = minutes * 60 + seconds
        
        # Look for incidents
        if "incident" in line_lower:
            import re
            match = re.search(r'(\d+)', line)
            if match:
                incidents = int(match.group(1))
    
    return best_lap, avg_lap, incidents


def visualize_rehearsal_impact(data: dict, output_file: Path = None):
    """
    Create comprehensive visualization of mental rehearsal impact.
    
    Args:
        data: Extracted rehearsal and performance data
        output_file: Optional path to save figure
    """
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (16, 10)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("Mental Rehearsal Impact Analysis", fontsize=16, fontweight='bold')
    
    # 1. Rehearsal frequency over time
    ax1 = axes[0, 0]
    event_nums = data["event_numbers"]
    pre_counts = np.cumsum(data["has_pre_rehearsal"])
    post_counts = np.cumsum(data["has_post_replay"])
    
    ax1.plot(event_nums, pre_counts, marker='o', label='Pre-session rehearsal', linewidth=2)
    ax1.plot(event_nums, post_counts, marker='s', label='Post-session replay', linewidth=2)
    ax1.set_xlabel("Event Number")
    ax1.set_ylabel("Cumulative Count")
    ax1.set_title("Mental Rehearsal Practice Over Time")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Rehearsal adoption rate
    ax2 = axes[0, 1]
    total_events = len(event_nums)
    pre_rate = sum(data["has_pre_rehearsal"]) / total_events * 100 if total_events > 0 else 0
    post_rate = sum(data["has_post_replay"]) / total_events * 100 if total_events > 0 else 0
    
    categories = ['Pre-session\nRehearsal', 'Post-session\nReplay']
    rates = [pre_rate, post_rate]
    colors = ['#2ecc71', '#3498db']
    
    bars = ax2.bar(categories, rates, color=colors, alpha=0.7, edgecolor='black')
    ax2.set_ylabel("Adoption Rate (%)")
    ax2.set_title("Mental Rehearsal Adoption Rate")
    ax2.set_ylim(0, 100)
    
    # Add percentage labels on bars
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontweight='bold')
    
    # 3. Confidence ratings distribution
    ax3 = axes[0, 2]
    confidence_vals = [c for c in data["confidence_ratings"] if c is not None]
    
    if confidence_vals:
        bins = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        ax3.hist(confidence_vals, bins=bins, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax3.set_xlabel("Confidence Rating")
        ax3.set_ylabel("Frequency")
        ax3.set_title("Pre-Session Confidence Distribution")
        ax3.set_xticks([1, 2, 3, 4, 5])
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add mean line
        mean_conf = np.mean(confidence_vals)
        ax3.axvline(mean_conf, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_conf:.2f}')
        ax3.legend()
    else:
        ax3.text(0.5, 0.5, "No confidence data available", 
                ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title("Pre-Session Confidence Distribution")
    
    # 4. Performance comparison: rehearsal vs. no rehearsal
    ax4 = axes[1, 0]
    
    # Group events by whether they had pre-session rehearsal
    with_rehearsal_laps = []
    without_rehearsal_laps = []
    
    for i, has_pre in enumerate(data["has_pre_rehearsal"]):
        best_lap = data["best_laps"][i]
        if best_lap is not None:
            if has_pre:
                with_rehearsal_laps.append(best_lap)
            else:
                without_rehearsal_laps.append(best_lap)
    
    if with_rehearsal_laps and without_rehearsal_laps:
        box_data = [without_rehearsal_laps, with_rehearsal_laps]
        bp = ax4.boxplot(box_data, labels=['No Rehearsal', 'With Rehearsal'],
                        patch_artist=True, widths=0.6)
        
        # Color the boxes
        bp['boxes'][0].set_facecolor('#e74c3c')
        bp['boxes'][1].set_facecolor('#2ecc71')
        
        for box in bp['boxes']:
            box.set_alpha(0.7)
        
        ax4.set_ylabel("Best Lap Time (seconds)")
        ax4.set_title("Performance: Rehearsal vs. No Rehearsal")
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add mean values as text
        mean_without = np.mean(without_rehearsal_laps)
        mean_with = np.mean(with_rehearsal_laps)
        improvement = ((mean_without - mean_with) / mean_without) * 100
        
        ax4.text(0.5, 0.02, f"Improvement: {improvement:+.2f}%",
                transform=ax4.transAxes, ha='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        ax4.text(0.5, 0.5, "Insufficient data for comparison\n(need events with and without rehearsal)",
                ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title("Performance: Rehearsal vs. No Rehearsal")
    
    # 5. Confidence vs. Performance correlation
    ax5 = axes[1, 1]
    
    conf_perf_pairs = []
    for i, conf in enumerate(data["confidence_ratings"]):
        best_lap = data["best_laps"][i]
        if conf is not None and best_lap is not None:
            conf_perf_pairs.append((conf, best_lap))
    
    if len(conf_perf_pairs) >= 3:
        confs, laps = zip(*conf_perf_pairs)
        ax5.scatter(confs, laps, s=100, alpha=0.6, color='#e67e22', edgecolors='black')
        
        # Add trend line
        z = np.polyfit(confs, laps, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(confs), max(confs), 100)
        ax5.plot(x_trend, p(x_trend), "r--", linewidth=2, alpha=0.8, label='Trend')
        
        # Calculate correlation
        correlation = np.corrcoef(confs, laps)[0, 1]
        
        ax5.set_xlabel("Pre-Session Confidence Rating")
        ax5.set_ylabel("Best Lap Time (seconds)")
        ax5.set_title("Confidence vs. Performance")
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        ax5.text(0.05, 0.95, f"Correlation: {correlation:.3f}",
                transform=ax5.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    else:
        ax5.text(0.5, 0.5, "Insufficient data for correlation\n(need 3+ events with confidence and performance)",
                ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title("Confidence vs. Performance")
    
    # 6. Rehearsal duration distribution
    ax6 = axes[1, 2]
    
    durations = [d for d in data["rehearsal_durations"] if d is not None]
    
    if durations:
        ax6.hist(durations, bins=range(0, max(durations)+2), 
                color='#1abc9c', alpha=0.7, edgecolor='black')
        ax6.set_xlabel("Duration (minutes)")
        ax6.set_ylabel("Frequency")
        ax6.set_title("Mental Rehearsal Duration Distribution")
        ax6.grid(True, alpha=0.3, axis='y')
        
        # Add mean line
        mean_dur = np.mean(durations)
        ax6.axvline(mean_dur, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_dur:.1f} min')
        ax6.legend()
    else:
        ax6.text(0.5, 0.5, "No duration data available",
                ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title("Mental Rehearsal Duration Distribution")
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✅ Visualization saved to {output_file}")
    else:
        plt.savefig(week_dir / "images" / "mental_rehearsal_impact.png", dpi=300, bbox_inches='tight')
        print(f"\n✅ Visualization saved to {week_dir / 'images' / 'mental_rehearsal_impact.png'}")
    
    plt.close()


def print_summary_statistics(data: dict):
    """
    Print summary statistics about mental rehearsal practice.
    
    Args:
        data: Extracted rehearsal and performance data
    """
    total_events = len(data["event_numbers"])
    pre_count = sum(data["has_pre_rehearsal"])
    post_count = sum(data["has_post_replay"])
    
    print("\n" + "="*70)
    print("MENTAL REHEARSAL SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total events: {total_events}")
    print(f"  Events with pre-session rehearsal: {pre_count} ({pre_count/total_events*100:.1f}%)")
    print(f"  Events with post-session replay: {post_count} ({post_count/total_events*100:.1f}%)")
    
    # Confidence statistics
    confidence_vals = [c for c in data["confidence_ratings"] if c is not None]
    if confidence_vals:
        print(f"\n📈 Confidence Ratings:")
        print(f"  Mean: {np.mean(confidence_vals):.2f}")
        print(f"  Std Dev: {np.std(confidence_vals):.2f}")
        print(f"  Range: {min(confidence_vals)} - {max(confidence_vals)}")
    
    # Duration statistics
    durations = [d for d in data["rehearsal_durations"] if d is not None]
    if durations:
        print(f"\n⏱️  Rehearsal Duration:")
        print(f"  Mean: {np.mean(durations):.1f} minutes")
        print(f"  Std Dev: {np.std(durations):.1f} minutes")
        print(f"  Range: {min(durations)} - {max(durations)} minutes")
    
    # Performance comparison
    with_rehearsal_laps = []
    without_rehearsal_laps = []
    
    for i, has_pre in enumerate(data["has_pre_rehearsal"]):
        best_lap = data["best_laps"][i]
        if best_lap is not None:
            if has_pre:
                with_rehearsal_laps.append(best_lap)
            else:
                without_rehearsal_laps.append(best_lap)
    
    if with_rehearsal_laps and without_rehearsal_laps:
        mean_with = np.mean(with_rehearsal_laps)
        mean_without = np.mean(without_rehearsal_laps)
        improvement = ((mean_without - mean_with) / mean_without) * 100
        
        print(f"\n🏁 Performance Impact:")
        print(f"  Mean lap time without rehearsal: {mean_without:.3f}s")
        print(f"  Mean lap time with rehearsal: {mean_with:.3f}s")
        print(f"  Improvement: {improvement:+.2f}%")
    
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("""
Mental Rehearsal Impact Visualization
======================================

Usage:
    python tools/visualize_rehearsal_impact.py <week_dir> [output_file]

Examples:
    python tools/visualize_rehearsal_impact.py weeks/week02
    python tools/visualize_rehearsal_impact.py weeks/week02 analysis/rehearsal.png
""")
        sys.exit(1)
    
    week_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not week_dir.exists():
        print(f"❌ Error: Week directory not found: {week_dir}")
        sys.exit(1)
    
    # Ensure images directory exists
    images_dir = week_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    print(f"\n📊 Analyzing mental rehearsal data from {week_dir}...")
    
    # Extract data
    data = extract_rehearsal_data(week_dir)
    
    # Print summary statistics
    print_summary_statistics(data)
    
    # Create visualization
    visualize_rehearsal_impact(data, output_file)


if __name__ == "__main__":
    main()
