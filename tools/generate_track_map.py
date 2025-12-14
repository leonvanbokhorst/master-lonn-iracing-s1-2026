#!/usr/bin/env python3
"""
Track Map Generator with Sector Coloring
Creates beautiful track maps from Garage61 telemetry exports.

Usage:
    uv run python tools/generate_track_map.py path/to/telemetry.csv
    uv run python tools/generate_track_map.py path/to/telemetry.csv --output track-map.png
    uv run python tools/generate_track_map.py path/to/telemetry.csv --sectors 0.55 0.77

The tool reads GPS coordinates from telemetry and creates a track map
with sectors color-coded and labeled.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Sector colors - vibrant and distinct
COLORS = {
    # Match the light, friendly style of the lap/pace graphs
    'S1': '#1f78b4',          # Blue
    'S2': '#e38f14',          # Orange
    'S3': '#2ca25f',          # Green
    'start_finish': '#e74c3c',# Red accent
    'sector_line': '#8c8c8c', # Mid-gray
    'background': '#FFFFFF',  # White figure background
    'track_bg': '#F5F7FA',    # Light panel background
    'track_outline': '#d0d7e2' # Soft outline for context
}


def load_telemetry(csv_path: Path) -> pd.DataFrame:
    """Load telemetry CSV and validate required columns."""
    df = pd.read_csv(csv_path)
    
    required = ['Lat', 'Lon', 'LapDistPct']
    missing = [col for col in required if col not in df.columns]
    
    if missing:
        print(f"❌ Missing required columns: {missing}")
        print(f"   Available columns: {list(df.columns)}")
        sys.exit(1)
    
    return df


def extract_track_data(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract and clean GPS coordinates and lap distance percentage."""
    # Filter out any invalid data
    valid = (
        (df['Lat'].notna()) & 
        (df['Lon'].notna()) & 
        (df['LapDistPct'].notna()) &
        (df['LapDistPct'] >= 0) &
        (df['LapDistPct'] <= 1)
    )
    
    df_clean = df[valid].copy()
    
    # Sort by lap distance to ensure continuous line
    df_clean = df_clean.sort_values('LapDistPct')
    
    lat = df_clean['Lat'].values
    lon = df_clean['Lon'].values
    dist_pct = df_clean['LapDistPct'].values
    
    return lat, lon, dist_pct


def find_sector_boundaries(dist_pct: np.ndarray, sector_splits: list[float]) -> list[int]:
    """Find indices where sectors change."""
    boundaries = []
    for split in sector_splits:
        # Find the index closest to this split point
        idx = np.argmin(np.abs(dist_pct - split))
        boundaries.append(idx)
    return boundaries


