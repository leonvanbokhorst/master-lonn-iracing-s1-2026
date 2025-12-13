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
    
    # Create figure with custom layout
    fig = plt.figure(figsize=(16, 12))
    
    # Grid: 3 rows, 2 columns
    # Row 1: Speed trace (full width)
    # Row 2: Throttle/Brake (left), Track map (right)
    # Row 3: Gear trace (left), G-forces (right)
    
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 1], 
                          hspace=0.3, wspace=0.25,
                          left=0.06, right=0.98, top=0.92, bottom=0.06)
    
    # Title
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97)
    
    # ========== 1. SPEED TRACE (full width) ==========
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor('#FAFAFA')
    
    ax1.plot(df['TrackPct'], df['Speed'], color=COLORS['speed'], 
             linewidth=1.5, alpha=0.9)
    ax1.fill_between(df['TrackPct'], 0, df['Speed'], 
                     color=COLORS['speed'], alpha=0.15)
    
    # Mark min/max speed
    max_idx = df['Speed'].idxmax()
    min_idx = df['Speed'].idxmin()
    ax1.scatter([df.loc[max_idx, 'TrackPct']], [df.loc[max_idx, 'Speed']], 
                color=COLORS['throttle'], s=80, zorder=5, marker='^')
    ax1.scatter([df.loc[min_idx, 'TrackPct']], [df.loc[min_idx, 'Speed']], 
                color=COLORS['brake'], s=80, zorder=5, marker='v')
    
    ax1.annotate(f'Max: {df["Speed"].max():.1f}', 
                xy=(df.loc[max_idx, 'TrackPct'], df.loc[max_idx, 'Speed']),
                xytext=(5, 10), textcoords='offset points', fontsize=9,
                color=COLORS['throttle'], fontweight='bold')
    ax1.annotate(f'Min: {df["Speed"].min():.1f}', 
                xy=(df.loc[min_idx, 'TrackPct'], df.loc[min_idx, 'Speed']),
                xytext=(5, -15), textcoords='offset points', fontsize=9,
                color=COLORS['brake'], fontweight='bold')
    
    ax1.set_xlabel('Track Position (%)', fontsize=11)
    ax1.set_ylabel('Speed', fontsize=11)
    ax1.set_title('Speed Trace', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, df['Speed'].max() * 1.1)
    
    # ========== 2. THROTTLE/BRAKE (left) ==========
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#FAFAFA')
    
    # Plot throttle and brake
    ax2.fill_between(df['TrackPct'], 0, df['Throttle'] * 100, 
                     color=COLORS['throttle'], alpha=0.6, label='Throttle')
    ax2.fill_between(df['TrackPct'], 0, -df['Brake'] * 100, 
                     color=COLORS['brake'], alpha=0.6, label='Brake')
    
    ax2.axhline(y=0, color='#666', linewidth=0.5)
    ax2.set_xlabel('Track Position (%)', fontsize=11)
    ax2.set_ylabel('Input %', fontsize=11)
    ax2.set_title('Throttle & Brake', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-105, 105)
    ax2.legend(loc='upper right', fontsize=9)
    
    # ========== 3. TRACK MAP (right) ==========
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor('#FAFAFA')
    
    # Plot track using GPS coordinates
    # Color by speed
    points = ax3.scatter(df['Lon'], df['Lat'], c=df['Speed'], 
                        cmap='RdYlGn', s=2, alpha=0.8)
    
    # Mark start/finish
    ax3.scatter([df.iloc[0]['Lon']], [df.iloc[0]['Lat']], 
                color=COLORS['track_start'], s=100, marker='o', 
                zorder=5, edgecolor='white', linewidth=2, label='Start/Finish')
    
    ax3.set_aspect('equal')
    ax3.set_title('Track Map (colored by speed)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Longitude', fontsize=10)
    ax3.set_ylabel('Latitude', fontsize=10)
    
    # Add colorbar
    cbar = plt.colorbar(points, ax=ax3, shrink=0.8, pad=0.02)
    cbar.set_label('Speed', fontsize=10)
    
    ax3.legend(loc='upper left', fontsize=9)
    
    # ========== 4. GEAR TRACE (left) ==========
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.set_facecolor('#FAFAFA')
    
    ax4.fill_between(df['TrackPct'], 0, df['Gear'], 
                     color=COLORS['gear'], alpha=0.6, step='mid')
    ax4.plot(df['TrackPct'], df['Gear'], color=COLORS['gear'], 
             linewidth=1, alpha=0.8, drawstyle='steps-mid')
    
    ax4.set_xlabel('Track Position (%)', fontsize=11)
    ax4.set_ylabel('Gear', fontsize=11)
    ax4.set_title('Gear Usage', fontsize=12, fontweight='bold')
    ax4.set_xlim(0, 100)
    ax4.set_ylim(0, df['Gear'].max() + 0.5)
    ax4.set_yticks(range(1, int(df['Gear'].max()) + 1))
    
    # ========== 5. G-FORCES (right) ==========
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.set_facecolor('#FAFAFA')
    
    # G-G diagram (lateral vs longitudinal)
    scatter = ax5.scatter(df['LatAccel'], df['LongAccel'], 
                         c=df['TrackPct'], cmap='viridis', s=3, alpha=0.5)
    
    # Add reference circles
    for g in [1, 2]:
        circle = plt.Circle((0, 0), g * 9.81, fill=False, 
                            color='#CCC', linestyle='--', linewidth=1)
        ax5.add_patch(circle)
        ax5.annotate(f'{g}g', xy=(g * 9.81 * 0.7, g * 9.81 * 0.7), 
                    fontsize=8, color='#999')
    
    ax5.axhline(y=0, color='#999', linewidth=0.5)
    ax5.axvline(x=0, color='#999', linewidth=0.5)
    ax5.set_xlabel('Lateral G (+ = right)', fontsize=11)
    ax5.set_ylabel('Longitudinal G (+ = accel)', fontsize=11)
    ax5.set_title('G-Force Diagram', fontsize=12, fontweight='bold')
    ax5.set_aspect('equal')
    
    # Set reasonable limits
    max_g = max(abs(df['LatAccel']).max(), abs(df['LongAccel']).max()) * 1.2
    ax5.set_xlim(-max_g, max_g)
    ax5.set_ylim(-max_g, max_g)
    
    cbar2 = plt.colorbar(scatter, ax=ax5, shrink=0.8, pad=0.02)
    cbar2.set_label('Track %', fontsize=10)
    
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
    print(f"   Max: {df['Speed'].max():.1f}")
    print(f"   Min: {df['Speed'].min():.1f}")
    print(f"   Avg: {df['Speed'].mean():.1f}")
    
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

