#!/usr/bin/env python3
"""
Lap Progression Visualization (Modular)
Creates a simple lap time progression chart - the baseline visualization.

Usage:
    python tools/viz_lap_progression.py event.csv output.png
    python tools/viz_lap_progression.py event.csv output.png --title "Event #1"
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from data_loader import load_event_csv

# Configure seaborn style
sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)

COLORS = {
    'primary': '#2E86AB',
    'fastest': '#1B998B',
    'dirty': '#E94F37',
}


def create_lap_progression(
    csv_path: Path,
    output_path: Path,
    title: str = "Lap Progression",
):
    """Create lap progression visualization."""
    
    # Load data
    df = load_event_csv(csv_path, exclude_first_lap=True)
    
    if df.empty:
        print(f"Error: No valid laps found in {csv_path}")
        return
    
    laps = df['Lap'].values
    times = df['Lap time'].values
    clean = df['Clean'].values if 'Clean' in df.columns else np.ones(len(laps))
    
    # Find fastest and dirty laps
    fastest_idx = np.argmin(times)
    fastest_lap = laps[fastest_idx]
    fastest_time = times[fastest_idx]
    dirty_laps = laps[clean == 0].tolist()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FFFFFF')
    
    # Plot lap times
    ax.plot(laps, times, 'o-', color=COLORS['primary'], linewidth=1.5, 
            markersize=7, markerfacecolor='white', markeredgewidth=1.5, alpha=0.9,
            label='Lap times')
    
    # Highlight fastest lap
    ax.scatter([fastest_lap], [fastest_time], color=COLORS['fastest'], 
              s=120, zorder=5, marker='*', label=f'Fastest: {fastest_time:.3f}s')
    
    # Highlight dirty/off-track laps
    for lap in dirty_laps:
        idx = np.where(laps == lap)[0]
        if len(idx) > 0:
            ax.scatter([lap], [times[idx[0]]], color=COLORS['dirty'], s=50, 
                      zorder=4, marker='x', linewidths=2, alpha=0.8)
    
    # Add mean line
    mean_time = np.mean(times)
    ax.axhline(mean_time, color='gray', linestyle='--', linewidth=1, 
              alpha=0.5, label=f'Mean: {mean_time:.3f}s')
    
    # Labels and title
    ax.set_xlabel('Lap', fontsize=12, fontweight='bold')
    ax.set_ylabel('Lap Time (s)', fontsize=12, fontweight='bold')
    
    full_title = f"{title} · Best {fastest_time:.3f}s · {len(laps)} laps"
    ax.set_title(full_title, fontsize=14, fontweight='bold', pad=15, color='#2C3E50')
    
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax.grid(True, alpha=0.3)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()
    
    print(f"✓ Lap progression saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create lap progression visualization"
    )
    parser.add_argument("csv_file", type=Path, help="Path to event CSV file")
    parser.add_argument("output", type=Path, help="Output PNG file path")
    parser.add_argument("--title", default="Lap Progression", help="Chart title")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}")
        return
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    create_lap_progression(args.csv_file, args.output, args.title)


if __name__ == "__main__":
    main()
