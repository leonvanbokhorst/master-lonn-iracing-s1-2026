#!/usr/bin/env python3
"""
Sector Loss Visualization (Modular)
Shows time lost in each sector compared to best sector time.

Usage:
    python tools/viz_sector_loss.py event.csv output.png
    python tools/viz_sector_loss.py event.csv output.png --title "Event #1"
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.ndimage import gaussian_filter1d

from data_loader import load_event_csv

# Configure seaborn style
sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)

SECTOR_COLORS = ['#2E86AB', '#F18F01', '#1B998B', '#A23B72', '#F6AE2D']


def create_sector_loss(
    csv_path: Path,
    output_path: Path,
    title: str = "Sector Loss Analysis",
):
    """Create sector loss visualization."""
    
    # Load data
    df = load_event_csv(csv_path, exclude_first_lap=True)
    
    if df.empty:
        print(f"Error: No valid laps found in {csv_path}")
        return
    
    # Get sector columns
    sector_cols = [col for col in df.columns if col.lower().startswith("sector ")]
    
    if not sector_cols:
        print(f"Error: No sector data found in {csv_path}")
        return
    
    laps = df['Lap'].values
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FFFFFF')
    
    # Calculate and plot sector loss
    sigma = max(2, len(laps) // 8) if len(laps) > 1 else 1
    
    for idx, col in enumerate(sector_cols):
        color = SECTOR_COLORS[idx % len(SECTOR_COLORS)]
        sector_times = df[col].values
        best = np.min(sector_times)
        delta = sector_times - best
        loss = np.nan_to_num(np.maximum(delta, 0), nan=0.0)
        
        total_loss = np.sum(loss)
        
        # Smooth the line if enough data
        if len(laps) >= 6:
            smooth_loss = gaussian_filter1d(loss, sigma=sigma)
            ax.plot(laps, smooth_loss, '-', color=color, linewidth=2.5,
                   label=f'{col} (+{total_loss:.1f}s total)', alpha=0.9)
            ax.scatter(laps, loss, color=color, alpha=0.3, s=20, zorder=1)
        else:
            ax.plot(laps, loss, 'o-', color=color, linewidth=2, markersize=5,
                   label=f'{col} (+{total_loss:.1f}s total)', alpha=0.9)
    
    # Zero line
    ax.axhline(0, color='#ccc', linewidth=1, linestyle='--', alpha=0.5)
    
    # Labels and title
    ax.set_xlabel('Lap', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time Lost vs Best (s)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#2C3E50')
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()
    
    print(f"✓ Sector loss visualization saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create sector loss visualization"
    )
    parser.add_argument("csv_file", type=Path, help="Path to event CSV file")
    parser.add_argument("output", type=Path, help="Output PNG file path")
    parser.add_argument("--title", default="Sector Loss Analysis", help="Chart title")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}")
        return
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    create_sector_loss(args.csv_file, args.output, args.title)


if __name__ == "__main__":
    main()
