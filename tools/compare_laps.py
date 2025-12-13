"""
Lap Comparison Tool
Compares multiple telemetry exports to visualize learning progression.

Usage:
    uv run python tools/compare_laps.py results/week01/
    uv run python tools/compare_laps.py results/week01/ --output images/week01/lap-comparison.png
"""

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')

# Colors for laps (chronological order)
LAP_COLORS = ['#E94F37', '#F6AE2D', '#33A1FD', '#1B998B', '#A23B72', '#2E86AB']


def decode_ulid_timestamp(ulid: str) -> int:
    """Extract approximate timestamp ordering from ULID (first 10 chars encode time)."""
    # ULID uses Crockford's base32: 0123456789ABCDEFGHJKMNPQRSTVWXYZ
    # First 10 characters encode 48-bit timestamp (milliseconds since Unix epoch)
    # For sorting purposes, we can just compare the string prefix lexicographically
    return ulid[:10]


def load_telemetry_files(directory: Path) -> list[tuple[pd.DataFrame, dict]]:
    """Load all telemetry CSVs from directory, sorted chronologically."""
    
    telemetry_files = []
    
    # Find telemetry files (they have lap times and ULIDs in filename)
    for csv_file in directory.glob("*.csv"):
        filename = csv_file.name
        
        # Telemetry files have format: "... - 00.XX.XXX - ULID.csv"
        # Check if this looks like a telemetry file (has lap time pattern)
        parts = filename.replace('.csv', '').split(' - ')
        
        lap_time = None
        ulid = None
        
        for i, part in enumerate(parts):
            # Look for lap time pattern (00.XX.XXX or 01.XX.XXX)
            if part.startswith('00.') or part.startswith('01.'):
                if '.' in part[3:]:  # Has decimal in lap time
                    try:
                        # Parse lap time: 00.51.148 -> 51.148 seconds
                        time_parts = part.split('.')
                        if len(time_parts) == 3:
                            minutes = int(time_parts[0])
                            seconds = int(time_parts[1])
                            millis = int(time_parts[2])
                            lap_time = minutes * 60 + seconds + millis / 1000
                            
                            # Next part should be ULID
                            if i + 1 < len(parts):
                                ulid = parts[i + 1]
                    except (ValueError, IndexError):
                        continue
        
        if lap_time and ulid:
            telemetry_files.append({
                'path': csv_file,
                'lap_time': lap_time,
                'ulid': ulid,
                'sort_key': decode_ulid_timestamp(ulid)
            })
    
    # Sort by ULID timestamp (chronological order)
    telemetry_files.sort(key=lambda x: x['sort_key'])
    
    # Load each file
    laps = []
    for i, file_info in enumerate(telemetry_files):
        df = pd.read_csv(file_info['path'])
        df['TrackPct'] = df['LapDistPct'] * 100
        
        info = {
            'event_num': i + 1,
            'lap_time': file_info['lap_time'],
            'ulid': file_info['ulid'],
            'filename': file_info['path'].name
        }
        
        laps.append((df, info))
    
    return laps