def create_track_map(
    lat: np.ndarray,
    lon: np.ndarray, 
    dist_pct: np.ndarray,
    sector_splits: list[float],
    title: str = "Track Map",
    output_path: Path | None = None,
):
    """Create the track map visualization with sector coloring."""
    
    # Convert to relative coordinates (meters-ish, for better aspect ratio)
    # Using simple equirectangular projection
    lat_center = np.mean(lat)
    lon_center = np.mean(lon)
    
    # Convert to approximate meters
    lat_scale = 111320  # meters per degree latitude
    lon_scale = 111320 * np.cos(np.radians(lat_center))  # meters per degree longitude
    
    x = (lon - lon_center) * lon_scale
    y = (lat - lat_center) * lat_scale
    
    # Find sector boundaries
    s1_end = sector_splits[0]
    s2_end = sector_splits[1]
    
    # Create masks for each sector
    s1_mask = dist_pct < s1_end
    s2_mask = (dist_pct >= s1_end) & (dist_pct < s2_end)
    s3_mask = dist_pct >= s2_end
    
    # Set up the figure with light theme to match other graphs
    fig, ax = plt.subplots(figsize=(12, 10), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['track_bg'])
    
    # Plot track outline (soft reference line)
    ax.plot(x, y, color=COLORS['track_outline'], linewidth=6, alpha=0.6, solid_capstyle='round')
    
    # Plot each sector with thick colored lines
    linewidth = 5
    
    # S1 - Blue
    if np.any(s1_mask):
        ax.plot(x[s1_mask], y[s1_mask], color=COLORS['S1'], 
                linewidth=linewidth, solid_capstyle='round', label='S1')
    
    # S2 - Orange
    if np.any(s2_mask):
        ax.plot(x[s2_mask], y[s2_mask], color=COLORS['S2'], 
                linewidth=linewidth, solid_capstyle='round', label='S2')
    
    # S3 - Green
    if np.any(s3_mask):
        ax.plot(x[s3_mask], y[s3_mask], color=COLORS['S3'], 
                linewidth=linewidth, solid_capstyle='round', label='S3')
    
    # Mark sector boundaries with small dots (no labels)
    boundaries = find_sector_boundaries(dist_pct, sector_splits)
    
    for idx in boundaries:
        ax.scatter([x[idx]], [y[idx]], color='white', 
                   s=80, zorder=10, marker='o', edgecolors=COLORS['sector_line'], linewidths=2)
    
    # Mark start/finish line (first point)
    ax.scatter([x[0]], [y[0]], color=COLORS['start_finish'], 
               s=300, zorder=15, marker='s', edgecolors='white', linewidths=3)
    ax.annotate('S/F', (x[0], y[0]), textcoords="offset points", 
               xytext=(15, -15), fontsize=12, color='white', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['start_finish'], alpha=0.9))
    
    # Add direction arrow (at 25% of lap)
    arrow_idx = np.argmin(np.abs(dist_pct - 0.25))
    arrow_idx_next = min(arrow_idx + 5, len(x) - 1)
    
    dx = x[arrow_idx_next] - x[arrow_idx]
    dy = y[arrow_idx_next] - y[arrow_idx]
    
    ax.annotate('', xy=(x[arrow_idx] + dx*2, y[arrow_idx] + dy*2), 
                xytext=(x[arrow_idx], y[arrow_idx]),
                arrowprops=dict(arrowstyle='->', color='white', lw=2))
    
    # Title and styling
    ax.set_title(title, fontsize=18, fontweight='bold', color='#2C3E50', pad=20)
    
    # Equal aspect ratio for proper track shape
    ax.set_aspect('equal')
    
    # Remove axes for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Create legend - positioned at bottom, outside track (S/F already labeled on map)
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['S1'], label='S1'),
        mpatches.Patch(facecolor=COLORS['S2'], label='S2'),
        mpatches.Patch(facecolor=COLORS['S3'], label='S3'),
    ]
    
    ax.legend(handles=legend_elements, loc='lower center', fontsize=11,
              facecolor='white', edgecolor='#d0d7e2',
              labelcolor='#2C3E50', framealpha=0.95, ncol=3,
              bbox_to_anchor=(0.5, -0.06))
    
    plt.tight_layout()
    
    # Save or show
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor=COLORS['background'], edgecolor='none')
        print(f"✅ Saved track map to: {output_path}")
    else:
        plt.show()
    
    return fig


def main():
    parser = argparse.ArgumentParser(
        description="Generate track map with sector coloring from telemetry"
    )
    parser.add_argument("csv_file", type=Path, help="Path to Garage61 telemetry CSV")
    parser.add_argument("--output", "-o", type=Path, help="Output PNG path")
    parser.add_argument("--title", "-t", type=str, default=None, 
                       help="Map title (auto-detected from filename if not provided)")
    parser.add_argument("--sectors", nargs=2, type=float, default=[0.55, 0.77],
                       metavar=('S1_END', 'S2_END'),
                       help="Sector split points as fractions (default: 0.55 0.77)")
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"❌ File not found: {args.csv_file}")
        sys.exit(1)
    
    # Auto-detect title from filename if not provided
    if args.title is None:
        # Try to extract track name from Garage61 filename format
        filename = args.csv_file.stem
        if " - " in filename:
            parts = filename.split(" - ")
            # Format: "Garage 61 - Driver - Car - Track - Time - ID"
            if len(parts) >= 4:
                args.title = parts[3]  # Track name
            else:
                args.title = filename
        else:
            args.title = filename
    
    # Auto-detect output path if not provided
    if args.output is None:
        args.output = args.csv_file.parent / f"{args.csv_file.stem}-track-map.png"
    
    print(f"📍 Loading telemetry from: {args.csv_file}")
    df = load_telemetry(args.csv_file)
    
    print(f"📊 Found {len(df)} data points")
    
    lat, lon, dist_pct = extract_track_data(df)
    print(f"🗺️  Extracted {len(lat)} valid GPS coordinates")
    
    print(f"🎨 Generating track map: {args.title}")
    print(f"   Sectors: S1 ends at {args.sectors[0]*100:.0f}%, S2 ends at {args.sectors[1]*100:.0f}%")
    
    create_track_map(
        lat=lat,
        lon=lon,
        dist_pct=dist_pct,
        sector_splits=args.sectors,
        title=args.title,
        output_path=args.output,
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

