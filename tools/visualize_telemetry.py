"""
Telemetry Visualization Tool
Reads Garage 61 single-lap telemetry exports and creates detailed analysis.

Usage:
    uv run python tools/visualize_telemetry.py path/to/telemetry.csv
    uv run python tools/visualize_telemetry.py path/to/telemetry.csv --output images/
"""

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

from config import pedals

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')

COLORS = {
    'speed': '#2E86AB',
    'throttle': '#1B998B',
    'brake': '#E94F37',
    'gear': '#F6AE2D',
    'track': '#2C3E50',
    'track_start': '#E94F37',
}

COAST_DISPLAY_THRESHOLD = 0.1  # %


def load_telemetry(csv_path: Path) -> pd.DataFrame:
    """Load telemetry CSV from Garage61."""
    df = pd.read_csv(csv_path)
    
    # Convert LapDistPct to percentage (0-100)
    df['TrackPct'] = df['LapDistPct'] * 100
    
    return df


def compute_coasting_zones(
    df: pd.DataFrame,
    throttle_threshold: float,
    brake_threshold: float,
    long_accel_threshold: float | None = None,
):
    """Compute coasting zones from pedal data.
    
    Returns:
        coasting_mask: Boolean array for each sample
        coasting_starts: List of track % where coasting begins
        coasting_ends: List of track % where coasting ends
        coasting_pct: Percentage of lap spent coasting
    """
    coasting_mask = (df['Throttle'] < throttle_threshold) & (df['Brake'] < brake_threshold)
    if long_accel_threshold is not None and 'LongAccel' in df.columns:
        coasting_mask &= df['LongAccel'].abs() < long_accel_threshold
    coasting_starts = []
    coasting_ends = []
    in_coast = False
    
    for i, is_coasting in enumerate(coasting_mask):
        if is_coasting and not in_coast:
            coasting_starts.append(df['TrackPct'].iloc[i])
            in_coast = True
        elif not is_coasting and in_coast:
            coasting_ends.append(df['TrackPct'].iloc[i])
            in_coast = False
    if in_coast:
        coasting_ends.append(df['TrackPct'].iloc[-1])
    
    coasting_pct = coasting_mask.sum() / len(coasting_mask) * 100
    
    return coasting_mask, coasting_starts, coasting_ends, coasting_pct


