#!/usr/bin/env python3
"""
Event Visualization Tool
Reads Garage 61 CSV exports and creates meaningful visualizations.

Usage:
    uv run python tools/visualize_event.py results/your-event.csv
    uv run python tools/visualize_event.py results/your-event.csv --output images/week01/
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Configure seaborn style - light and fancy
sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)
sns.set_context("notebook", rc={"lines.linewidth": 1.5})

# Custom color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'fastest': '#1B998B',
    'dirty': '#E94F37',
    'early': '#E94F37',
    'middle': '#F6AE2D',
    'main': '#33A1FD',
    'band': '#86BA90',
    's1': '#2E86AB',
    's2': '#F18F01',
    's3': '#1B998B',
}


def load_event_csv(csv_path: Path, min_lap_time: float = 48.0, max_lap_time: float = 90.0) -> pd.DataFrame:
    """Load and clean a Garage 61 CSV export.
    
    Args:
        csv_path: Path to CSV file
        min_lap_time: Minimum valid lap time (filters incomplete laps)
        max_lap_time: Maximum valid lap time (filters pit/reset laps)
    """
    df = pd.read_csv(csv_path)
    
    # Clean column names (strip whitespace)
    df.columns = df.columns.str.strip()
    
    # Filter out incomplete laps and obvious outliers
    df = df[df['Lap'] > 0].copy()
    df = df[(df['Lap time'] >= min_lap_time) & (df['Lap time'] <= max_lap_time)].copy()
    
    # Parse timestamp
    if 'Started at' in df.columns:
        df['timestamp'] = pd.to_datetime(df['Started at'])
    
    # Convert sector times to float, handling any issues
    for sector in ['Sector 1', 'Sector 2', 'Sector 3']:
        if sector in df.columns:
            df[sector] = pd.to_numeric(df[sector], errors='coerce')
    
    return df


def detect_phases(lap_times: np.ndarray, threshold_pct: float = 0.03) -> tuple[int, int]:
    """
    Auto-detect race phases based on pace stabilization.
    Returns (early_end, middle_end) lap indices.
    """
    n = len(lap_times)
    if n < 10:
        return (n // 3, 2 * n // 3)
    
    # Find where pace starts stabilizing (rolling std drops)
    window = min(5, n // 3)
    rolling_std = pd.Series(lap_times).rolling(window).std()
    
    # Early phase ends when std drops below threshold
    median_time = np.median(lap_times)
    threshold = median_time * threshold_pct
    
    early_end = 0
    for i in range(window, n):
        if rolling_std.iloc[i] < threshold:
            early_end = i - window // 2
            break
    
    if early_end == 0:
        early_end = n // 3
    
    # Middle phase: find where we're consistently near the median
    middle_end = early_end
    for i in range(early_end, n):
        recent_avg = np.mean(lap_times[max(0, i-3):i+1])
        if recent_avg < median_time * 1.02:  # Within 2% of median
            middle_end = i
            break
    
    if middle_end <= early_end:
        middle_end = min(early_end + (n - early_end) // 2, n - 1)
    
    return (early_end, middle_end)


def create_event_visualization(
    df: pd.DataFrame,
    title: str = "Event Analysis",
    output_path: Path | None = None,
    phase_boundaries: tuple[int, int] | None = None,
):
    """Create comprehensive session visualization from Garage 61 CSV data."""
    
    laps = df['Lap'].values
    times = df['Lap time'].values
    clean = df['Clean'].values if 'Clean' in df.columns else np.ones(len(laps))
    
    # Auto-detect phases if not provided
    if phase_boundaries is None:
        phase_boundaries = detect_phases(times)
    
    early_end, middle_end = phase_boundaries
    
    # Find fastest and dirty laps
    fastest_idx = np.argmin(times)
    fastest_lap = laps[fastest_idx]
    dirty_laps = laps[clean == 0].tolist()
    
    # Check if we have sector data
    has_sectors = all(col in df.columns for col in ['Sector 1', 'Sector 2', 'Sector 3'])
    
    # Create figure
    n_rows = 3 if has_sectors else 2
    fig = plt.figure(figsize=(14, 4 * n_rows + 1))
    fig.patch.set_facecolor('#FAFAFA')
    fig.suptitle(title, fontsize=18, fontweight='bold', color='#2C3E50', y=0.99)
    
    gs = fig.add_gridspec(n_rows, 2, hspace=0.35, wspace=0.25)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 1: Lap progression with phases
    # ═══════════════════════════════════════════════════════════════════════════
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#FFFFFF')
    
    # Phase backgrounds
    ax1.axvspan(laps[0], laps[min(early_end, len(laps)-1)], alpha=0.2, color=COLORS['early'], label='Early')
    ax1.axvspan(laps[min(early_end, len(laps)-1)], laps[min(middle_end, len(laps)-1)], alpha=0.2, color=COLORS['middle'], label='Middle')
    ax1.axvspan(laps[min(middle_end, len(laps)-1)], laps[-1] + 0.5, alpha=0.2, color=COLORS['main'], label='Main')
    
    # Plot lap times
    ax1.plot(laps, times, 'o-', color=COLORS['primary'], linewidth=1.2, 
             markersize=6, markerfacecolor='white', markeredgewidth=1.5, alpha=0.9)
    
    # Highlight fastest lap (subtle)
    ax1.scatter([fastest_lap], [times[fastest_idx]], color=COLORS['fastest'], 
               s=80, zorder=5, marker='*', label=f'Fastest: {times[fastest_idx]:.3f}s')
    
    # Highlight dirty/off-track laps (subtle)
    for lap in dirty_laps:
        idx = np.where(laps == lap)[0]
        if len(idx) > 0:
            ax1.scatter([lap], [times[idx[0]]], color=COLORS['dirty'], s=35, 
                       zorder=4, marker='x', linewidths=1.5, alpha=0.7)
    
    ax1.set_xlabel('Lap', fontsize=11)
    ax1.set_ylabel('Lap Time (s)', fontsize=11)
    ax1.set_title('Lap Progression', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8, framealpha=0.95)
    
    y_min, y_max = min(times) - 0.5, max(times) + 0.5
    ax1.set_ylim(y_min, y_max)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 2: Rolling average trend
    # ═══════════════════════════════════════════════════════════════════════════
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#FFFFFF')
    
    window_3 = np.convolve(times, np.ones(3)/3, mode='valid')
    window_5 = np.convolve(times, np.ones(5)/5, mode='valid')
    
    ax2.scatter(laps, times, color=COLORS['primary'], alpha=0.4, s=30, label='Individual')
    ax2.plot(laps[1:-1], window_3, '-', color=COLORS['accent'], linewidth=1.5, label='3-lap avg')
    ax2.plot(laps[2:-2], window_5, '-', color=COLORS['fastest'], linewidth=1.8, label='5-lap avg')
    
    # Settled average line
    if middle_end < len(times):
        settled_times = times[middle_end:]
        settled_mean = np.mean(settled_times)
        ax2.axhline(settled_mean, color=COLORS['secondary'], linestyle='--', linewidth=1.2, 
                    alpha=0.7, label=f'Settled: {settled_mean:.2f}s')
    
    ax2.set_xlabel('Lap', fontsize=11)
    ax2.set_ylabel('Lap Time (s)', fontsize=11)
    ax2.set_title('Pace Trend', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8, framealpha=0.95)
    ax2.set_ylim(y_min, y_max)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 3: Distribution
    # ═══════════════════════════════════════════════════════════════════════════
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#FFFFFF')
    
    sns.histplot(times, bins=15, kde=True, color=COLORS['primary'], 
                 alpha=0.6, edgecolor='white', linewidth=0.8, ax=ax3)
    
    mean_val = np.mean(times)
    median_val = np.median(times)
    ax3.axvline(mean_val, color=COLORS['dirty'], linestyle='--', linewidth=1.5, 
                label=f'Mean: {mean_val:.2f}s')
    ax3.axvline(median_val, color=COLORS['fastest'], linestyle=':', linewidth=1.5, 
                label=f'Median: {median_val:.2f}s')
    
    ax3.set_xlabel('Lap Time (s)', fontsize=11)
    ax3.set_ylabel('Frequency', fontsize=11)
    ax3.set_title('Lap Time Distribution', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9, framealpha=0.95)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 4: Phase comparison
    # ═══════════════════════════════════════════════════════════════════════════
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#FFFFFF')
    
    early_times = times[:early_end] if early_end > 0 else times[:1]
    middle_times = times[early_end:middle_end] if middle_end > early_end else times[early_end:early_end+1]
    main_times = times[middle_end:] if middle_end < len(times) else times[-1:]
    
    phase_df = pd.DataFrame({
        'Lap Time': list(early_times) + list(middle_times) + list(main_times),
        'Phase': (['Early'] * len(early_times) + 
                  ['Middle'] * len(middle_times) + 
                  ['Main'] * len(main_times))
    })
    
    sns.violinplot(data=phase_df, x='Phase', y='Lap Time', hue='Phase',
                   palette=[COLORS['early'], COLORS['middle'], COLORS['main']], 
                   alpha=0.6, inner=None, legend=False, ax=ax4)
    sns.stripplot(data=phase_df, x='Phase', y='Lap Time', color='#2C3E50', 
                  alpha=0.7, size=5, jitter=0.15, legend=False, ax=ax4)
    
    # Add stats
    for i, (data, name) in enumerate(zip([early_times, middle_times, main_times], ['Early', 'Middle', 'Main'])):
        if len(data) > 0:
            mean = np.mean(data)
            std = np.std(data)
            ax4.annotate(f'μ={mean:.2f}s\nσ={std:.2f}s', 
                        xy=(i, max(data) + 0.5),
                        ha='center', fontsize=8, color='#2C3E50',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                                 edgecolor='#DDD', alpha=0.9))
    
    ax4.set_xlabel('', fontsize=11)
    ax4.set_ylabel('Lap Time (s)', fontsize=11)
    ax4.set_title('Phase Comparison', fontsize=12, fontweight='bold')
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 5 & 6: Sector Analysis (if available)
    # ═══════════════════════════════════════════════════════════════════════════
    if has_sectors:
        # Sector delta from best - all on same scale for comparison
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.set_facecolor('#FFFFFF')
        
        # Calculate delta from best for each sector
        s1_best = df['Sector 1'].min()
        s2_best = df['Sector 2'].min()
        s3_best = df['Sector 3'].min()
        
        s1_delta = df['Sector 1'].values - s1_best
        s2_delta = df['Sector 2'].values - s2_best
        s3_delta = df['Sector 3'].values - s3_best
        
        ax5.plot(laps, s1_delta, 'o-', color=COLORS['s1'], 
                linewidth=1.2, markersize=4, label=f'S1 (best: {s1_best:.2f}s)', alpha=0.8)
        ax5.plot(laps, s2_delta, 's-', color=COLORS['s2'], 
                linewidth=1.2, markersize=4, label=f'S2 (best: {s2_best:.2f}s)', alpha=0.8)
        ax5.plot(laps, s3_delta, '^-', color=COLORS['s3'], 
                linewidth=1.2, markersize=4, label=f'S3 (best: {s3_best:.2f}s)', alpha=0.8)
        
        # Add zero line (= personal best)
        ax5.axhline(0, color='#999', linestyle='--', linewidth=1, alpha=0.5)
        
        ax5.set_xlabel('Lap', fontsize=11)
        ax5.set_ylabel('Delta from Best (s)', fontsize=11)
        ax5.set_title('Sector Time Loss', fontsize=12, fontweight='bold')
        ax5.legend(loc='upper right', fontsize=8, framealpha=0.95)
        
        # Sector Focus Analysis - "Where's the Time?"
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.set_facecolor('#FFFFFF')
        
        # Use main phase for sector analysis
        main_df = df.iloc[middle_end:].copy() if middle_end < len(df) else df.copy()
        
        # Calculate metrics for each sector
        sectors = ['S1', 'S2', 'S3']
        sector_cols = ['Sector 1', 'Sector 2', 'Sector 3']
        
        gaps = []  # Mean - Best (time left on table)
        cvs = []   # Coefficient of variation (normalized consistency)
        
        for col in sector_cols:
            best = main_df[col].min()
            mean = main_df[col].mean()
            std = main_df[col].std()
            gaps.append(mean - best)
            cvs.append((std / mean) * 100 if mean > 0 else 0)
        
        # Create bar chart for gaps
        x = np.arange(len(sectors))
        colors = [COLORS['s1'], COLORS['s2'], COLORS['s3']]
        
        bars = ax6.bar(x, gaps, width=0.6, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
        
        # Add labels on bars
        for i, (bar, gap, cv) in enumerate(zip(bars, gaps, cvs)):
            # Gap label inside bar
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                    f'+{gap:.2f}s', ha='center', va='center', 
                    fontsize=11, fontweight='bold', color='white')
            
            # CV label above bar
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'CV: {cv:.1f}%', ha='center', va='bottom', 
                    fontsize=9, color='#666')
        
        ax6.set_xticks(x)
        ax6.set_xticklabels(sectors, fontsize=11)
        ax6.set_xlabel('', fontsize=11)
        ax6.set_ylabel('Gap to Best (s)', fontsize=11)
        ax6.set_title("Where's the Time? (Main Phase)", fontsize=12, fontweight='bold')
        max_gap = max(gaps)
        ax6.set_ylim(0, max_gap * 1.4 if max_gap > 0 else 0.5)
        
        # Add total gap annotation
        total_gap = sum(gaps)
        ax6.text(0.98, 0.95, f'Total gap: +{total_gap:.2f}s', 
                transform=ax6.transAxes, ha='right', va='top',
                fontsize=10, color='#666',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#DDD'))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Finalize
    # ═══════════════════════════════════════════════════════════════════════════
    plt.subplots_adjust(top=0.93, hspace=0.35, wspace=0.25)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='#FAFAFA', edgecolor='none')
        print(f"✅ Saved to: {output_path}")
    
    
    # Print summary stats
    print("\n" + "="*60)
    print("SESSION SUMMARY")
    print("="*60)
    print(f"Total laps: {len(laps)}")
    print(f"Clean laps: {int(clean.sum())} ({100*clean.sum()/len(clean):.0f}%)")
    print(f"Best lap: {times[fastest_idx]:.3f}s (lap {fastest_lap})")
    print(f"Mean: {mean_val:.3f}s | Median: {median_val:.3f}s")
    
    if middle_end < len(times):
        main_times = times[middle_end:]
        print(f"\nMAIN PHASE (laps {laps[middle_end]}-{laps[-1]}):")
        print(f"  Mean: {np.mean(main_times):.3f}s")
        print(f"  Std:  {np.std(main_times):.3f}s")
        print(f"  Band: {np.min(main_times):.3f}s - {np.max(main_times):.3f}s")
    
    if has_sectors:
        print(f"\nBEST SECTORS:")
        print(f"  S1: {df['Sector 1'].min():.3f}s")
        print(f"  S2: {df['Sector 2'].min():.3f}s")
        print(f"  S3: {df['Sector 3'].min():.3f}s")
        print(f"  Optimal: {df['Sector 1'].min() + df['Sector 2'].min() + df['Sector 3'].min():.3f}s")
    
    return fig


def main():
    parser = argparse.ArgumentParser(description="Visualize Garage 61 event CSV")
    parser.add_argument("csv_file", type=Path, help="Path to Garage 61 CSV export")
    parser.add_argument("--output", "-o", type=Path, help="Output directory or file path")
    parser.add_argument("--title", "-t", type=str, help="Custom title for the visualization")
    parser.add_argument("--show", "-s", action="store_true", help="Show interactive plot window")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"❌ File not found: {args.csv_file}")
        return 1
    
    # Load data
    print(f"Loading {args.csv_file}...")
    df = load_event_csv(args.csv_file)
    print(f"Found {len(df)} valid laps")
    
    # Determine output path
    if args.output:
        if args.output.is_dir():
            output_path = args.output / f"{args.csv_file.stem}.png"
        else:
            output_path = args.output
    else:
        output_path = args.csv_file.with_suffix('.png')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate title from filename if not provided
    if args.title:
        title = args.title
    else:
        # Parse filename for info
        filename = args.csv_file.stem
        # Try to extract date and session type
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        date_str = date_match.group(1) if date_match else ""
        
        if 'Race' in filename:
            event_type = "Race"
        elif 'Practice' in filename or 'Qualify' in filename:
            event_type = "Practice"
        else:
            event_type = "Event"
        
        title = f"{event_type} Analysis"
        if date_str:
            title += f" – {date_str}"
        
        # Add key stats
        best = df['Lap time'].min()
        title += f"\nBest: {best:.3f}s | Laps: {len(df)}"
    
    # Create visualization
    create_event_visualization(df, title=title, output_path=output_path)
    
    # Show interactive window if requested
    if args.show:
        plt.show()
    
    return 0


if __name__ == "__main__":
    exit(main())

