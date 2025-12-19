#!/usr/bin/env python3
"""
Hypothesis Testing Visualization
=================================

Analyzes and visualizes hypothesis testing data, showing success rates,
patterns, and the evolution of experimental learning over time.

Generates visualizations showing:
- Hypothesis status distribution
- Success rate by area
- Test result trends
- Timeline of hypothesis lifecycle

Usage:
    python tools/visualize_hypotheses.py [output_file]

Example:
    python tools/visualize_hypotheses.py
    python tools/visualize_hypotheses.py analysis/hypotheses.png

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from collections import Counter

# Hypothesis database file
HYPOTHESIS_DB = Path("coaching/hypotheses.json")


def load_hypotheses() -> dict:
    """
    Load hypotheses from JSON database.
    
    Returns:
        Dictionary of hypotheses data
    """
    if not HYPOTHESIS_DB.exists():
        return {"hypotheses": [], "next_id": 1}
    
    with open(HYPOTHESIS_DB, 'r') as f:
        return json.load(f)


def _plot_insufficient_data(ax, title: str, message: str) -> None:
    """
    Display "insufficient data" message on a subplot.
    
    Args:
        ax: Matplotlib axis object
        title: Title for the subplot
        message: Message to display
    """
    ax.text(0.5, 0.5, message, ha='center', va='center', transform=ax.transAxes)
    ax.set_title(title)


def visualize_hypotheses(output_file: Path) -> None:
    """
    Create comprehensive visualization of hypothesis testing data.
    
    Args:
        output_file: Path to save figure
    """
    data = load_hypotheses()
    hypotheses = data.get("hypotheses", [])
    
    if not hypotheses:
        print("\n📋 No hypotheses to visualize yet")
        print("   Create one with: make hypothesis-create")
        return
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (16, 10)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("Hypothesis Testing Analysis", fontsize=16, fontweight='bold')
    
    # 1. Status distribution
    ax1 = axes[0, 0]
    status_counts = Counter(h["status"] for h in hypotheses)
    
    status_labels = {
        "active": "Active",
        "confirmed": "Confirmed",
        "partially_confirmed": "Partially Confirmed",
        "rejected": "Rejected"
    }
    
    status_colors = {
        "active": "#3498db",
        "confirmed": "#2ecc71",
        "partially_confirmed": "#f39c12",
        "rejected": "#e74c3c"
    }
    
    labels = [status_labels.get(s, s) for s in status_counts.keys()]
    sizes = list(status_counts.values())
    colors = [status_colors.get(s, "#95a5a6") for s in status_counts.keys()]
    
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, textprops={'fontsize': 10})
    ax1.set_title("Hypothesis Status Distribution")
    
    # 2. Success rate by area
    ax2 = axes[0, 1]
    
    # Group by area
    area_stats = {}
    for h in hypotheses:
        area = h.get("area", "Unknown")
        if area not in area_stats:
            area_stats[area] = {"total": 0, "confirmed": 0, "partial": 0}
        
        area_stats[area]["total"] += 1
        if h["status"] == "confirmed":
            area_stats[area]["confirmed"] += 1
        elif h["status"] == "partially_confirmed":
            area_stats[area]["partial"] += 1
    
    if area_stats:
        areas = list(area_stats.keys())
        confirmed_rates = [(area_stats[a]["confirmed"] / area_stats[a]["total"]) * 100 
                          for a in areas]
        partial_rates = [(area_stats[a]["partial"] / area_stats[a]["total"]) * 100 
                        for a in areas]
        
        x = np.arange(len(areas))
        width = 0.35
        
        bars1 = ax2.bar(x - width/2, confirmed_rates, width, label='Confirmed', 
                       color='#2ecc71', alpha=0.8)
        bars2 = ax2.bar(x + width/2, partial_rates, width, label='Partially Confirmed',
                       color='#f39c12', alpha=0.8)
        
        ax2.set_xlabel("Focus Area")
        ax2.set_ylabel("Success Rate (%)")
        ax2.set_title("Success Rate by Focus Area")
        ax2.set_xticks(x)
        ax2.set_xticklabels(areas, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
    else:
        _plot_insufficient_data(
            ax2,
            "Success Rate by Focus Area",
            "No concluded hypotheses yet"
        )
    
    # 3. Test result trends
    ax3 = axes[0, 2]
    
    # Collect all test results chronologically
    all_tests = []
    for h in hypotheses:
        for test in h.get("tested_events", []):
            all_tests.append({
                "hypothesis_id": h["id"],
                "result": test["result"],
                "tested_at": test["tested_at"]
            })
    
    if len(all_tests) >= 3:
        # Sort by date
        all_tests.sort(key=lambda x: x["tested_at"])
        
        test_numbers = list(range(1, len(all_tests) + 1))
        results = [t["result"] for t in all_tests]
        
        # Plot individual results
        ax3.scatter(test_numbers, results, s=80, alpha=0.6, color='#3498db',
                   edgecolors='black', zorder=3)
        
        # Add trend line
        if len(results) >= 3:
            z = np.polyfit(test_numbers, results, 1)
            p = np.poly1d(z)
            ax3.plot(test_numbers, p(test_numbers), "r--", linewidth=2, 
                    alpha=0.8, label='Trend', zorder=2)
        
        # Add moving average
        if len(results) >= 5:
            window = 3
            moving_avg = np.convolve(results, np.ones(window)/window, mode='valid')
            ma_x = list(range(window, len(results) + 1))
            ax3.plot(ma_x, moving_avg, color='#2ecc71', linewidth=2,
                    label=f'{window}-test MA', zorder=2)
        
        ax3.set_xlabel("Test Number")
        ax3.set_ylabel("Result (1-5)")
        ax3.set_title("Test Result Trends Over Time")
        ax3.set_ylim(0.5, 5.5)
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Add mean line
        mean_result = np.mean(results)
        ax3.axhline(mean_result, color='gray', linestyle=':', linewidth=1.5,
                   label=f'Mean: {mean_result:.2f}', zorder=1)
    else:
        _plot_insufficient_data(
            ax3,
            "Test Result Trends Over Time",
            "Need 3+ test sessions for trend analysis"
        )
    
    # 4. Hypothesis lifecycle timeline
    ax4 = axes[1, 0]
    
    if hypotheses:
        # Sort by creation date
        sorted_hyps = sorted(hypotheses, key=lambda x: x["created_at"])
        
        for i, h in enumerate(sorted_hyps):
            created = datetime.fromisoformat(h["created_at"])
            
            # Determine end date
            if h.get("concluded_at"):
                ended = datetime.fromisoformat(h["concluded_at"])
            else:
                ended = datetime.now()
            
            # Color by status
            color = status_colors.get(h["status"], "#95a5a6")
            
            # Plot timeline bar
            ax4.barh(i, (ended - created).days, left=created.toordinal(),
                    height=0.8, color=color, alpha=0.7, edgecolor='black')
            
            # Add hypothesis ID label
            ax4.text(created.toordinal(), i, f" #{h['id']}", 
                    va='center', fontsize=9, fontweight='bold')
        
        ax4.set_yticks(range(len(sorted_hyps)))
        ax4.set_yticklabels([f"H{h['id']}" for h in sorted_hyps])
        ax4.set_xlabel("Date")
        ax4.set_title("Hypothesis Lifecycle Timeline")
        ax4.grid(True, alpha=0.3, axis='x')
        
        # Format x-axis as dates
        from matplotlib.dates import DateFormatter, DayLocator
        ax4.xaxis_date()
        ax4.xaxis.set_major_formatter(DateFormatter('%m/%d'))
    else:
        _plot_insufficient_data(
            ax4,
            "Hypothesis Lifecycle Timeline",
            "No hypotheses yet"
        )
    
    # 5. Average test results per hypothesis
    ax5 = axes[1, 1]
    
    hyp_averages = []
    hyp_labels = []
    
    for h in hypotheses:
        if h.get("tested_events"):
            avg = np.mean([t["result"] for t in h["tested_events"]])
            hyp_averages.append(avg)
            hyp_labels.append(f"#{h['id']}")
    
    if hyp_averages:
        colors_by_avg = ['#2ecc71' if avg >= 4 else '#f39c12' if avg >= 3 else '#e74c3c' 
                        for avg in hyp_averages]
        
        bars = ax5.barh(hyp_labels, hyp_averages, color=colors_by_avg, alpha=0.7,
                       edgecolor='black')
        
        ax5.set_xlabel("Average Test Result")
        ax5.set_ylabel("Hypothesis")
        ax5.set_title("Average Test Results per Hypothesis")
        ax5.set_xlim(0, 5)
        ax5.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, avg) in enumerate(zip(bars, hyp_averages)):
            ax5.text(avg + 0.1, i, f'{avg:.2f}', va='center', fontsize=9)
    else:
        _plot_insufficient_data(
            ax5,
            "Average Test Results per Hypothesis",
            "No test sessions recorded yet"
        )
    
    # 6. Testing activity over time
    ax6 = axes[1, 2]
    
    if all_tests:
        # Group tests by week
        test_dates = [datetime.fromisoformat(t["tested_at"]) for t in all_tests]
        
        if test_dates:
            # Create weekly bins
            min_date = min(test_dates)
            max_date = max(test_dates)
            
            # Calculate weeks
            weeks = [(d - min_date).days // 7 for d in test_dates]
            week_counts = Counter(weeks)
            
            week_labels = sorted(week_counts.keys())
            counts = [week_counts[w] for w in week_labels]
            
            ax6.bar(week_labels, counts, color='#3498db', alpha=0.7, edgecolor='black')
            ax6.set_xlabel("Week")
            ax6.set_ylabel("Number of Tests")
            ax6.set_title("Testing Activity Over Time")
            ax6.grid(True, alpha=0.3, axis='y')
            
            # Add trend line if enough data
            if len(week_labels) >= 3:
                z = np.polyfit(week_labels, counts, 1)
                p = np.poly1d(z)
                ax6.plot(week_labels, p(week_labels), "r--", linewidth=2, alpha=0.8)
    else:
        _plot_insufficient_data(
            ax6,
            "Testing Activity Over Time",
            "No test sessions recorded yet"
        )
    
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualization saved to {output_file}")
    plt.close()


def print_summary_statistics() -> None:
    """
    Print summary statistics about hypothesis testing.
    """
    data = load_hypotheses()
    hypotheses = data.get("hypotheses", [])
    
    if not hypotheses:
        print("\n📋 No hypotheses yet")
        print("   Create one with: make hypothesis-create")
        return
    
    total = len(hypotheses)
    active = len([h for h in hypotheses if h["status"] == "active"])
    confirmed = len([h for h in hypotheses if h["status"] == "confirmed"])
    partial = len([h for h in hypotheses if h["status"] == "partially_confirmed"])
    rejected = len([h for h in hypotheses if h["status"] == "rejected"])
    
    print("\n" + "="*70)
    print("HYPOTHESIS TESTING SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total hypotheses: {total}")
    print(f"  Active: {active}")
    print(f"  Confirmed: {confirmed}")
    print(f"  Partially confirmed: {partial}")
    print(f"  Rejected: {rejected}")
    
    # Success rate
    concluded = confirmed + partial + rejected
    if concluded > 0:
        success_rate = ((confirmed + partial) / concluded) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        print(f"   (Confirmed + Partially Confirmed) / Total Concluded")
    
    # Test sessions
    total_tests = sum(len(h.get("tested_events", [])) for h in hypotheses)
    if total_tests > 0:
        print(f"\n🔬 Test Sessions:")
        print(f"  Total: {total_tests}")
        print(f"  Average per hypothesis: {total_tests/total:.1f}")
        
        # Average test result
        all_results = []
        for h in hypotheses:
            for test in h.get("tested_events", []):
                all_results.append(test["result"])
        
        if all_results:
            avg_result = np.mean(all_results)
            print(f"  Average result: {avg_result:.2f}/5")
    
    # Areas
    areas = Counter(h.get("area", "Unknown") for h in hypotheses)
    if areas:
        print(f"\n🎯 Focus Areas:")
        for area, count in areas.most_common():
            print(f"  {area}: {count}")
    
    print()


def main():
    """Main entry point."""
    # Determine output file
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
    else:
        output_file = Path("coaching/hypotheses_analysis.png")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n📊 Analyzing hypothesis testing data...")
    
    # Print summary statistics
    print_summary_statistics()
    
    # Create visualization
    visualize_hypotheses(output_file)


if __name__ == "__main__":
    main()
