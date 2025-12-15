#!/usr/bin/env python3
"""
Week Progress Visualization Tool
Analyzes all events in a week directory and shows longitudinal progress.

Usage:
    uv run python tools/visualize_week.py results/week01/
    uv run python tools/visualize_week.py results/week01/ --output images/week01/week-progress.png
    uv run python tools/visualize_week.py results/week01/ --include-first-lap  # for rolling starts
"""

import argparse
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from data_loader import load_event_csv_with_metadata

# Configure seaborn style - thinner lines for readability
sns.set_theme(style="whitegrid", palette="husl", font_scale=1.0)
sns.set_context("notebook", rc={"lines.linewidth": 1.0})

# Custom color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'fastest': '#1B998B',
    'dirty': '#E94F37',
    'band_fill': '#86BA90',
    's1': '#2E86AB',
    's2': '#F18F01', 
    's3': '#1B998B',
}

# Event colors for progression
EVENT_COLORS = ['#E94F37', '#F6AE2D', '#33A1FD', '#1B998B', '#A23B72', '#2E86AB']


def is_telemetry_file(filename: str) -> bool:
    """Check if a CSV is single-lap telemetry (not event data)."""
    # Telemetry files have lap time pattern: 00.XX.XXX or 01.XX.XXX
    import re
    return bool(re.search(r' - 0[01]\.\d+\.\d+ - ', filename))


def load_week_events(week_dir: Path, exclude_first_lap: bool = True) -> list[tuple[pd.DataFrame, dict]]:
    """Load all event CSV files in a week directory, sorted by time.
    
    Args:
        week_dir: Directory containing event CSV files
        exclude_first_lap: Exclude lap 1 (standing start). Set False for rolling starts.
    """
    sessions = []
    
    # Filter out telemetry files (single-lap exports)
    # Use rglob to find CSVs in subdirectories (like data/processed/)
    csv_files = [f for f in sorted(week_dir.rglob("*.csv")) 
                 if not is_telemetry_file(f.name)]
    
    for csv_file in csv_files:
        df = load_event_csv_with_metadata(csv_file, exclude_first_lap=exclude_first_lap)
        
        if len(df) == 0:
            continue
        
        # Extract session info
        event_start = df['timestamp'].min()
        event_type = "Race" if "Race" in csv_file.name else "Practice"
        
        info = {
            'file': csv_file.name,
            'start_time': event_start,
            'type': event_type,
            'laps': len(df),
            'best': df['Lap time'].min(),
            'mean': df['Lap time'].mean(),
            'clean_pct': df['Clean'].mean() * 100 if 'Clean' in df.columns else 100,
        }
        
        # Calculate "settled" stats (last 60% of laps)
        settled_start = int(len(df) * 0.4)
        settled_df = df.iloc[settled_start:]
        info['settled_mean'] = settled_df['Lap time'].mean()
        info['settled_std'] = settled_df['Lap time'].std()
        
        # Sector bests if available
        if all(col in df.columns for col in ['Sector 1', 'Sector 2', 'Sector 3']):
            info['s1_best'] = df['Sector 1'].min()
            info['s2_best'] = df['Sector 2'].min()
            info['s3_best'] = df['Sector 3'].min()
            info['optimal'] = info['s1_best'] + info['s2_best'] + info['s3_best']
        
        sessions.append((df, info))
    
    # Sort by start time
    sessions.sort(key=lambda x: x[1]['start_time'])
    
    return sessions


