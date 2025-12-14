#!/usr/bin/env python3
"""
Event Visualization Tool
Reads Garage 61 CSV exports and creates meaningful visualizations.

Usage:
    uv run python tools/visualize_event.py results/your-event.csv
    uv run python tools/visualize_event.py results/your-event.csv --output images/week01/
    uv run python tools/visualize_event.py results/your-event.csv --include-first-lap  # for rolling starts
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.interpolate import make_interp_spline
from scipy.ndimage import gaussian_filter1d

from data_loader import load_event_csv

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
    best_time = np.min(times)
    laps_count = len(laps)
    fig.suptitle(
        f"{title} · Best {best_time:.3f}s · Laps {laps_count}",
        fontsize=18,
        fontweight='bold',
        color='#2C3E50',
        y=0.99,
    )
    
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
    ax1.set_title('Lap Progression', fontsize=12, fontweight='bold', pad=10)
    ax1.legend(loc='upper right', fontsize=8, framealpha=0.95)
    
    y_min, y_max = min(times) - 0.5, max(times) + 0.5
    ax1.set_ylim(y_min, y_max)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 2: Pace Trend - LEFT column, row 1 (lap-based)
    # ═══════════════════════════════════════════════════════════════════════════
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#FFFFFF')
    
    # Calculate rolling min/max for 5-lap corridor
    window_5_min = np.array([np.min(times[i:i+5]) for i in range(len(times)-4)])
    window_5_max = np.array([np.max(times[i:i+5]) for i in range(len(times)-4)])
    
    # Individual laps as subtle dots
    ax2.scatter(laps, times, color=COLORS['primary'], alpha=0.4, s=30, label='Individual')
    
    # X values for curves
    x_5 = laps[2:-2]  # x values for 5-lap range
    
    # Gaussian smoothing sigma (higher = smoother, adapts to session length)
    sigma = max(2, len(laps) // 10)
    
    if len(x_5) >= 4:
        # Pre-smooth the data with Gaussian filter to remove spikes
        smooth_min = gaussian_filter1d(window_5_min, sigma=sigma)
        smooth_max = gaussian_filter1d(window_5_max, sigma=sigma)
        
        # Create smooth x-axis with more points
        x_smooth = np.linspace(x_5.min(), x_5.max(), 200)
        
        # Smooth splines for flowing curves
        spline_min = make_interp_spline(x_5, smooth_min, k=3)
        spline_max = make_interp_spline(x_5, smooth_max, k=3)
        y_min_smooth = spline_min(x_smooth)
        y_max_smooth = spline_max(x_smooth)
        
        # 5-lap corridor as flowing range
        ax2.fill_between(x_smooth, y_min_smooth, y_max_smooth, 
                         color=COLORS['fastest'], alpha=0.2, label='5-lap range')
        
        # 3-lap trend line (use midpoint of corridor, extra smoothed)
        smooth_mid = gaussian_filter1d((window_5_min + window_5_max) / 2, sigma=sigma)
        spline_mid = make_interp_spline(x_5, smooth_mid, k=3)
        y_mid_smooth = spline_mid(x_smooth)
        ax2.plot(x_smooth, y_mid_smooth, '-', color=COLORS['accent'], linewidth=2.5, label='Trend')
    else:
        # Fallback for short sessions
        ax2.fill_between(x_5, window_5_min, window_5_max, 
                         color=COLORS['fastest'], alpha=0.2, label='5-lap range')
        ax2.plot(x_5, (window_5_min + window_5_max) / 2, '-', color=COLORS['accent'], linewidth=2.5, label='Trend')
    
    # Settled average line
    if middle_end < len(times):
        settled_times = times[middle_end:]
        settled_mean = np.mean(settled_times)
        ax2.axhline(settled_mean, color=COLORS['secondary'], linestyle='--', linewidth=1.2, 
                    alpha=0.7, label=f'Settled: {settled_mean:.2f}s')
    
    ax2.set_xlabel('Lap', fontsize=11)
    ax2.set_ylabel('Lap Time (s)', fontsize=11)
    ax2.set_title('Pace Trend', fontsize=12, fontweight='bold', pad=10)
    ax2.legend(loc='upper right', fontsize=8, framealpha=0.95)
    ax2.set_ylim(y_min, y_max)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 3: Rhythm Band Distribution - RIGHT column, row 0 (summary)
    # ═══════════════════════════════════════════════════════════════════════════
    ax3 = fig.add_subplot(gs[0, 1])
    ax3.set_facecolor('#FFFFFF')
    
    # Calculate the band from ALL flying laps (honest race reality)
    # Lap 1 already excluded by data_loader, so this includes warmup + main phase
    band_mean = np.mean(times)
    band_std = np.std(times)
    band_low = band_mean - band_std
    band_high = band_mean + band_std
    
    # Identify in-band vs out-of-band laps
    in_band_mask = (times >= band_low) & (times <= band_high)
    in_band_times = times[in_band_mask]
    out_band_times = times[~in_band_mask]
    in_band_pct = (len(in_band_times) / len(times)) * 100
    
    # Draw smooth KDE curve - subtle gray, not distracting
    sns.kdeplot(times, color='#6B7280', linewidth=1.5, ax=ax3, fill=True, alpha=0.15)
    
    # Add band shading - prominent green zone
    ax3.axvspan(band_low, band_high, alpha=0.35, color='#10B981', zorder=1)
    
    # Band boundary lines - subtle
    ax3.axvline(band_low, color='#10B981', linestyle='--', linewidth=1, alpha=0.5)
    ax3.axvline(band_high, color='#10B981', linestyle='--', linewidth=1, alpha=0.5)
    ax3.axvline(band_mean, color='#059669', linestyle='-', linewidth=2, alpha=0.8)
    
    # Plot out-of-band laps only - in-band count shown in legend
    y_base = ax3.get_ylim()[1] * 0.03
    
    # Out-of-band laps: orange markers - these need attention
    if len(out_band_times) > 0:
        ax3.scatter(out_band_times, [y_base] * len(out_band_times), 
                   color='#F59E0B', s=45, marker='o', zorder=6, alpha=0.85,
                   edgecolor='#D97706', linewidth=1, label=f'Out of band ({len(out_band_times)})')
    
    # Add all info to legend (right side, away from left peak)
    ax3.plot([], [], ' ', label=f'In band ({len(in_band_times)})')
    ax3.plot([], [], ' ', label=f'Band: {band_low:.2f}s – {band_high:.2f}s')
    ax3.plot([], [], ' ', label=f'σ {band_std:.2f}s')
    
    ax3.set_xlabel('Lap Time (s)', fontsize=11)
    ax3.set_ylabel('Density', fontsize=11)
    ax3.set_title(f'Rhythm Band ({in_band_pct:.0f}% in band)', fontsize=12, fontweight='bold', pad=10)
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
    ax4.set_title('Phase Comparison', fontsize=12, fontweight='bold', pad=10)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 5 & 6: Sector Analysis (if available)
    # ═══════════════════════════════════════════════════════════════════════════
    if has_sectors:
        # Rolling sector loss trend (smooth flowing lines)
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.set_facecolor('#FFFFFF')
        
        # Calculate delta from best for each sector
        s1_best = df['Sector 1'].min()
        s2_best = df['Sector 2'].min()
        s3_best = df['Sector 3'].min()
        
        # Calculate deltas, handling NaN values robustly
        s1_delta = df['Sector 1'].values - s1_best
        s2_delta = df['Sector 2'].values - s2_best
        s3_delta = df['Sector 3'].values - s3_best
        
        # Replace NaN with 0 (incomplete laps)
        s1_loss = np.nan_to_num(np.maximum(s1_delta, 0), nan=0.0)
        s2_loss = np.nan_to_num(np.maximum(s2_delta, 0), nan=0.0)
        s3_loss = np.nan_to_num(np.maximum(s3_delta, 0), nan=0.0)
        
        # Gaussian smoothing for trend (adapts to session length)
        sigma = max(2, len(laps) // 8)
        
        if len(laps) >= 6:
            s1_smooth = gaussian_filter1d(s1_loss, sigma=sigma)
            s2_smooth = gaussian_filter1d(s2_loss, sigma=sigma)
            s3_smooth = gaussian_filter1d(s3_loss, sigma=sigma)
            
            # Interpolate for flowing curves
            x_smooth = np.linspace(laps.min(), laps.max(), 200)
            
            # Plot flowing trend lines
            if len(laps) >= 4:
                spline_s1 = make_interp_spline(laps, s1_smooth, k=3)
                spline_s2 = make_interp_spline(laps, s2_smooth, k=3)
                spline_s3 = make_interp_spline(laps, s3_smooth, k=3)
                
                ax5.plot(x_smooth, spline_s1(x_smooth), '-', color=COLORS['s1'], 
                         linewidth=2.5, label=f'S1 (+{np.sum(s1_loss):.1f}s total)', alpha=0.9)
                ax5.plot(x_smooth, spline_s2(x_smooth), '-', color=COLORS['s2'], 
                         linewidth=2.5, label=f'S2 (+{np.sum(s2_loss):.1f}s total)', alpha=0.9)
                ax5.plot(x_smooth, spline_s3(x_smooth), '-', color=COLORS['s3'], 
                         linewidth=2.5, label=f'S3 (+{np.sum(s3_loss):.1f}s total)', alpha=0.9)
            else:
                ax5.plot(laps, s1_smooth, '-', color=COLORS['s1'], linewidth=2.5, 
                         label=f'S1 (+{np.sum(s1_loss):.1f}s total)', alpha=0.9)
                ax5.plot(laps, s2_smooth, '-', color=COLORS['s2'], linewidth=2.5, 
                         label=f'S2 (+{np.sum(s2_loss):.1f}s total)', alpha=0.9)
                ax5.plot(laps, s3_smooth, '-', color=COLORS['s3'], linewidth=2.5, 
                         label=f'S3 (+{np.sum(s3_loss):.1f}s total)', alpha=0.9)
            
            # Add subtle scatter for actual data points
            ax5.scatter(laps, s1_loss, color=COLORS['s1'], alpha=0.3, s=15, zorder=1)
            ax5.scatter(laps, s2_loss, color=COLORS['s2'], alpha=0.3, s=15, zorder=1)
            ax5.scatter(laps, s3_loss, color=COLORS['s3'], alpha=0.3, s=15, zorder=1)
        else:
            # Fallback for short sessions - simple lines
            ax5.plot(laps, s1_loss, '-o', color=COLORS['s1'], linewidth=2, markersize=4,
                     label=f'S1 (+{np.sum(s1_loss):.1f}s total)', alpha=0.9)
            ax5.plot(laps, s2_loss, '-o', color=COLORS['s2'], linewidth=2, markersize=4,
                     label=f'S2 (+{np.sum(s2_loss):.1f}s total)', alpha=0.9)
            ax5.plot(laps, s3_loss, '-o', color=COLORS['s3'], linewidth=2, markersize=4,
                     label=f'S3 (+{np.sum(s3_loss):.1f}s total)', alpha=0.9)
        
        ax5.axhline(0, color='#ccc', linewidth=1, linestyle='--', alpha=0.5)
        ax5.set_xlabel('Lap', fontsize=11)
        ax5.set_ylabel('Time Lost (s)', fontsize=11)
        ax5.set_title('Sector Loss Trend', fontsize=12, fontweight='bold', pad=10)
        ax5.legend(loc='upper right', fontsize=8, framealpha=0.95)
        ax5.set_ylim(bottom=0)
        
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
        ax6.set_title("Where's the Time? (Main Phase)", fontsize=12, fontweight='bold', pad=10)
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
    print(f"Mean: {np.mean(times):.3f}s | Median: {np.median(times):.3f}s")
    
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
    parser.add_argument("--include-first-lap", action="store_true", 
                       help="Include lap 1 in analysis (use for rolling starts)")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"❌ File not found: {args.csv_file}")
        return 1
    
    # Load data (exclude first lap by default for standing starts)
    exclude_first = not args.include_first_lap
    print(f"Loading {args.csv_file}...")
    df = load_event_csv(args.csv_file, exclude_first_lap=exclude_first)
    print(f"Found {len(df)} valid laps" + (" (excluding lap 1)" if exclude_first else ""))
    
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
    
    # Create visualization
    create_event_visualization(df, title=title, output_path=output_path)
    
    # Show interactive window if requested
    if args.show:
        plt.show()
    
    return 0


if __name__ == "__main__":
    exit(main())

