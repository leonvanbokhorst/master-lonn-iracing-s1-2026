#!/usr/bin/env python3
"""
Spaced Repetition System Visualization
=======================================

Analyzes and visualizes SRS data, showing retention rates, review patterns,
and the effectiveness of spaced repetition for track knowledge consolidation.

Generates visualizations showing:
- Retention rate by track and category
- Review schedule calendar
- Easiness factor distribution
- Learning curve over time

Usage:
    python tools/visualize_srs.py [output_file]

Example:
    python tools/visualize_srs.py
    python tools/visualize_srs.py analysis/srs_analysis.png

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
from datetime import datetime, timedelta
from collections import Counter

# Knowledge cards database
CARDS_DB = Path("coaching/knowledge_cards.json")


def load_cards() -> dict:
    """
    Load knowledge cards from JSON database.
    
    Returns:
        Dictionary of cards data
    """
    if not CARDS_DB.exists():
        return {"cards": [], "next_id": 1}
    
    with open(CARDS_DB, 'r') as f:
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


def visualize_srs(output_file: Path) -> None:
    """
    Create comprehensive visualization of SRS data.
    
    Args:
        output_file: Path to save figure
    """
    data = load_cards()
    cards = data.get("cards", [])
    
    if not cards:
        print("\n📋 No knowledge cards to visualize yet")
        print("   Add one with: make srs-add")
        return
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (16, 10)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("Spaced Repetition System Analysis", fontsize=16, fontweight='bold')
    
    # 1. Retention rate by track
    ax1 = axes[0, 0]
    
    # Group by track
    tracks = {}
    for card in cards:
        if card["track"] not in tracks:
            tracks[card["track"]] = []
        tracks[card["track"]].append(card)
    
    if tracks:
        track_names = []
        retention_rates = []
        
        for track, track_cards in sorted(tracks.items()):
            reviewed = [c for c in track_cards if c["total_reviews"] > 0]
            if reviewed:
                total = sum(c["total_reviews"] for c in reviewed)
                correct = sum(c["correct_reviews"] for c in reviewed)
                retention = (correct / total) * 100 if total > 0 else 0
                
                track_names.append(track[:20])  # Truncate long names
                retention_rates.append(retention)
        
        if retention_rates:
            colors = ['#2ecc71' if r >= 80 else '#f39c12' if r >= 60 else '#e74c3c' 
                     for r in retention_rates]
            
            bars = ax1.barh(track_names, retention_rates, color=colors, alpha=0.7,
                           edgecolor='black')
            
            ax1.set_xlabel("Retention Rate (%)")
            ax1.set_ylabel("Track")
            ax1.set_title("Retention Rate by Track")
            ax1.set_xlim(0, 100)
            ax1.grid(True, alpha=0.3, axis='x')
            
            # Add value labels
            for i, (bar, rate) in enumerate(zip(bars, retention_rates)):
                ax1.text(rate + 2, i, f'{rate:.1f}%', va='center', fontsize=9)
            
            # Add target line
            ax1.axvline(80, color='green', linestyle='--', linewidth=1.5, 
                       alpha=0.5, label='Target: 80%')
            ax1.legend()
        else:
            _plot_insufficient_data(
                ax1,
                "Retention Rate by Track",
                "No reviewed cards yet"
            )
    else:
        _plot_insufficient_data(
            ax1,
            "Retention Rate by Track",
            "No cards yet"
        )
    
    # 2. Retention rate by category
    ax2 = axes[0, 1]
    
    categories = {}
    for card in cards:
        cat = card["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(card)
    
    if categories:
        cat_names = []
        cat_retention = []
        
        for cat, cat_cards in sorted(categories.items()):
            reviewed = [c for c in cat_cards if c["total_reviews"] > 0]
            if reviewed:
                total = sum(c["total_reviews"] for c in reviewed)
                correct = sum(c["correct_reviews"] for c in reviewed)
                retention = (correct / total) * 100 if total > 0 else 0
                
                cat_names.append(cat.replace('_', ' ').title())
                cat_retention.append(retention)
        
        if cat_retention:
            colors = ['#2ecc71' if r >= 80 else '#f39c12' if r >= 60 else '#e74c3c' 
                     for r in cat_retention]
            
            bars = ax2.bar(range(len(cat_names)), cat_retention, color=colors, 
                          alpha=0.7, edgecolor='black')
            
            ax2.set_xlabel("Category")
            ax2.set_ylabel("Retention Rate (%)")
            ax2.set_title("Retention Rate by Category")
            ax2.set_xticks(range(len(cat_names)))
            ax2.set_xticklabels(cat_names, rotation=45, ha='right')
            ax2.set_ylim(0, 100)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Add value labels
            for bar, rate in zip(bars, cat_retention):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                        f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
            
            # Add target line
            ax2.axhline(80, color='green', linestyle='--', linewidth=1.5, 
                       alpha=0.5, label='Target: 80%')
            ax2.legend()
        else:
            _plot_insufficient_data(
                ax2,
                "Retention Rate by Category",
                "No reviewed cards yet"
            )
    else:
        _plot_insufficient_data(
            ax2,
            "Retention Rate by Category",
            "No cards yet"
        )
    
    # 3. Review schedule (next 30 days)
    ax3 = axes[0, 2]
    
    if cards:
        now = datetime.now()
        future_date = now + timedelta(days=30)
        
        # Count reviews per day
        review_counts = {}
        for i in range(31):
            date = now + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            review_counts[date_str] = 0
        
        for card in cards:
            next_review = datetime.fromisoformat(card["next_review"])
            if now <= next_review <= future_date:
                date_str = next_review.strftime('%Y-%m-%d')
                if date_str in review_counts:
                    review_counts[date_str] += 1
        
        dates = list(review_counts.keys())
        counts = list(review_counts.values())
        
        # Plot as bar chart
        x = range(len(dates))
        colors = ['#e74c3c' if c > 10 else '#f39c12' if c > 5 else '#3498db' 
                 for c in counts]
        
        ax3.bar(x, counts, color=colors, alpha=0.7, edgecolor='black')
        ax3.set_xlabel("Date")
        ax3.set_ylabel("Cards Due")
        ax3.set_title("Review Schedule (Next 30 Days)")
        ax3.set_xticks([0, 7, 14, 21, 28])
        ax3.set_xticklabels([dates[i][-5:] for i in [0, 7, 14, 21, 28]], 
                           rotation=45, ha='right')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add today marker
        ax3.axvline(0, color='red', linestyle='--', linewidth=2, 
                   alpha=0.7, label='Today')
        ax3.legend()
    else:
        _plot_insufficient_data(
            ax3,
            "Review Schedule (Next 30 Days)",
            "No cards yet"
        )
    
    # 4. Easiness factor distribution
    ax4 = axes[1, 0]
    
    reviewed_cards = [c for c in cards if c["total_reviews"] > 0]
    
    if reviewed_cards:
        efs = [c["easiness_factor"] for c in reviewed_cards]
        
        ax4.hist(efs, bins=15, color='#3498db', alpha=0.7, edgecolor='black')
        ax4.set_xlabel("Easiness Factor")
        ax4.set_ylabel("Number of Cards")
        ax4.set_title("Easiness Factor Distribution")
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add mean line
        mean_ef = np.mean(efs)
        ax4.axvline(mean_ef, color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {mean_ef:.2f}')
        
        # Add reference lines
        ax4.axvline(2.5, color='green', linestyle=':', linewidth=1.5,
                   alpha=0.5, label='Default: 2.5')
        
        ax4.legend()
    else:
        _plot_insufficient_data(
            ax4,
            "Easiness Factor Distribution",
            "No reviewed cards yet"
        )
    
    # 5. Learning curve (cumulative cards over time)
    ax5 = axes[1, 1]
    
    if cards:
        # Sort by creation date
        sorted_cards = sorted(cards, key=lambda c: c["created_at"])
        
        dates = []
        cumulative = []
        
        for i, card in enumerate(sorted_cards, 1):
            created = datetime.fromisoformat(card["created_at"])
            dates.append(created)
            cumulative.append(i)
        
        ax5.plot(dates, cumulative, marker='o', linewidth=2, markersize=6,
                color='#2ecc71', alpha=0.8)
        ax5.fill_between(dates, cumulative, alpha=0.3, color='#2ecc71')
        
        ax5.set_xlabel("Date")
        ax5.set_ylabel("Total Cards")
        ax5.set_title("Learning Curve (Cumulative Cards)")
        ax5.grid(True, alpha=0.3)
        
        # Format x-axis
        from matplotlib.dates import DateFormatter
        ax5.xaxis.set_major_formatter(DateFormatter('%m/%d'))
        plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        _plot_insufficient_data(
            ax5,
            "Learning Curve (Cumulative Cards)",
            "No cards yet"
        )
    
    # 6. Review activity over time
    ax6 = axes[1, 2]
    
    if reviewed_cards:
        # Collect all review dates
        review_dates = []
        for card in reviewed_cards:
            if card.get("last_reviewed"):
                review_dates.append(datetime.fromisoformat(card["last_reviewed"]))
        
        if review_dates:
            # Group by date
            date_counts = Counter(d.strftime('%Y-%m-%d') for d in review_dates)
            
            sorted_dates = sorted(date_counts.keys())
            counts = [date_counts[d] for d in sorted_dates]
            
            dates_dt = [datetime.strptime(d, '%Y-%m-%d') for d in sorted_dates]
            
            ax6.bar(dates_dt, counts, color='#9b59b6', alpha=0.7, edgecolor='black')
            ax6.set_xlabel("Date")
            ax6.set_ylabel("Reviews Completed")
            ax6.set_title("Review Activity Over Time")
            ax6.grid(True, alpha=0.3, axis='y')
            
            # Format x-axis
            from matplotlib.dates import DateFormatter
            ax6.xaxis.set_major_formatter(DateFormatter('%m/%d'))
            plt.setp(ax6.xaxis.get_majorticklabels(), rotation=45, ha='right')
        else:
            _plot_insufficient_data(
                ax6,
                "Review Activity Over Time",
                "No review history yet"
            )
    else:
        _plot_insufficient_data(
            ax6,
            "Review Activity Over Time",
            "No reviewed cards yet"
        )
    
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualization saved to {output_file}")
    plt.close()


def print_summary_statistics() -> None:
    """
    Print summary statistics about the SRS.
    """
    data = load_cards()
    cards = data.get("cards", [])
    
    if not cards:
        print("\n📋 No knowledge cards yet")
        print("   Add one with: make srs-add")
        return
    
    print("\n" + "="*70)
    print("SPACED REPETITION SYSTEM STATISTICS")
    print("="*70)
    
    # Overall stats
    total_cards = len(cards)
    now = datetime.now()
    due_cards = sum(1 for c in cards if datetime.fromisoformat(c["next_review"]) <= now)
    reviewed_cards = [c for c in cards if c["total_reviews"] > 0]
    
    print(f"\n📊 Overall:")
    print(f"   Total Cards: {total_cards}")
    print(f"   Due for Review: {due_cards}")
    print(f"   Reviewed at least once: {len(reviewed_cards)}")
    
    # Performance
    if reviewed_cards:
        total_reviews = sum(c["total_reviews"] for c in reviewed_cards)
        correct_reviews = sum(c["correct_reviews"] for c in reviewed_cards)
        
        print(f"\n📈 Performance:")
        print(f"   Total Reviews: {total_reviews}")
        print(f"   Correct Reviews: {correct_reviews}")
        
        if total_reviews > 0:
            overall_retention = (correct_reviews / total_reviews) * 100
            print(f"   Overall Retention: {overall_retention:.1f}%")
        
        avg_ef = sum(c["easiness_factor"] for c in reviewed_cards) / len(reviewed_cards)
        print(f"   Average Easiness Factor: {avg_ef:.2f}")
    
    # By track
    tracks = {}
    for card in cards:
        if card["track"] not in tracks:
            tracks[card["track"]] = []
        tracks[card["track"]].append(card)
    
    print(f"\n🏁 By Track:")
    for track, track_cards in sorted(tracks.items()):
        due = sum(1 for c in track_cards if datetime.fromisoformat(c["next_review"]) <= now)
        print(f"   {track}: {len(track_cards)} cards ({due} due)")
    
    # By category
    categories = Counter(c["category"] for c in cards)
    
    print(f"\n📂 By Category:")
    for cat, count in categories.most_common():
        print(f"   {cat}: {count}")
    
    print()


def main():
    """Main entry point."""
    # Determine output file
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
    else:
        output_file = Path("coaching/srs_analysis.png")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n📊 Analyzing spaced repetition data...")
    
    # Print summary statistics
    print_summary_statistics()
    
    # Create visualization
    visualize_srs(output_file)


if __name__ == "__main__":
    main()