def create_week_visualization(
    sessions: list[tuple[pd.DataFrame, dict]],
    title: str = "Week Progress",
    output_path: Path | None = None,
):
    """Create comprehensive week progress visualization."""
    
    n_events = len(sessions)
    if n_events == 0:
        print("❌ No events found!")
        return None
    
    # Create figure - dynamic width based on session count
    base_width = 14
    extra_width_per_session = 1.5 if n_events > 6 else 0
    fig_width = base_width + max(0, (n_events - 6)) * extra_width_per_session
    fig_width = min(fig_width, 24)  # Cap at reasonable max
    
    fig = plt.figure(figsize=(fig_width, 12))
    fig.patch.set_facecolor('#FAFAFA')
    
    # Rotation for x-labels when many sessions
    label_rotation = 45 if n_events > 6 else 0
    label_ha = 'right' if n_events > 6 else 'center'
    fig.suptitle(title, fontsize=18, fontweight='bold', color='#2C3E50', y=0.98)
    
    gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.25)
    
    # Prepare session labels (use # to avoid collision with S1/S2/S3 sectors)
    # Use shorter format for many sessions
    event_labels = []
    event_labels_short = []  # For cramped plots
    for i, (df, info) in enumerate(sessions):
        type_char = "AI" if info['type'] == 'Race' else "P"
        
        if n_events <= 6:
            # Full format for few sessions
            date_str = info['start_time'].strftime('%m/%d %H:%M')
            event_labels.append(f"#{i+1}\n{date_str}\n[{type_char}]")
        else:
            # Compact format for many sessions
            date_str = info['start_time'].strftime('%d/%H:%M')
            event_labels.append(f"#{i+1}\n{date_str}")
        
        # Always have a short version available
        event_labels_short.append(f"#{i+1}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 1: Best Lap Progress
    # ═══════════════════════════════════════════════════════════════════════════
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#FFFFFF')
    
    bests = [info['best'] for _, info in sessions]
    x_pos = range(n_events)
    
    bars = ax1.bar(x_pos, bests, color=[EVENT_COLORS[i % len(EVENT_COLORS)] for i in range(n_events)],
                   alpha=0.8, edgecolor='white', linewidth=1.5)
    
    # Add value labels
    for i, (bar, best) in enumerate(zip(bars, bests)):
        # Best lap time on top of bar
        fontsize = 9 if n_events <= 8 else 7
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{best:.3f}', ha='center', va='bottom', fontsize=fontsize)
        
        # Delta from previous event (inside bar, white text)
        if i > 0 and n_events <= 10:
            delta = bests[i] - bests[i-1]
            # Position inside the bar, near the bottom
            y_pos = bar.get_height() - 0.15
            ax1.text(bar.get_x() + bar.get_width()/2, y_pos,
                    f'{delta:+.3f}', ha='center', va='top', fontsize=8, 
                    fontweight='bold', color='white')
    
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(event_labels, fontsize=8, rotation=label_rotation, ha=label_ha)
    ax1.set_ylabel('Best Lap (s)', fontsize=11)
    ax1.set_title('Best Lap Progress', fontsize=12, fontweight='bold')
    ax1.set_ylim(min(bests) - 0.6, max(bests) + 0.5)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 2: Band Evolution (settled mean ± std)
    # ═══════════════════════════════════════════════════════════════════════════
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#FFFFFF')
    
    settled_means = [info['settled_mean'] for _, info in sessions]
    settled_stds = [info['settled_std'] for _, info in sessions]
    
    ax2.errorbar(x_pos, settled_means, yerr=settled_stds, fmt='o-', 
                color=COLORS['secondary'], linewidth=1.2, markersize=8,
                capsize=6, capthick=1.2, ecolor=COLORS['secondary'], alpha=0.8)
    
    # Fill band
    lower = [m - s for m, s in zip(settled_means, settled_stds)]
    upper = [m + s for m, s in zip(settled_means, settled_stds)]
    ax2.fill_between(x_pos, lower, upper, alpha=0.2, color=COLORS['band_fill'])
    
    # Add annotations below the error bars
    for i, (m, s) in enumerate(zip(settled_means, settled_stds)):
        ax2.annotate(f'σ={s:.2f}', xy=(i, m - s - 0.8), ha='center', fontsize=8,
                    color='#2C3E50', fontweight='medium',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white', 
                             edgecolor='none', alpha=0.9))
    
    # Expand y-axis to make room for labels below
    y_min = min(lower) - 1.5
    y_max = max(upper) + 0.5
    ax2.set_ylim(y_min, y_max)
    
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(event_labels, fontsize=8, rotation=label_rotation, ha=label_ha)
    ax2.set_ylabel('Settled Pace (s)', fontsize=11)
    ax2.set_title('Band Evolution (Mean ± Std)', fontsize=12, fontweight='bold')
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 3: Rhythm Discovery (Laps to Settle) - LINE CHART
    # ═══════════════════════════════════════════════════════════════════════════
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#FFFFFF')
    
    # Calculate settling metrics
    settling_data = []
    for i, (df, info) in enumerate(sessions):
        times = df['Lap time'].values
        settled_mean = info['settled_mean']
        settled_std = info['settled_std']
        
        # Find when driver "settled" (within 1σ of settled mean for 3+ consecutive laps)
        threshold = settled_mean + settled_std * 1.5
        laps_to_settle = 1
        for j in range(len(times) - 2):
            if all(t < threshold for t in times[j:j+3]):
                laps_to_settle = j + 1
                break
        else:
            laps_to_settle = len(times) // 2  # Default if never settled
        
        settling_data.append(laps_to_settle)

    # Plot line chart
    ax3.plot(x_pos, settling_data, 'o-', color=COLORS['accent'], linewidth=1.5, markersize=6)
    
    # Add labels
    for i, val in enumerate(settling_data):
        ax3.annotate(str(val), xy=(i, val), xytext=(0, 5), 
                    textcoords='offset points', ha='center', fontsize=8)

    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(event_labels_short, fontsize=9)
    ax3.set_ylabel('Laps to Settle', fontsize=11)
    ax3.set_title('Rhythm Discovery (Laps to settle)', fontsize=12, fontweight='bold')
    ax3.set_ylim(0, max(settling_data) * 1.2)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 4: Consistency Trend (Sigma) - LINE CHART
    # ═══════════════════════════════════════════════════════════════════════════
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#FFFFFF')
    
    sigmas = [info['settled_std'] for _, info in sessions]
    
    # Plot line chart for Sigma
    ax4.plot(x_pos, sigmas, 'o-', color=COLORS['secondary'], linewidth=1.5, markersize=6)
    ax4.fill_between(x_pos, 0, sigmas, alpha=0.1, color=COLORS['secondary'])
    
    # Add value labels
    for i, sigma in enumerate(sigmas):
        ax4.annotate(f'{sigma:.2f}s', xy=(i, sigma), xytext=(0, 5), 
                    textcoords='offset points', ha='center', fontsize=8)
    
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(event_labels_short, fontsize=9)
    ax4.set_ylabel('Consistency σ (s)', fontsize=11)
    ax4.set_title('Consistency Evolution (Lower is Better)', fontsize=12, fontweight='bold')
    ax4.set_ylim(0, max(sigmas) * 1.2)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 5: Sector Progress (if available)
    # ═══════════════════════════════════════════════════════════════════════════
    has_sectors = all('s1_best' in info for _, info in sessions)
    
    if has_sectors:
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.set_facecolor('#FFFFFF')
        
        # Calculate sector consistency (σ) for the last/most recent session
        # This tells driver WHERE to focus
        last_df = sessions[-1][0]
        s1_std = last_df['Sector 1'].std()
        s2_std = last_df['Sector 2'].std()
        s3_std = last_df['Sector 3'].std()
        
        s1_mean = last_df['Sector 1'].mean()
        s2_mean = last_df['Sector 2'].mean()
        s3_mean = last_df['Sector 3'].mean()
        
        s1_best = last_df['Sector 1'].min()
        s2_best = last_df['Sector 2'].min()
        s3_best = last_df['Sector 3'].min()
        
        sectors = ['S1\n(T1-esses)', 'S2\n(T6 pinch)', 'S3\n(carousel)']
        sector_stds = [s1_std, s2_std, s3_std]
        sector_means = [s1_mean, s2_mean, s3_mean]
        sector_bests = [s1_best, s2_best, s3_best]
        sector_colors = [COLORS['s1'], COLORS['s2'], COLORS['s3']]
        
        # Bar chart of sector σ (consistency)
        bars = ax5.bar(sectors, sector_stds, color=sector_colors, alpha=0.7, edgecolor='white', linewidth=1.5)
        
        # Add annotations
        for i, (bar, std, mean, best) in enumerate(zip(bars, sector_stds, sector_means, sector_bests)):
            label = f'σ={std:.2f}s\nbest={best:.2f}s'
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    label, ha='center', va='bottom', fontsize=8)
        
        ax5.set_ylabel('Sector Consistency (σ in seconds)', fontsize=11)
        ax5.set_title('Sector Consistency (Latest Event)', fontsize=12, fontweight='bold')
        ax5.set_ylim(0, max(sector_stds) * 1.5)
        
        # PLOT 6: Optimal vs Actual
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.set_facecolor('#FFFFFF')
        
        optimals = [info['optimal'] for _, info in sessions]
        
        ax6.plot(x_pos, bests, 'o-', color=COLORS['primary'], linewidth=1.2, 
                markersize=7, label='Actual Best')
        ax6.plot(x_pos, optimals, 's--', color=COLORS['fastest'], linewidth=1.2,
                markersize=6, label='Theoretical Optimal')
        
        # Gap annotations
        for i, (actual, optimal) in enumerate(zip(bests, optimals)):
            gap = actual - optimal
            ax6.annotate(f'Gap: {gap:.3f}s', xy=(i, (actual + optimal)/2),
                        ha='center', fontsize=8, color=COLORS['secondary'],
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        
        ax6.set_xticks(x_pos)
        ax6.set_xticklabels(event_labels_short, fontsize=9)
        ax6.set_ylabel('Lap Time (s)', fontsize=11)
        ax6.set_title('Actual vs Optimal', fontsize=12, fontweight='bold')
        ax6.legend(loc='upper right', fontsize=9, framealpha=0.95)
    
    else:
        # If no sectors, show consistency metrics instead
        ax5 = fig.add_subplot(gs[2, :])
        ax5.set_facecolor('#FFFFFF')
        
        # Clean lap percentage
        clean_pcts = [info['clean_pct'] for _, info in sessions]
        lap_counts = [info['laps'] for _, info in sessions]
        
        ax5_twin = ax5.twinx()
        
        bars = ax5.bar(x_pos, clean_pcts, color=COLORS['fastest'], alpha=0.6, label='Clean %')
        ax5_twin.plot(x_pos, lap_counts, 'o-', color=COLORS['secondary'], 
            linewidth=1.2, markersize=7, label='Lap Count')
        
        ax5.set_xticks(x_pos)
        ax5.set_xticklabels(event_labels, fontsize=8, rotation=label_rotation, ha=label_ha)
        ax5.set_ylabel('Clean Lap %', fontsize=11, color=COLORS['fastest'])
        ax5_twin.set_ylabel('Lap Count', fontsize=11, color=COLORS['secondary'])
        ax5.set_title('Event Quality Metrics', fontsize=12, fontweight='bold')
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Finalize
    # ═══════════════════════════════════════════════════════════════════════════
    plt.subplots_adjust(top=0.93, hspace=0.4, wspace=0.25)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
            facecolor='#FAFAFA', edgecolor='none')
        print(f"✅ Saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("WEEK PROGRESS SUMMARY")
    print("="*70)
    
    print(f"\n{'Event':<10} {'Date/Time':<18} {'Type':<10} {'Laps':<6} {'Best':<10} {'Settled':<12} {'σ':<8}")
    print("-"*70)
    
    for i, (df, info) in enumerate(sessions):
        date_str = info['start_time'].strftime('%Y-%m-%d %H:%M')
        print(f"#{i+1:<9} {date_str:<18} {info['type']:<10} {info['laps']:<6} "
            f"{info['best']:.3f}s | {info['settled_mean']:.3f}s | {info['settled_std']:.3f}s")
    
    # Progress summary
    print("\n" + "-"*70)
    first_best = sessions[0][1]['best']
    last_best = sessions[-1][1]['best']
    improvement = first_best - last_best
    print(f"Best lap improvement: {first_best:.3f}s → {last_best:.3f}s = {improvement:+.3f}s 🎯")
    
    first_std = sessions[0][1]['settled_std']
    last_std = sessions[-1][1]['settled_std']
    std_change = first_std - last_std
    print(f"Consistency improvement: σ {first_std:.3f}s → σ {last_std:.3f}s = {std_change:+.3f}s tighter")
    
    if has_sectors:
        print(f"\nBest theoretical optimal: {min(optimals):.3f}s")
        print(f"Gap to optimal (last session): {bests[-1] - optimals[-1]:.3f}s")
    
    return fig


def main():
    parser = argparse.ArgumentParser(description="Visualize week progress from Garage 61 CSVs")
    parser.add_argument("week_dir", type=Path, help="Path to week directory with CSV files")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")
    parser.add_argument("--title", "-t", type=str, help="Custom title")
    parser.add_argument("--include-first-lap", action="store_true",
        help="Include lap 1 in analysis (use for rolling starts)")
    
    args = parser.parse_args()
    
    if not args.week_dir.exists():
        print(f"❌ Directory not found: {args.week_dir}")
        return 1
    
    # Load all sessions (exclude first lap by default for standing starts)
    exclude_first = not args.include_first_lap
    print(f"Loading events from {args.week_dir}...")
    events = load_week_events(args.week_dir, exclude_first_lap=exclude_first)
    print(f"Found {len(events)} events" + (" (excluding lap 1)" if exclude_first else ""))
    
    if len(events) == 0:
        print("❌ No valid CSV files found!")
        return 1
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # New structure: weeks/weekXX/data/ → weeks/weekXX/images/
        output_path = args.week_dir.parent / "images" / "week-progress.png"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate title
    if args.title:
        title = args.title
    else:
        week_name = args.week_dir.name
        n_events = len(events)
        first_date = events[0][1]['start_time'].strftime('%Y-%m-%d')
        last_date = events[-1][1]['start_time'].strftime('%Y-%m-%d')
        title = f"{week_name.upper()} Progress – {n_events} Events\n{first_date} → {last_date}"
    
    # Create visualization
    create_week_visualization(events, title=title, output_path=output_path)
    
    return 0


if __name__ == "__main__":
    exit(main())

