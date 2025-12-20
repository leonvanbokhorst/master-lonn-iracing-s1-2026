#!/usr/bin/env python3
"""
Pace Trend Visualization (Modular)
Shows smoothed pace trend with 5-lap corridor and settled pace line.
Useful for analyzing consistency issues.

Usage:
    python tools/viz_pace_trend.py event.csv output.png
    python tools/viz_pace_trend.py event.csv output.png --title "Event #1"
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.interpolate import make_interp_spline
from scipy.ndimage import gaussian_filter1d

from data_loader import load_event_csv

# Configure seaborn style
sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)

COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'fastest': '#1B998B',
}


def create_pace_trend(
    csv_path: Path,
    output_path: Path,
    title: str = "Pace Trend Analysis",
):
    """Create pace trend visualization with smoothed corridor."""
    
    # Load data
    df = load_event_csv(csv_path, exclude_first_lap=True)
    
    if df.empty:
        print(f"Error: No valid laps found in {csv_path}")
        return
    
    laps = df['Lap'].values
    times = df['Lap time'].values
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FFFFFF')
    
    # Scatter individual laps
    ax.scatter(laps, times, color=COLORS['primary'], alpha=0.4, s=40, 
              label='Individual laps', zorder=2)
    
    # Calculate smoothed corridor (5-lap window)
    sigma = max(2, len(laps) // 10) if len(laps) > 1 else 1
    
    if len(times) >= 5:
        window_5_min = np.array([np.min(times[i:i+5]) for i in range(len(times) - 4)])
        window_5_max = np.array([np.max(times[i:i+5]) for i in range(len(times) - 4)])
        x_5 = laps[2:-2]
        
        if len(x_5) >= 4:
            # Smooth and spline
            smooth_min = gaussian_filter1d(window_5_min, sigma=sigma)
            smooth_max = gaussian_filter1d(window_5_max, sigma=sigma)
            
            x_smooth = np.linspace(x_5.min(), x_5.max(), 200)
            
            spline_min = make_interp_spline(x_5, smooth_min, k=3)
            spline_max = make_interp_spline(x_5, smooth_max, k=3)
            y_min_smooth = spline_min(x_smooth)
            y_max_smooth = spline_max(x_smooth)
            
            # Fill corridor
            ax.fill_between(
                x_smooth, y_min_smooth, y_max_smooth,
                color=COLORS['fastest'], alpha=0.2, label='5-lap pace range',
                zorder=1
            )
            
            # Trend line (middle of corridor)
            smooth_mid = gaussian_filter1d((window_5_min + window_5_max) / 2, sigma=sigma)
            spline_mid = make_interp_spline(x_5, smooth_mid, k=3)
            ax.plot(x_smooth, spline_mid(x_smooth), '-', color=COLORS['accent'],
                   linewidth=3, label='Pace trend', zorder=3)
        else:
            # Fallback for short sessions
            ax.fill_between(x_5, window_5_min, window_5_max,
                           color=COLORS['fastest'], alpha=0.2, label='5-lap pace range',
                           zorder=1)
            ax.plot(x_5, (window_5_min + window_5_max) / 2, '-',
                   color=COLORS['accent'], linewidth=3, label='Pace trend', zorder=3)
    else:
        # Very short session - just smooth the raw times
        smooth = gaussian_filter1d(times, sigma=sigma)
        ax.plot(laps, smooth, '-', color=COLORS['accent'], linewidth=3, 
               label='Pace trend', zorder=3)
    
    # Settled pace line (last third of session)
    middle_end = 2 * len(times) // 3
    if middle_end < len(times):
        settled_times = times[middle_end:]
        settled_mean = np.mean(settled_times)
        ax.axhline(settled_mean, color=COLORS['secondary'], linestyle='--', 
                  linewidth=2, alpha=0.7, 
                  label=f'Settled pace: {settled_mean:.2f}s', zorder=3)
    
    # Labels and title
    ax.set_xlabel('Lap', fontsize=12, fontweight='bold')
    ax.set_ylabel('Lap Time (s)', fontsize=12, fontweight='bold')
    
    best_time = np.min(times)
    sigma_val = np.std(times)
    full_title = f"{title} · Best {best_time:.3f}s · σ = {sigma_val:.2f}s"
    ax.set_title(full_title, fontsize=14, fontweight='bold', pad=15, color='#2C3E50')
    
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax.grid(True, alpha=0.3)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()
    
    print(f"✓ Pace trend visualization saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create pace trend visualization"
    )
    parser.add_argument("csv_file", type=Path, help="Path to event CSV file")
    parser.add_argument("output", type=Path, help="Output PNG file path")
    parser.add_argument("--title", default="Pace Trend Analysis", help="Chart title")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}")
        return
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    create_pace_trend(args.csv_file, args.output, args.title)


if __name__ == "__main__":
    main()