def create_telemetry_visualization(
    df: pd.DataFrame,
    title: str = "Lap Telemetry Analysis",
    output_path: Path = None
):
    """Create a comprehensive telemetry visualization."""
    
    # Create figure with custom layout (taller to fit everything)
    fig = plt.figure(figsize=(16, 14))
    
    # Grid: 3 rows
    # Row 0: Speed trace (full width)
    # Row 1: Throttle/Brake (full width) - aligned with speed for comparison
    # Row 2: Track map (full width, big)
    
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1.6], 
                          hspace=0.25,
                          left=0.06, right=0.98, top=0.94, bottom=0.04)
    
    # Title
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97)
    
    # ========== 1. SPEED TRACE COLORED BY PEDAL INPUT (full width) ==========
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor('#FAFAFA')
    
    # Classify each point by pedal state (match event stats thresholds)
    throttle_threshold = 0.05  # 5% throttle treated as on-throttle
    brake_threshold = 0.01     # 2% brake ≈ light trail braking
    coast_accel_threshold = 0.5  # |LongAccel| < 0.5 m/s² counts as true coasting
    
    x = df['TrackPct'].values
    y = df['Speed'].values * 3.6  # Convert m/s to km/h
    throttle = df['Throttle'].values
    brake = df['Brake'].values
    
    # Compute coasting zones once (used by speed trace, track map, and pedal graph)
    coasting_mask, coasting_starts, coasting_ends, coasting_pct = compute_coasting_zones(
        df, throttle_threshold, brake_threshold, coast_accel_threshold
    )
    
    # Draw coasting zones behind everything
    show_coast = coasting_pct >= COAST_DISPLAY_THRESHOLD

    if show_coast:
        for start, end in zip(coasting_starts, coasting_ends):
            ax1.axvspan(start, end, alpha=0.25, color='#38BDF8', zorder=0)
    
    # Plot speed trace colored by pedal state using vectorized masks (performance)
    # Brake has precedence over throttle
    brake_mask = brake > brake_threshold
    throttle_mask = (throttle > throttle_threshold) & ~brake_mask
    coast_mask = coasting_mask
    
    # Use NaNs to break lines between segments of different states
    y_brake = np.where(brake_mask, y, np.nan)
    y_throttle = np.where(throttle_mask, y, np.nan)
    y_coast = np.where(coast_mask, y, np.nan)
    
    # Base speed trace for continuity
    ax1.plot(x, y, color='#CBD5F5', linewidth=1.2, alpha=0.5, zorder=0.5)

    # Coasting = thin, light, dashed - only when significant
    if show_coast:
        ax1.plot(x, y_coast, color='#D1D5DB', linewidth=1.5, alpha=0.6, linestyle='--')
    # Throttle = green
    ax1.plot(x, y_throttle, color=COLORS['throttle'], linewidth=2.5, alpha=0.9, solid_capstyle='round')
    # Braking = red
    ax1.plot(x, y_brake, color=COLORS['brake'], linewidth=2.5, alpha=0.9, solid_capstyle='round')
    
    # Add subtle fill for shape context
    ax1.fill_between(x, 0, y, color='#E5E7EB', alpha=0.3)
    
    # Mark min/max speed (using km/h values)
    max_idx = df['Speed'].idxmax()
    min_idx = df['Speed'].idxmin()
    max_speed_kmh = df.loc[max_idx, 'Speed'] * 3.6
    min_speed_kmh = df.loc[min_idx, 'Speed'] * 3.6
    ax1.scatter([df.loc[max_idx, 'TrackPct']], [max_speed_kmh], 
                color=COLORS['throttle'], s=60, zorder=5, marker='^', edgecolor='white', linewidth=1)
    ax1.scatter([df.loc[min_idx, 'TrackPct']], [min_speed_kmh], 
                color=COLORS['brake'], s=60, zorder=5, marker='v', edgecolor='white', linewidth=1)
    
    ax1.annotate(f'Max: {max_speed_kmh:.0f}', 
                xy=(df.loc[max_idx, 'TrackPct'], max_speed_kmh),
                xytext=(5, 10), textcoords='offset points', fontsize=9,
                color=COLORS['throttle'], fontweight='bold')
    ax1.annotate(f'Min: {min_speed_kmh:.0f}', 
                xy=(df.loc[min_idx, 'TrackPct'], min_speed_kmh),
                xytext=(5, -15), textcoords='offset points', fontsize=9,
                color=COLORS['brake'], fontweight='bold')
    
    # Add legend for pedal colors
    legend_elements = [
        Line2D([0], [0], color=COLORS['throttle'], linewidth=3, label='Throttle'),
        Line2D([0], [0], color=COLORS['brake'], linewidth=3, label='Braking'),
    ]
    if show_coast:
        legend_elements.append(Line2D([0], [0], color='#D1D5DB', linewidth=1.5, linestyle='--', label='Coasting'))
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.95)
    
    ax1.set_xlabel('Track Position (%)', fontsize=11)
    ax1.set_ylabel('Speed (km/h)', fontsize=11)
    ax1.set_title('Speed Trace (colored by pedal input)', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, df['Speed'].max() * 3.6 * 1.1)
    
    # ========== 3. TRACK MAP COLORED BY PEDAL STATE (full width, row 2) ==========
    ax3 = fig.add_subplot(gs[2])  # Full width, bottom row
    ax3.set_facecolor('#FAFAFA')
    
    # Plot track by pedal state - coasting only when above threshold
    throttle_mask = df['Throttle'] > throttle_threshold
    brake_mask = df['Brake'] > brake_threshold
    coast_mask = coasting_mask if show_coast else None
    
    if show_coast:
        ax3.scatter(df.loc[coast_mask, 'Lon'], df.loc[coast_mask, 'Lat'], 
                   c='#D1D5DB', s=2, alpha=0.3)
    
    # Throttle = bold green
    ax3.scatter(df.loc[throttle_mask, 'Lon'], df.loc[throttle_mask, 'Lat'], 
               c=COLORS['throttle'], s=10, alpha=0.9)
    
    # Braking = bold red
    ax3.scatter(df.loc[brake_mask, 'Lon'], df.loc[brake_mask, 'Lat'], 
               c=COLORS['brake'], s=10, alpha=0.9)
    
    # Mark start/finish
    ax3.scatter([df.iloc[0]['Lon']], [df.iloc[0]['Lat']], 
                color='white', s=120, marker='o', 
                zorder=5, edgecolor=COLORS['track_start'], linewidth=3)
    ax3.annotate('S/F', xy=(df.iloc[0]['Lon'], df.iloc[0]['Lat']),
                xytext=(8, 8), textcoords='offset points', fontsize=10,
                fontweight='bold', color=COLORS['track_start'])
    
    ax3.set_aspect('equal')
    title_suffix = f"Coasting: {coasting_pct:.1f}%"
    if not show_coast:
        title_suffix += " (hidden)"
    ax3.set_title(f'Track Map (colored by pedal input) – {title_suffix}', fontsize=12, fontweight='bold')
    ax3.set_xlabel('')
    ax3.set_ylabel('')
    ax3.set_xticks([])
    ax3.set_yticks([])
    
    # Custom legend
    legend_elements = [
        Patch(facecolor=COLORS['throttle'], label='Throttle'),
        Patch(facecolor=COLORS['brake'], label='Braking'),
    ]
    if show_coast:
        legend_elements.append(Patch(facecolor='#D1D5DB', alpha=0.3, label='Coasting (gaps)'))
    ax3.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.95)
    
    # ========== 4. PEDALS (trail braking view) ==========
    ax4 = fig.add_subplot(gs[1])  # Full width, middle row (aligned with speed trace)
    ax4.set_facecolor('#FAFAFA')
    ax4.grid(True, axis='y', alpha=0.3)  # Horizontal grid lines only
    # Remove top/bottom spines (the horizontal lines at 0 and 100)
    ax4.spines['top'].set_visible(False)
    ax4.spines['bottom'].set_visible(False)
    
    # Draw coasting zones
    if show_coast:
        for start, end in zip(coasting_starts, coasting_ends):
            ax4.axvspan(start, end, alpha=0.2, color='#38BDF8', zorder=0)
    
    # Detect and highlight OVERLAP zones (any throttle while braking = not fully lifting!)
    # Even 3% throttle while braking is feedback: "lift your foot!"
    # BUT: heel-toe blips are brief and intentional - filter those out
    overlap_mask = (df['Throttle'] > 0.02) & (df['Brake'] > 0.05)  # 2% throttle + 5% brake = foot not lifted
    
    # Find overlap spans, filtering out brief blips using TIME (sample count)
    # Estimate sample rate from data: samples / (lap time in seconds)
    # Typical lap ~51s with ~3000 samples = ~60Hz, but calculate to be robust
    estimated_sample_rate = len(df) / 51.0  # Assume ~51s lap if no timing data
    min_overlap_duration_sec = 0.4  # 400ms = blip threshold
    min_overlap_samples = int(min_overlap_duration_sec * estimated_sample_rate)
    
    overlap_starts = []
    overlap_ends = []
    in_overlap = False
    overlap_start_idx = None
    overlap_start_pct = None
    
    for i, is_overlap in enumerate(overlap_mask):
        if is_overlap and not in_overlap:
            overlap_start_idx = i
            overlap_start_pct = df['TrackPct'].iloc[i]
            in_overlap = True
        elif not is_overlap and in_overlap:
            overlap_end_pct = df['TrackPct'].iloc[i]
            sample_count = i - overlap_start_idx
            # Only keep if duration > minimum samples (filters out blips)
            if sample_count > min_overlap_samples:
                overlap_starts.append(overlap_start_pct)
                overlap_ends.append(overlap_end_pct)
            in_overlap = False
    
    if in_overlap:
        sample_count = len(df) - overlap_start_idx
        if sample_count > min_overlap_samples:
            overlap_starts.append(overlap_start_pct)
            overlap_ends.append(df['TrackPct'].iloc[-1])
    
    # Draw overlap zones (amber/orange = attention!)
    for start, end in zip(overlap_starts, overlap_ends):
        ax4.axvspan(start, end, alpha=0.3, color='#F59E0B', zorder=0)
    
    # Plot throttle and brake as LINES (both positive, 0-100%)
    # Trail braking shows as the crossover point
    ax4.plot(df['TrackPct'], df['Throttle'] * 100, 
             color=COLORS['throttle'], linewidth=2, label='Throttle', alpha=0.9)
    ax4.plot(df['TrackPct'], df['Brake'] * 100, 
             color=COLORS['brake'], linewidth=2, label='Brake', alpha=0.9)
    
    ax4.set_xlabel('Track Position (%)', fontsize=10)
    ax4.set_ylabel('Pedal %', fontsize=10)
    ax4.set_title('Pedals (trail braking view)', fontsize=11, fontweight='bold')
    ax4.set_xlim(0, 100)
    ax4.set_ylim(0, 100)  # Exact 0-100 range, no padding
    # Add overlap info to legend if any detected
    if len(overlap_starts) > 0:
        overlap_pct = overlap_mask.sum() / len(overlap_mask) * 100
        ax4.plot([], [], ' ', label=f'Overlap ({overlap_pct:.1f}%)')
    ax4.legend(loc='upper right', fontsize=9, framealpha=0.9)
    
    
    # Save or show
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"✅ Saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()
    
    # Print summary
    print_telemetry_summary(df)


