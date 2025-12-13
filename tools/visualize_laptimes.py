#!/usr/bin/env python3
"""
Lap Time Visualization Tool
Creates meaningful visualizations of race lap times showing phases and bands.

Usage:
    uv run python tools/visualize_laptimes.py
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Configure seaborn style - light and fancy!
sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)
sns.set_context("notebook", rc={"lines.linewidth": 1.5})

# Custom color palette - warm and inviting
COLORS = {
    'primary': '#2E86AB',      # Steel blue
    'secondary': '#A23B72',    # Raspberry
    'accent': '#F18F01',       # Orange
    'success': '#C73E1D',      # Brick red
    'fastest': '#1B998B',      # Teal
    'early': '#E94F37',        # Coral red
    'middle': '#F6AE2D',       # Golden yellow
    'main': '#33A1FD',         # Sky blue
    'band': '#86BA90',         # Sage green
}


def parse_laptime(time_str: str) -> float:
    """Convert MM:SS.mmm or SS.mmm to seconds."""
    if ':' in time_str:
        parts = time_str.split(':')
        return float(parts[0]) * 60 + float(parts[1])
    return float(time_str)


def create_race_visualization(
    lap_times: list[float],
    title: str = "Race Lap Times",
    output_path: Path | None = None,
    fastest_lap: int | None = None,
    off_track_laps: list[int] | None = None,
    phase_boundaries: tuple[int, int] | None = None,
    target_band: tuple[float, float] | None = None,
):
    """Create a comprehensive lap time visualization with seaborn styling."""
    
    laps = list(range(1, len(lap_times) + 1))
    times = np.array(lap_times)
    
    # Auto-detect phases if not provided
    if phase_boundaries is None:
        early_end = next((i for i, t in enumerate(times) if t < 53.0), 8)
        middle_end = next((i for i, t in enumerate(times) if t < 51.8), 15)
        phase_boundaries = (early_end, middle_end)
    
    # Create figure with custom layout
    fig = plt.figure(figsize=(14, 11))
    fig.patch.set_facecolor('#FAFAFA')
    
    # Title with style
    fig.suptitle(title, fontsize=18, fontweight='bold', color='#2C3E50', y=0.99)
    
    # Create grid spec for flexible layout
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 1: Main lap time progression with phases
    # ═══════════════════════════════════════════════════════════════════════════
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#FFFFFF')
    
    early_end, middle_end = phase_boundaries
    
    # Plot phase regions with soft colors
    ax1.axvspan(1, early_end + 0.5, alpha=0.25, color=COLORS['early'], label='Early (warm-up)')
    ax1.axvspan(early_end + 0.5, middle_end + 0.5, alpha=0.25, color=COLORS['middle'], label='Middle (settling)')
    ax1.axvspan(middle_end + 0.5, len(laps) + 0.5, alpha=0.25, color=COLORS['main'], label='Main (metronome)')
    
    # Target band
    if target_band:
        ax1.axhspan(target_band[0], target_band[1], alpha=0.15, color=COLORS['band'], 
                   label=f'Target: {target_band[0]:.1f}-{target_band[1]:.1f}s')
    
    # Plot lap times with markers
    ax1.plot(laps, times, 'o-', color=COLORS['primary'], linewidth=1.2, 
             markersize=6, markerfacecolor='white', markeredgewidth=1.5, alpha=0.9)
    
    # Highlight fastest lap
    if fastest_lap:
        ax1.scatter([fastest_lap], [times[fastest_lap - 1]], color=COLORS['fastest'], 
                   s=250, zorder=5, marker='*', label=f'Fastest: {times[fastest_lap-1]:.3f}s')
    
    # Highlight off-track laps
    if off_track_laps:
        for lap in off_track_laps:
            ax1.scatter([lap], [times[lap - 1]], color=COLORS['early'], s=120, 
                       zorder=4, marker='X', linewidths=2)
            ax1.annotate('off-track', (lap, times[lap - 1] + 0.3), ha='center', 
                        fontsize=8, color=COLORS['early'])
    
    ax1.set_xlabel('Lap', fontsize=12, fontweight='medium')
    ax1.set_ylabel('Lap Time (seconds)', fontsize=12, fontweight='medium')
    ax1.set_title('Lap Progression by Phase', fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc='upper right', fontsize=8, framealpha=0.95, edgecolor='#DDD')
    
    y_min, y_max = min(times) - 1, max(times) + 1
    ax1.set_ylim(y_min, y_max)
    ax1.set_xlim(0.5, len(laps) + 0.5)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 2: Rolling average (trend line)
    # ═══════════════════════════════════════════════════════════════════════════
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#FFFFFF')
    
    # Calculate rolling averages
    window_3 = np.convolve(times, np.ones(3)/3, mode='valid')
    window_5 = np.convolve(times, np.ones(5)/5, mode='valid')
    
    ax2.scatter(laps, times, color=COLORS['primary'], alpha=0.4, s=30, label='Individual laps')
    ax2.plot(laps[1:-1], window_3, '-', color=COLORS['accent'], linewidth=1.5, label='3-lap rolling avg')
    ax2.plot(laps[2:-2], window_5, '-', color=COLORS['fastest'], linewidth=2, label='5-lap rolling avg')
    
    # Add confidence interval for the settled phase
    settled_times = times[middle_end:]
    settled_mean = np.mean(settled_times)
    settled_std = np.std(settled_times)
    ax2.axhline(settled_mean, color=COLORS['secondary'], linestyle='--', linewidth=1.2, alpha=0.7, 
                label=f'Settled avg: {settled_mean:.2f}s')
    ax2.fill_between([middle_end + 1, len(laps)], 
                     settled_mean - settled_std, settled_mean + settled_std,
                     alpha=0.15, color=COLORS['secondary'])
    
    ax2.set_xlabel('Lap', fontsize=12, fontweight='medium')
    ax2.set_ylabel('Lap Time (seconds)', fontsize=12, fontweight='medium')
    ax2.set_title('Pace Trend (Rolling Average)', fontsize=13, fontweight='bold', pad=10)
    ax2.legend(loc='upper right', fontsize=8, framealpha=0.95, edgecolor='#DDD')
    ax2.set_ylim(y_min, y_max)
    ax2.set_xlim(0.5, len(laps) + 0.5)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 3: Distribution with KDE
    # ═══════════════════════════════════════════════════════════════════════════
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#FFFFFF')
    
    # Skip outlap for cleaner distribution
    race_times = times[1:]
    
    # Use seaborn's histplot with KDE
    sns.histplot(race_times, bins=15, kde=True, color=COLORS['primary'], 
                 alpha=0.6, edgecolor='white', linewidth=0.8, ax=ax3)
    
    # Add mean and median lines
    mean_val = np.mean(race_times)
    median_val = np.median(race_times)
    ax3.axvline(mean_val, color=COLORS['early'], linestyle='--', linewidth=1.5, 
                label=f'Mean: {mean_val:.2f}s')
    ax3.axvline(median_val, color=COLORS['fastest'], linestyle=':', linewidth=1.5, 
                label=f'Median: {median_val:.2f}s')
    
    ax3.set_xlabel('Lap Time (seconds)', fontsize=12, fontweight='medium')
    ax3.set_ylabel('Frequency', fontsize=12, fontweight='medium')
    ax3.set_title('Lap Time Distribution (excl. outlap)', fontsize=13, fontweight='bold', pad=10)
    ax3.legend(loc='upper right', fontsize=9, framealpha=0.95, edgecolor='#DDD')
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLOT 4: Phase comparison violin + swarm
    # ═══════════════════════════════════════════════════════════════════════════
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#FFFFFF')
    
    # Prepare data for seaborn
    import pandas as pd
    
    early_times = times[:early_end]
    middle_times = times[early_end:middle_end]
    main_times = times[middle_end:]
    
    phase_df = pd.DataFrame({
        'Lap Time': list(early_times) + list(middle_times) + list(main_times),
        'Phase': (['Early\n(warm-up)'] * len(early_times) + 
                  ['Middle\n(settling)'] * len(middle_times) + 
                  ['Main\n(metronome)'] * len(main_times))
    })
    
    # Create violin plot with individual points
    sns.violinplot(data=phase_df, x='Phase', y='Lap Time', hue='Phase',
                   palette=[COLORS['early'], COLORS['middle'], COLORS['main']], 
                   alpha=0.6, inner=None, legend=False, ax=ax4)
    sns.stripplot(data=phase_df, x='Phase', y='Lap Time', color='#2C3E50', 
                  alpha=0.7, size=6, jitter=0.15, legend=False, ax=ax4)
    
    # Add statistics annotations
    phases_data = [early_times, middle_times, main_times]
    phase_names = ['Early\n(warm-up)', 'Middle\n(settling)', 'Main\n(metronome)']
    
    for i, (data, name) in enumerate(zip(phases_data, phase_names)):
        mean = np.mean(data)
        std = np.std(data)
        ax4.annotate(f'μ={mean:.2f}s\nσ={std:.2f}s', 
                    xy=(i, max(data) + 0.8),
                    ha='center', fontsize=9, fontweight='medium', color='#2C3E50',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                             edgecolor='#DDD', alpha=0.9))
    
    ax4.set_xlabel('', fontsize=12)
    ax4.set_ylabel('Lap Time (seconds)', fontsize=12, fontweight='medium')
    ax4.set_title('Phase Comparison', fontsize=13, fontweight='bold', pad=10)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Finalize
    # ═══════════════════════════════════════════════════════════════════════════
    plt.subplots_adjust(top=0.90, hspace=0.32, wspace=0.25)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='#FAFAFA', edgecolor='none')
        print(f"✅ Saved to: {output_path}")
    
    plt.show()
    return fig


def main():
    """Example usage with the AI race data from 2025-12-12."""
    
    # Lap times from the AI race (in seconds)
    lap_times = [
        63.043,  # Lap 1 - outlap
        54.408,  # Lap 2
        54.923,  # Lap 3
        53.685,  # Lap 4
        53.661,  # Lap 5
        53.036,  # Lap 6
        53.788,  # Lap 7
        53.180,  # Lap 8
        52.226,  # Lap 9
        51.707,  # Lap 10
        52.168,  # Lap 11
        51.374,  # Lap 12
        51.569,  # Lap 13
        51.834,  # Lap 14
        52.239,  # Lap 15 - off track
        51.460,  # Lap 16
        51.495,  # Lap 17
        51.547,  # Lap 18
        51.534,  # Lap 19
        51.148,  # Lap 20 - FASTEST
        51.201,  # Lap 21
        51.490,  # Lap 22
        51.386,  # Lap 23
        51.900,  # Lap 24
        51.557,  # Lap 25
        51.637,  # Lap 26
        51.745,  # Lap 27
        51.428,  # Lap 28
        51.320,  # Lap 29
    ]
    
    output_path = Path(__file__).parent.parent / "images" / "week01" / "20251212-ai-race-laptimes.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    create_race_visualization(
        lap_times=lap_times,
        title="AI Race – Jefferson Circuit – 2025-12-12\nP12 → P2 | Best: 51.148s | 14x inc",
        output_path=output_path,
        fastest_lap=20,
        off_track_laps=[15],
        phase_boundaries=(8, 15),
        target_band=(51.0, 52.0),
    )


if __name__ == "__main__":
    main()
