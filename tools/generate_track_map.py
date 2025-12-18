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
    'start_finish': '#e74c3c',   # Red accent
    'sector_line': '#8c8c8c',    # Mid-gray
    'background': '#FFFFFF',     # White figure background
    'track_bg': '#F5F7FA',       # Light panel background
    'track_outline': '#d0d7e2',  # Soft outline for context
}

# Default palette for up to 6 sectors (wraps if more are requested)
SECTOR_COLORS = [
    '#1f78b4',  # S1 - Blue
    '#e38f14',  # S2 - Orange
    '#2ca25f',  # S3 - Green
    '#8f3f97',  # S4 - Purple
    '#f15a24',  # S5 - Orange-red
    '#17becf',  # S6 - Teal
]


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
    splits = sorted({split for split in sector_splits if 0 < split < 1})
    
    # Create boolean masks for each sector (n splits => n+1 sectors)
    split_bounds = [0.0] + splits + [1.0000001]
    sector_masks: list[np.ndarray] = []
    for idx in range(len(split_bounds) - 1):
        start = split_bounds[idx]
        end = split_bounds[idx + 1]
        if idx == len(split_bounds) - 2:
            mask = dist_pct >= start
        else:
            mask = (dist_pct >= start) & (dist_pct < end)
        sector_masks.append(mask)
    
    # Set up the figure with light theme to match other graphs
    fig, ax = plt.subplots(figsize=(12, 10), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['track_bg'])
    
    # Plot track outline (soft reference line)
    ax.plot(x, y, color=COLORS['track_outline'], linewidth=6, alpha=0.6, solid_capstyle='round')
    
    # Plot each sector with thick colored lines
    linewidth = 5
    legend_elements: list[mpatches.Patch] = []
    
    for idx, mask in enumerate(sector_masks):
        if not np.any(mask):
            continue
        color = SECTOR_COLORS[idx % len(SECTOR_COLORS)]
        label = f"S{idx + 1}"
        ax.plot(
            x[mask],
            y[mask],
            color=color,
            linewidth=linewidth,
            solid_capstyle='round',
            label=label,
        )
        legend_elements.append(mpatches.Patch(facecolor=color, label=label))
    
    # Mark sector boundaries with small dots (no labels)
    boundaries = find_sector_boundaries(dist_pct, splits)
    
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
    if legend_elements:
        ax.legend(
            handles=legend_elements,
            loc='lower center',
            fontsize=11,
            facecolor='white',
            edgecolor='#d0d7e2',
            labelcolor='#2C3E50',
            framealpha=0.95,
            ncol=min(len(legend_elements), 4),
            bbox_to_anchor=(0.5, -0.06),
        )
    
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
    parser.add_argument(
        "--sectors",
        nargs="+",
        type=float,
        default=[0.55, 0.77],
        metavar="SPLIT",
        help=(
            "Sector split points as lap distance fractions (0-1). "
            "Provide N values to draw N+1 sectors. Default: 0.55 0.77"
        ),
    )
    
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
    splits = sorted({split for split in args.sectors if 0 < split < 1})
    if splits:
        split_summary = ", ".join(
            f"S{i+1} end {split*100:.1f}%" for i, split in enumerate(splits)
        )
        print(f"   Sectors: {split_summary}, S{len(splits)+1} closes the lap")
    else:
        print("   Sectors: single color (no valid split points provided)")
    
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