def calculate_speed_delta(df_ref: pd.DataFrame, df_compare: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Calculate cumulative time delta between two laps based on speed."""
    
    # Resample both laps to common track positions
    track_positions = np.linspace(0, 100, 500)
    
    # Interpolate speed at each position
    speed_ref = np.interp(track_positions, df_ref['TrackPct'], df_ref['Speed'])
    speed_compare = np.interp(track_positions, df_compare['TrackPct'], df_compare['Speed'])
    
    # Calculate time per segment (assuming equal distance segments)
    # Time = Distance / Speed
    # For relative comparison, we can use 1/speed as proxy
    segment_length = 100 / len(track_positions)  # Percentage of track per segment
    
    # Avoid division by zero
    speed_ref = np.maximum(speed_ref, 0.1)
    speed_compare = np.maximum(speed_compare, 0.1)
    
    # Time difference per segment (positive = compare is slower)
    time_diff = segment_length * (1/speed_compare - 1/speed_ref)
    
    # Cumulative delta
    cumulative_delta = np.cumsum(time_diff)
    
    # Normalize so that final value matches actual lap time difference
    actual_delta = df_compare['LapDistPct'].iloc[-1] - df_ref['LapDistPct'].iloc[-1]
    
    return track_positions, cumulative_delta


def create_comparison_visualization(
    laps: list[tuple[pd.DataFrame, dict]],
    title: str = "Lap Comparison",
    output_path: Path = None
):
    """Create a comprehensive lap comparison visualization."""
    
    n_laps = len(laps)
    if n_laps < 2:
        print("❌ Need at least 2 laps to compare!")
        return
    
    # Create figure
    fig = plt.figure(figsize=(16, 14))
    
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 1],
                          hspace=0.3, wspace=0.25,
                          left=0.06, right=0.98, top=0.92, bottom=0.05)
    
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97)
    
    # ========== 1. SPEED TRACE OVERLAY (full width) ==========
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor('#FAFAFA')
    
    for i, (df, info) in enumerate(laps):
        color = LAP_COLORS[i % len(LAP_COLORS)]
        label = f"#{info['event_num']}: {info['lap_time']:.3f}s"
        ax1.plot(df['TrackPct'], df['Speed'], color=color, 
                linewidth=1.5 if i == len(laps)-1 else 1.0,
                alpha=0.9 if i == len(laps)-1 else 0.6,
                label=label)
    
    ax1.set_xlabel('Track Position (%)', fontsize=11)
    ax1.set_ylabel('Speed', fontsize=11)
    ax1.set_title('Speed Trace Evolution (all best laps)', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 100)
    ax1.legend(loc='upper right', fontsize=9)
    
    # ========== 2. SPEED DIFFERENCE FROM FIRST LAP (left) ==========
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#FAFAFA')
    
    ref_df = laps[0][0]  # First lap as reference
    track_positions = np.linspace(0, 100, 500)
    ref_speed = np.interp(track_positions, ref_df['TrackPct'], ref_df['Speed'])
    
    for i, (df, info) in enumerate(laps[1:], start=1):  # Skip first lap
        color = LAP_COLORS[i % len(LAP_COLORS)]
        compare_speed = np.interp(track_positions, df['TrackPct'], df['Speed'])
        speed_diff = compare_speed - ref_speed  # Positive = faster
        
        label = f"#{info['event_num']} vs #1"
        ax2.plot(track_positions, speed_diff, color=color, linewidth=1.2, 
                alpha=0.8, label=label)
    
    ax2.axhline(y=0, color='#999', linewidth=1, linestyle='--')
    ax2.fill_between(track_positions, 0, 0, alpha=0)  # Dummy for consistent ylim
    
    ax2.set_xlabel('Track Position (%)', fontsize=11)
    ax2.set_ylabel('Speed Δ (vs Event #1)', fontsize=11)
    ax2.set_title('Speed Gain/Loss vs First Lap', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 100)
    ax2.legend(loc='upper right', fontsize=9)
    
    # Add green/red zones
    ylim = ax2.get_ylim()
    ax2.fill_between([0, 100], [0, 0], [ylim[1], ylim[1]], alpha=0.05, color='green')
    ax2.fill_between([0, 100], [ylim[0], ylim[0]], [0, 0], alpha=0.05, color='red')
    ax2.text(2, ylim[1]*0.8, 'FASTER', fontsize=8, color='green', alpha=0.5)
    ax2.text(2, ylim[0]*0.8, 'SLOWER', fontsize=8, color='red', alpha=0.5)
    
    # ========== 3. MIN CORNER SPEED PROGRESSION (right) ==========
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor('#FAFAFA')
    
    # Define approximate corner locations (percentage of track)
    # For Jefferson Circuit - these are rough estimates based on speed trace
    corners = {
        'T1-2': (12, 22),
        'Esses': (28, 42),
        'T6': (48, 58),
        'Carousel': (72, 92),
    }
    
    corner_names = list(corners.keys())
    x_pos = np.arange(len(corner_names))
    bar_width = 0.8 / n_laps
    
    for i, (df, info) in enumerate(laps):
        min_speeds = []
        for corner_name, (start, end) in corners.items():
            mask = (df['TrackPct'] >= start) & (df['TrackPct'] <= end)
            min_speed = df.loc[mask, 'Speed'].min() if mask.any() else 0
            min_speeds.append(min_speed)
        
        color = LAP_COLORS[i % len(LAP_COLORS)]
        offset = (i - n_laps/2 + 0.5) * bar_width
        bars = ax3.bar(x_pos + offset, min_speeds, bar_width * 0.9, 
                      color=color, alpha=0.7, label=f"#{info['event_num']}")
    
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(corner_names, fontsize=10)
    ax3.set_ylabel('Min Speed', fontsize=11)
    ax3.set_title('Corner Minimum Speed (higher = better)', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9)
    
    # ========== 4. TECHNIQUE METRICS (left) ==========
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.set_facecolor('#FAFAFA')
    
    metrics = {
        'Full Throttle %': [],
        'Braking %': [],
        'Coasting %': [],
    }
    
    for df, info in laps:
        full_throttle = (df['Throttle'] > 0.95).sum() / len(df) * 100
        braking = (df['Brake'] > 0.1).sum() / len(df) * 100
        coasting = ((df['Throttle'] < 0.1) & (df['Brake'] < 0.1)).sum() / len(df) * 100
        
        metrics['Full Throttle %'].append(full_throttle)
        metrics['Braking %'].append(braking)
        metrics['Coasting %'].append(coasting)
    
    x_pos = np.arange(n_laps)
    bar_width = 0.25
    
    for j, (metric_name, values) in enumerate(metrics.items()):
        offset = (j - 1) * bar_width
        color = ['#1B998B', '#E94F37', '#999'][j]
        ax4.bar(x_pos + offset, values, bar_width * 0.9, 
               color=color, alpha=0.7, label=metric_name)
    
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f"#{info['event_num']}" for _, info in laps], fontsize=10)
    ax4.set_ylabel('% of Lap', fontsize=11)
    ax4.set_title('Pedal Technique Evolution', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right', fontsize=9)
    
    # ========== 5. LAP TIME PROGRESSION (right) ==========
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.set_facecolor('#FAFAFA')
    
    lap_times = [info['lap_time'] for _, info in laps]
    event_nums = [info['event_num'] for _, info in laps]
    
    bars = ax5.bar(event_nums, lap_times, color=[LAP_COLORS[i % len(LAP_COLORS)] for i in range(n_laps)],
                  alpha=0.8, edgecolor='white', linewidth=1.5)
    
    # Add lap time labels
    for bar, lap_time in zip(bars, lap_times):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{lap_time:.3f}', ha='center', va='bottom', fontsize=10)
    
    # Add delta labels
    for i in range(1, len(lap_times)):
        delta = lap_times[i] - lap_times[0]
        color = '#1B998B' if delta < 0 else '#E94F37'
        ax5.text(event_nums[i], lap_times[i] - 0.15,
                f'{delta:+.3f}', ha='center', va='top', fontsize=9,
                fontweight='bold', color='white')
    
    ax5.set_xlabel('Event #', fontsize=11)
    ax5.set_ylabel('Lap Time (s)', fontsize=11)
    ax5.set_title('Best Lap Progression', fontsize=12, fontweight='bold')
    
    # Adjust y-axis to show differences clearly
    y_min = min(lap_times) - 0.3
    y_max = max(lap_times) + 0.3
    ax5.set_ylim(y_min, y_max)
    
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
    print_comparison_summary(laps, corners)


def print_comparison_summary(laps: list[tuple[pd.DataFrame, dict]], corners: dict):
    """Print learning insights from lap comparison."""
    
    print("\n" + "="*70)
    print("LAP COMPARISON ANALYSIS")
    print("="*70)
    
    print(f"\n📊 Comparing {len(laps)} laps:")
    for df, info in laps:
        print(f"   #{info['event_num']}: {info['lap_time']:.3f}s")
    
    # Overall improvement
    first_time = laps[0][1]['lap_time']
    best_time = min(info['lap_time'] for _, info in laps)
    best_idx = [i for i, (_, info) in enumerate(laps) if info['lap_time'] == best_time][0]
    
    print(f"\n🎯 Total improvement: {first_time:.3f}s → {best_time:.3f}s = {first_time - best_time:+.3f}s")
    print(f"   Best lap: Event #{laps[best_idx][1]['event_num']}")
    
    # Corner analysis
    print(f"\n🔄 Corner minimum speeds:")
    print(f"   {'Corner':<12} {'#1':>8} {'Best':>8} {'Δ':>8}")
    print("   " + "-"*40)
    
    for corner_name, (start, end) in corners.items():
        first_df = laps[0][0]
        mask_first = (first_df['TrackPct'] >= start) & (first_df['TrackPct'] <= end)
        min_first = first_df.loc[mask_first, 'Speed'].min() if mask_first.any() else 0
        
        best_corner = min_first
        best_event = 1
        for i, (df, info) in enumerate(laps):
            mask = (df['TrackPct'] >= start) & (df['TrackPct'] <= end)
            min_speed = df.loc[mask, 'Speed'].min() if mask.any() else 0
            if min_speed > best_corner:
                best_corner = min_speed
                best_event = info['event_num']
        
        delta = best_corner - min_first
        print(f"   {corner_name:<12} {min_first:>7.1f} {best_corner:>7.1f} {delta:>+7.1f}")
    
    # Technique evolution
    print(f"\n🦶 Technique evolution:")
    first_df = laps[0][0]
    last_df = laps[-1][0]
    
    coast_first = ((first_df['Throttle'] < 0.1) & (first_df['Brake'] < 0.1)).sum() / len(first_df) * 100
    coast_last = ((last_df['Throttle'] < 0.1) & (last_df['Brake'] < 0.1)).sum() / len(last_df) * 100
    
    print(f"   Coasting: {coast_first:.1f}% → {coast_last:.1f}% ({coast_last - coast_first:+.1f}%)")
    
    throttle_first = (first_df['Throttle'] > 0.95).sum() / len(first_df) * 100
    throttle_last = (last_df['Throttle'] > 0.95).sum() / len(last_df) * 100
    print(f"   Full throttle: {throttle_first:.1f}% → {throttle_last:.1f}% ({throttle_last - throttle_first:+.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Compare lap telemetry for learning analysis")
    parser.add_argument("directory", type=Path, help="Directory containing telemetry CSVs")
    parser.add_argument("--output", "-o", type=Path, help="Output image path")
    parser.add_argument("--title", "-t", type=str, help="Custom title")
    
    args = parser.parse_args()
    
    if not args.directory.exists():
        print(f"❌ Directory not found: {args.directory}")
        return 1
    
    print(f"Loading telemetry files from {args.directory}...")
    laps = load_telemetry_files(args.directory)
    
    if len(laps) < 2:
        print(f"❌ Found only {len(laps)} telemetry file(s). Need at least 2 to compare.")
        return 1
    
    print(f"Found {len(laps)} telemetry files (chronological order):")
    for df, info in laps:
        print(f"  #{info['event_num']}: {info['lap_time']:.3f}s")
    
    # Generate title
    title = args.title
    if not title:
        week_name = args.directory.name.upper()
        title = f"{week_name} – Learning Progression ({len(laps)} Best Laps)"
    
    # Output path
    output_path = args.output
    if not output_path:
        # New structure: weeks/weekXX/data/ → weeks/weekXX/images/
        output_path = args.directory.parent / "images" / "lap-comparison.png"
    
    create_comparison_visualization(laps, title=title, output_path=output_path)
    
    return 0


if __name__ == "__main__":
    exit(main())

