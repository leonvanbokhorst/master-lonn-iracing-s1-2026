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
import numpy as np

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


def load_telemetry(csv_path: Path) -> pd.DataFrame:
    """Load telemetry CSV from Garage61."""
    df = pd.read_csv(csv_path)
    
    # Convert LapDistPct to percentage (0-100)
    df['TrackPct'] = df['LapDistPct'] * 100
    
    return df


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
    
    # Classify each point by pedal state
    # Brake threshold must be very low - even 2 bar (5% of 40 bar) is real trail braking!
    throttle_threshold = 0.05  # 5% throttle = "on throttle"
    brake_threshold = 0.01     # 1% brake = truly off brake (0.4 bar of 40 bar max)
    
    x = df['TrackPct'].values
    y = df['Speed'].values * 3.6  # Convert m/s to km/h
    throttle = df['Throttle'].values
    brake = df['Brake'].values
    
    # Identify and draw coasting zones as vertical bands (same as throttle/brake graph)
    coasting_mask = (df['Throttle'] < throttle_threshold) & (df['Brake'] < brake_threshold)
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
    
    # Draw coasting zones behind everything
    for start, end in zip(coasting_starts, coasting_ends):
        ax1.axvspan(start, end, alpha=0.25, color='#38BDF8', zorder=0)
    
    # Plot speed trace colored by pedal state (segment by segment)
    for i in range(len(x) - 1):
        # Determine color based on pedal state
        if brake[i] > brake_threshold:
            color = COLORS['brake']  # Braking = red
            alpha = 0.9
        elif throttle[i] > throttle_threshold:
            color = COLORS['throttle']  # Throttle = green
            alpha = 0.9
        else:
            # Coasting = thin, light, dashed - "nothing happening here"
            ax1.plot(x[i:i+2], y[i:i+2], color='#D1D5DB', linewidth=1.5, 
                    alpha=0.6, linestyle='--')
            continue
        
        ax1.plot(x[i:i+2], y[i:i+2], color=color, linewidth=2.5, alpha=alpha, solid_capstyle='round')
    
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
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=COLORS['throttle'], linewidth=3, label='Throttle'),
        Line2D([0], [0], color=COLORS['brake'], linewidth=3, label='Braking'),
        Line2D([0], [0], color='#D1D5DB', linewidth=1.5, linestyle='--', label='Coasting'),
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.95)
    
    ax1.set_xlabel('Track Position (%)', fontsize=11)
    ax1.set_ylabel('Speed (km/h)', fontsize=11)
    ax1.set_title('Speed Trace (colored by pedal input)', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, df['Speed'].max() * 3.6 * 1.1)
    
    # Calculate coasting zones (used by track map and throttle/brake graph)
    coasting_mask = (df['Throttle'] < throttle_threshold) & (df['Brake'] < brake_threshold)
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
    
    from matplotlib.patches import Patch
    
    # ========== 3. TRACK MAP COLORED BY PEDAL STATE (full width, row 2) ==========
    ax3 = fig.add_subplot(gs[2])  # Full width, bottom row
    ax3.set_facecolor('#FAFAFA')
    
    # Plot track by pedal state - coasting as gaps (very faint)
    throttle_mask = df['Throttle'] > throttle_threshold
    brake_mask = df['Brake'] > brake_threshold
    coast_mask = ~throttle_mask & ~brake_mask
    
    # Coasting = tiny, faint dots (gaps in the action)
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
    ax3.set_title('Track Map (colored by pedal input)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('')
    ax3.set_ylabel('')
    ax3.set_xticks([])
    ax3.set_yticks([])
    
    # Custom legend
    legend_elements = [
        Patch(facecolor=COLORS['throttle'], label='Throttle'),
        Patch(facecolor=COLORS['brake'], label='Braking'),
        Patch(facecolor='#D1D5DB', alpha=0.3, label='Coasting (gaps)'),
    ]
    ax3.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.95)
    
    # ========== 4. PEDALS (trail braking view) ==========
    ax4 = fig.add_subplot(gs[1])  # Full width, middle row (aligned with speed trace)
    ax4.set_facecolor('#FAFAFA')
    ax4.grid(True, axis='y', alpha=0.3)  # Horizontal grid lines only
    # Remove top/bottom spines (the horizontal lines at 0 and 100)
    ax4.spines['top'].set_visible(False)
    ax4.spines['bottom'].set_visible(False)
    
    # Draw coasting zones
    for start, end in zip(coasting_starts, coasting_ends):
        ax4.axvspan(start, end, alpha=0.2, color='#38BDF8', zorder=0)
    
    # Detect and highlight OVERLAP zones (any throttle while braking = not fully lifting!)
    # Even 3% throttle while braking is feedback: "lift your foot!"
    # BUT: heel-toe blips are brief and intentional - filter those out
    overlap_mask = (df['Throttle'] > 0.02) & (df['Brake'] > 0.05)  # 2% throttle + 5% brake = foot not lifted
    
    # Find overlap spans, filtering out brief blips using TIME (sample count)
    # Telemetry is ~60Hz, so:
    # - Blip (~200ms) = ~12 samples
    # - Sustained (>400ms) = >24 samples = real problem
    min_overlap_samples = 24  # ~400ms at 60Hz - blips are shorter than this
    
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
    
    # Throttle/brake time
    full_throttle_pct = (df['Throttle'] > 0.95).sum() / len(df) * 100
    braking_pct = (df['Brake'] > 0.1).sum() / len(df) * 100
    coasting_pct = ((df['Throttle'] < 0.1) & (df['Brake'] < 0.1)).sum() / len(df) * 100
    
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

