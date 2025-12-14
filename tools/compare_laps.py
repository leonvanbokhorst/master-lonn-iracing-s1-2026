"""
Lap Comparison Tool
Compares multiple telemetry exports to visualize learning progression.

Usage:
    uv run python tools/compare_laps.py results/week01/
    uv run python tools/compare_laps.py results/week01/ --output images/week01/lap-comparison.png
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Add parent to path for config import when running as script
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.config import pedals, visualization, COLORS

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')


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
    # Use rglob to find CSVs in subdirectories (like data/processed/)
    seen_ulids = set()
    
    for csv_file in directory.rglob("*.csv"):
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
            if ulid not in seen_ulids:
                seen_ulids.add(ulid)
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
    """Create a focused lap comparison visualization showing The Journey: First → Best → Latest."""
    
    n_laps = len(laps)
    if n_laps < 2:
        print("❌ Need at least 2 laps to compare!")
        return
    
    # === THE JOURNEY: Select First, Best, Latest ===
    first_lap = laps[0]
    best_idx = min(range(len(laps)), key=lambda i: laps[i][1]['lap_time'])
    best_lap = laps[best_idx]
    latest_lap = laps[-1]
    
    # Build journey laps (deduplicate if best=first or best=latest)
    journey_laps = []
    journey_labels = []
    journey_colors = [COLORS['first'], COLORS['best'], COLORS['latest']]
    
    journey_laps.append(first_lap)
    journey_labels.append(f"First (#{first_lap[1]['event_num']}): {first_lap[1]['lap_time']:.3f}s")
    
    if best_idx != 0 and best_idx != len(laps) - 1:
        journey_laps.append(best_lap)
        journey_labels.append(f"Best (#{best_lap[1]['event_num']}): {best_lap[1]['lap_time']:.3f}s")
    
    if len(laps) > 1:
        journey_laps.append(latest_lap)
        best_marker = " ⭐" if best_idx == len(laps) - 1 else ""
        journey_labels.append(f"Latest (#{latest_lap[1]['event_num']}): {latest_lap[1]['lap_time']:.3f}s{best_marker}")
    
    n_journey = len(journey_laps)
    
    # Create figure - cleaner 3-row layout (removed corner speed chart)
    fig = plt.figure(figsize=(16, 12))
    
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 1],
                          hspace=0.35, wspace=0.25,
                          left=0.06, right=0.98, top=0.93, bottom=0.06)
    
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97)
    
    # ========== 1. SPEED TRACE: THE JOURNEY (full width) ==========
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor('#FAFAFA')
    
    # Plot all three with equal weight - let the delta chart below tell the details
    vis_cfg = visualization()
    for i, ((df, info), label) in enumerate(zip(journey_laps, journey_labels)):
        color = journey_colors[i % len(journey_colors)]
        ax1.plot(df['TrackPct'], df['Speed'] * 3.6, color=color, 
                linewidth=2.0, alpha=vis_cfg.trace_alpha, label=label)
    
    ax1.set_xlabel('Track Position (%)', fontsize=11)
    ax1.set_ylabel('Speed (km/h)', fontsize=11)
    ax1.set_title('The Journey: First → Best → Latest', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 100)
    ax1.legend(loc='upper right', fontsize=10, framealpha=0.95)
    
    # ========== 2. SPEED DELTA: Where did the time come from? (left) ==========
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#FAFAFA')
    
    ref_df = first_lap[0]  # First lap as reference
    track_positions = np.linspace(0, 100, 500)
    ref_speed = np.interp(track_positions, ref_df['TrackPct'], ref_df['Speed'])
    
    # Only show Best and Latest vs First (cleaner)
    compare_laps = [(best_lap, 'Best', COLORS['best']), (latest_lap, 'Latest', COLORS['latest'])]
    if best_idx == len(laps) - 1:
        compare_laps = [(latest_lap, 'Latest (Best)', COLORS['best'])]
    elif best_idx == 0:
        compare_laps = [(latest_lap, 'Latest', COLORS['latest'])]
    
    for (df, info), label, color in compare_laps:
        compare_speed = np.interp(track_positions, df['TrackPct'], df['Speed'])
        speed_diff = compare_speed - ref_speed  # Positive = faster
        ax2.plot(track_positions, speed_diff, color=color, linewidth=2, 
                alpha=0.9, label=f"{label} vs First")
    
    ax2.axhline(y=0, color='#999', linewidth=1, linestyle='--')
    
    ax2.set_xlabel('Track Position (%)', fontsize=11)
    ax2.set_ylabel('Speed Δ (vs First)', fontsize=11)
    ax2.set_title('Where did the speed come from?', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 100)
    ax2.legend(loc='upper right', fontsize=10)
    
    # Add green/red zones
    ylim = ax2.get_ylim()
    max_y = max(abs(ylim[0]), abs(ylim[1]))
    ax2.set_ylim(-max_y * 1.1, max_y * 1.1)
    ylim = ax2.get_ylim()
    ax2.fill_between([0, 100], [0, 0], [ylim[1], ylim[1]], alpha=0.08, color='#1B998B')
    ax2.fill_between([0, 100], [ylim[0], ylim[0]], [0, 0], alpha=0.08, color='#E94F37')
    ax2.text(2, ylim[1]*0.85, 'FASTER', fontsize=9, color='#1B998B', fontweight='bold', alpha=0.7)
    ax2.text(2, ylim[0]*0.85, 'SLOWER', fontsize=9, color='#E94F37', fontweight='bold', alpha=0.7)
    
    # Build journey short labels for charts
    journey_short_labels = ['First', 'Best', 'Latest'][:n_journey]
    if best_idx == len(laps) - 1:
        journey_short_labels = ['First', 'Latest ⭐']
    elif best_idx == 0:
        journey_short_labels = ['First ⭐', 'Latest']
    
    # ========== 3. TECHNIQUE: The Journey metrics (right of delta) ==========
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#FAFAFA')
    
    metrics = {
        'Full Throttle': [],
        'Braking': [],
        'Coasting': [],
    }
    
    # Use thresholds from config
    pedals_cfg = pedals()
    
    for df, info in journey_laps:
        full_throttle = (df['Throttle'] > pedals_cfg.throttle_full).sum() / len(df) * 100
        braking = (df['Brake'] > pedals_cfg.brake_on).sum() / len(df) * 100
        coasting = ((df['Throttle'] < pedals_cfg.throttle_on) & (df['Brake'] < pedals_cfg.brake_on)).sum() / len(df) * 100
        
        metrics['Full Throttle'].append(full_throttle)
        metrics['Braking'].append(braking)
        metrics['Coasting'].append(coasting)
    
    x_pos = np.arange(n_journey)
    bar_width = 0.25
    
    metric_colors = ['#1B998B', '#E94F37', '#94A3B8']
    for j, (metric_name, values) in enumerate(metrics.items()):
        offset = (j - 1) * bar_width
        ax4.bar(x_pos + offset, values, bar_width * 0.85, 
               color=metric_colors[j], alpha=0.8, label=metric_name, edgecolor='white', linewidth=1)
    
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(journey_short_labels, fontsize=11)
    ax4.set_ylabel('% of Lap', fontsize=11)
    ax4.set_title('Pedal Technique Evolution', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right', fontsize=10)
    
    # ========== 4. LAP TIME: Full progression with journey highlighted (full width) ==========
    ax5 = fig.add_subplot(gs[2, :])
    ax5.set_facecolor('#FAFAFA')
    
    lap_times = [info['lap_time'] for _, info in laps]
    event_nums = [info['event_num'] for _, info in laps]
    
    # Color bars: journey events highlighted, others muted
    bar_colors = []
    for i, (_, info) in enumerate(laps):
        if i == 0:
            bar_colors.append(COLORS['first'])
        elif i == best_idx:
            bar_colors.append(COLORS['best'])
        elif i == len(laps) - 1:
            bar_colors.append(COLORS['latest'])
        else:
            bar_colors.append(COLORS['muted'])
    
    bars = ax5.bar(event_nums, lap_times, color=bar_colors,
                  alpha=0.9, edgecolor='white', linewidth=1.5)
    
    # Add lap time labels
    for i, (bar, lap_time) in enumerate(zip(bars, lap_times)):
        fontweight = 'bold' if i in [0, best_idx, len(laps)-1] else 'normal'
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{lap_time:.3f}', ha='center', va='bottom', fontsize=9, fontweight=fontweight)
    
    # Add delta labels for highlighted events only (use set to avoid duplicates when best=latest)
    first_time = lap_times[0]
    for i in {best_idx, len(laps)-1}:  # Set deduplicates when best_idx == len(laps)-1
        if i > 0:
            delta = lap_times[i] - first_time
            ax5.text(event_nums[i], lap_times[i] - 0.12,
                    f'{delta:+.3f}', ha='center', va='top', fontsize=9,
                    fontweight='bold', color='white')
    
    ax5.set_xlabel('Event #', fontsize=11)
    ax5.set_ylabel('Lap Time (s)', fontsize=11)
    ax5.set_title('Best Lap Progression (Journey highlighted)', fontsize=12, fontweight='bold')
    
    # Adjust y-axis
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
    print_comparison_summary(laps)


def print_comparison_summary(laps: list[tuple[pd.DataFrame, dict]]):
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
    
    # Technique evolution
    print(f"\n🦶 Technique evolution:")
    first_df = laps[0][0]
    last_df = laps[-1][0]
    
    # Use thresholds from config
    pedals_cfg = pedals()
    coast_first = ((first_df['Throttle'] < pedals_cfg.throttle_on) & (first_df['Brake'] < pedals_cfg.brake_on)).sum() / len(first_df) * 100
    coast_last = ((last_df['Throttle'] < pedals_cfg.throttle_on) & (last_df['Brake'] < pedals_cfg.brake_on)).sum() / len(last_df) * 100
    
    print(f"   Coasting: {coast_first:.1f}% → {coast_last:.1f}% ({coast_last - coast_first:+.1f}%)")
    
    throttle_first = (first_df['Throttle'] > pedals_cfg.throttle_full).sum() / len(first_df) * 100
    throttle_last = (last_df['Throttle'] > pedals_cfg.throttle_full).sum() / len(last_df) * 100
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
        # Try parent dir if current is 'data'
        dir_name = args.directory.name
        if dir_name.lower() == 'data':
            dir_name = args.directory.parent.name
        
        # Handle weekXX pattern, otherwise use directory name as-is
        if dir_name.lower().startswith('week'):
            week_name = dir_name.replace('week', 'Week ').replace('Week 0', 'Week ')
        else:
            week_name = dir_name.title()
        title = f"{week_name} Best Lap Evolution"
    
    # Output path
    output_path = args.output
    if not output_path:
        # New structure: weeks/weekXX/data/ → weeks/weekXX/images/
        output_path = args.directory.parent / "images" / "lap-comparison.png"
    
    create_comparison_visualization(laps, title=title, output_path=output_path)
    
    return 0


if __name__ == "__main__":
    exit(main())