def print_telemetry_summary(df: pd.DataFrame):
    """Print key telemetry statistics."""
    print("\n" + "="*60)
    print("TELEMETRY SUMMARY")
    print("="*60)
    
    print(f"\n📊 Data points: {len(df)}")
    print(f"\n🏎️  Speed:")
    print(f"   Max: {df['Speed'].max() * 3.6:.0f} km/h")
    print(f"   Min: {df['Speed'].min() * 3.6:.0f} km/h")
    print(f"   Avg: {df['Speed'].mean() * 3.6:.0f} km/h")
    
    print(f"\n⚙️  Gears used: {int(df['Gear'].min())} - {int(df['Gear'].max())}")
    
    pedals_cfg = pedals()
    throttle_threshold = pedals_cfg.throttle_on
    brake_threshold = pedals_cfg.brake_on
    coast_accel_threshold = pedals_cfg.coast_long_accel
    full_throttle_pct = (df['Throttle'] > 0.95).sum() / len(df) * 100
    braking_pct = (df['Brake'] > brake_threshold).sum() / len(df) * 100
    coast_mask = (df['Throttle'] < throttle_threshold) & (df['Brake'] < brake_threshold)
    if 'LongAccel' in df.columns:
        coast_mask &= df['LongAccel'].abs() < coast_accel_threshold
    coasting_pct = coast_mask.sum() / len(df) * 100
    
    print(f"\n🦶 Pedal usage:")
    print(f"   Full throttle: {full_throttle_pct:.1f}%")
    print(f"   Braking: {braking_pct:.1f}%")
    print(f"   Coasting: {coasting_pct:.1f}%")
    
    print(f"\n💫 G-forces:")
    print(f"   Max lateral: {abs(df['LatAccel']).max() / 9.81:.2f}g")
    print(f"   Max braking: {abs(df['LongAccel'].min()) / 9.81:.2f}g")
    print(f"   Max accel: {df['LongAccel'].max() / 9.81:.2f}g")


def main():
    parser = argparse.ArgumentParser(description="Visualize Garage 61 lap telemetry")
    parser.add_argument("csv_file", type=Path, help="Path to telemetry CSV")
    parser.add_argument("--output", "-o", type=Path, help="Output image path")
    parser.add_argument("--title", "-t", type=str, help="Custom title")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"❌ File not found: {args.csv_file}")
        return 1
    
    print(f"Loading telemetry from {args.csv_file}...")
    df = load_telemetry(args.csv_file)
    print(f"Loaded {len(df)} data points")
    
    # Extract lap time from filename if possible
    filename = args.csv_file.stem
    title = args.title
    if not title:
        # Try to extract lap time from filename (format: ... - 00.51.148 - ...)
        parts = filename.split(' - ')
        for part in parts:
            if part.startswith('00.') or part.startswith('01.'):
                lap_time = part.replace('.', ':', 1)  # 00.51.148 -> 00:51.148
                title = f"Lap Analysis: {lap_time}"
                break
        if not title:
            title = "Lap Telemetry Analysis"
    
    # Determine output path
    output_path = args.output
    if not output_path:
        output_path = args.csv_file.parent / f"{args.csv_file.stem}-telemetry.png"
    
    create_telemetry_visualization(df, title=title, output_path=output_path)
    
    return 0


if __name__ == "__main__":
    exit(main())

