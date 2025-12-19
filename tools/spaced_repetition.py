#!/usr/bin/env python3
"""
Spaced Repetition System for Track Knowledge
=============================================

Implements the SM-2 algorithm for optimal scheduling of track knowledge reviews.
Helps consolidate long-term memory of corners, braking points, racing lines, and
track-specific techniques.

Based on cognitive science research showing that spaced repetition is the most
effective method for long-term retention.

Usage:
    # Add a new knowledge card
    python tools/spaced_repetition.py add
    
    # Review due cards
    python tools/spaced_repetition.py review
    
    # List all cards
    python tools/spaced_repetition.py list [--track TRACK] [--due]
    
    # View card details
    python tools/spaced_repetition.py view <card_id>
    
    # Show statistics
    python tools/spaced_repetition.py stats

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Knowledge cards database
CARDS_DB = Path("coaching/knowledge_cards.json")


@dataclass
class KnowledgeCard:
    """Represents a single knowledge card with SM-2 scheduling data."""
    id: int
    track: str
    category: str  # corner, braking, racing_line, technique, racecraft
    question: str
    answer: str
    created_at: str
    
    # SM-2 algorithm fields
    easiness_factor: float = 2.5  # EF, starts at 2.5
    interval: int = 0  # Days until next review
    repetitions: int = 0  # Number of successful reviews
    next_review: str = ""  # ISO date of next review
    last_reviewed: Optional[str] = None
    
    # Statistics
    total_reviews: int = 0
    correct_reviews: int = 0


def load_cards() -> Dict:
    """
    Load knowledge cards from JSON database.
    
    Returns:
        Dictionary of cards data
    """
    if not CARDS_DB.exists():
        return {"cards": [], "next_id": 1}
    
    with open(CARDS_DB, 'r') as f:
        data = json.load(f)
        # Convert dict cards back to KnowledgeCard objects
        cards = []
        for card_dict in data.get("cards", []):
            cards.append(KnowledgeCard(**card_dict))
        data["cards"] = cards
        return data


def save_cards(data: Dict) -> None:
    """
    Save knowledge cards to JSON database.
    
    Args:
        data: Cards data dictionary
    """
    CARDS_DB.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert KnowledgeCard objects to dicts
    save_data = {
        "cards": [asdict(card) for card in data["cards"]],
        "next_id": data["next_id"]
    }
    
    with open(CARDS_DB, 'w') as f:
        json.dump(save_data, f, indent=2)


def calculate_next_review(quality: int, card: KnowledgeCard) -> KnowledgeCard:
    """
    Calculate next review date using SM-2 algorithm.
    
    Args:
        quality: Quality of recall (0-5)
                 0-2: Incorrect, reset
                 3: Correct with difficulty
                 4: Correct after hesitation
                 5: Perfect recall
        card: Knowledge card to update
    
    Returns:
        Updated knowledge card
    """
    # Update easiness factor
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    ef = card.easiness_factor
    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    # EF must be at least 1.3
    if ef < 1.3:
        ef = 1.3
    
    card.easiness_factor = ef
    
    # Calculate interval
    if quality < 3:
        # Incorrect recall - reset
        card.repetitions = 0
        card.interval = 0
        interval_days = 0
    else:
        # Correct recall
        card.repetitions += 1
        
        if card.repetitions == 1:
            interval_days = 1
        elif card.repetitions == 2:
            interval_days = 6
        else:
            interval_days = round(card.interval * ef)
        
        card.interval = interval_days
        card.correct_reviews += 1
    
    # Set next review date
    next_date = datetime.now() + timedelta(days=interval_days)
    card.next_review = next_date.isoformat()
    card.last_reviewed = datetime.now().isoformat()
    card.total_reviews += 1
    
    return card


def add_card() -> None:
    """
    Interactive prompts to add a new knowledge card.
    """
    print("\n" + "="*70)
    print("ADD NEW KNOWLEDGE CARD")
    print("="*70)
    print("\nSpaced repetition helps consolidate track knowledge into long-term memory.")
    print("Create cards for corners, braking points, racing lines, and techniques.")
    print()
    
    # Track
    print("Which track is this knowledge for?")
    print("  Examples: 'Summit Point Jefferson Circuit', 'Watkins Glen'")
    track = input("Track: ").strip()
    
    if not track:
        print("❌ Track cannot be empty")
        return
    
    # Category
    print("\nWhat category does this knowledge belong to?")
    print("  1 = Corner technique")
    print("  2 = Braking point")
    print("  3 = Racing line")
    print("  4 = General technique")
    print("  5 = Racecraft/strategy")
    
    while True:
        cat_str = input("Category (1-5): ").strip()
        try:
            cat_num = int(cat_str)
            if 1 <= cat_num <= 5:
                break
            print("  ⚠️  Please enter a number between 1 and 5")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    category_map = {
        1: "corner",
        2: "braking",
        3: "racing_line",
        4: "technique",
        5: "racecraft"
    }
    category = category_map[cat_num]
    
    # Question (front of card)
    print("\nQuestion (what you're trying to remember):")
    print("  Examples:")
    print("    - 'What is the optimal braking point for T1?'")
    print("    - 'What line maximizes exit speed in T3?'")
    print("    - 'How should I approach T6-T7 complex?'")
    question = input("Question: ").strip()
    
    if not question:
        print("❌ Question cannot be empty")
        return
    
    # Answer (back of card)
    print("\nAnswer (the knowledge you want to remember):")
    print("  Be specific and detailed. Include landmarks, techniques, etc.")
    answer = input("Answer: ").strip()
    
    if not answer:
        print("❌ Answer cannot be empty")
        return
    
    # Create card
    db = load_cards()
    card_id = db["next_id"]
    
    # New cards are due immediately for first review
    card = KnowledgeCard(
        id=card_id,
        track=track,
        category=category,
        question=question,
        answer=answer,
        created_at=datetime.now().isoformat(),
        next_review=datetime.now().isoformat()
    )
    
    db["cards"].append(card)
    db["next_id"] += 1
    
    save_cards(db)
    
    print(f"\n✅ Knowledge card #{card_id} created")
    print(f"   Track: {track}")
    print(f"   Category: {category}")
    print(f"\n💡 Review it now with: make srs-review")


def review_cards() -> None:
    """
    Interactive review session for due cards.
    """
    db = load_cards()
    
    # Find due cards
    now = datetime.now()
    due_cards = [
        card for card in db["cards"]
        if datetime.fromisoformat(card.next_review) <= now
    ]
    
    if not due_cards:
        print("\n✅ No cards due for review!")
        print("   Next review: ", end="")
        
        if db["cards"]:
            next_card = min(db["cards"], key=lambda c: c.next_review)
            next_date = datetime.fromisoformat(next_card.next_review)
            days_until = (next_date - now).days
            
            if days_until == 0:
                print("later today")
            elif days_until == 1:
                print("tomorrow")
            else:
                print(f"in {days_until} days ({next_date.strftime('%Y-%m-%d')})")
        else:
            print("no cards yet")
        
        print("\n💡 Add more cards with: make srs-add")
        return
    
    print("\n" + "="*70)
    print(f"REVIEW SESSION - {len(due_cards)} card(s) due")
    print("="*70)
    print("\nRate your recall quality:")
    print("  0 = Complete blackout, no recall")
    print("  1 = Incorrect, but familiar")
    print("  2 = Incorrect, but close")
    print("  3 = Correct with difficulty")
    print("  4 = Correct after hesitation")
    print("  5 = Perfect recall")
    print()
    
    reviewed = 0
    
    for i, card in enumerate(due_cards, 1):
        print(f"\n{'='*70}")
        print(f"Card {i}/{len(due_cards)}")
        print(f"{'='*70}")
        print(f"\n📍 Track: {card.track}")
        print(f"📂 Category: {card.category}")
        print(f"\n❓ {card.question}")
        print()
        
        input("Press Enter to reveal answer...")
        
        print(f"\n✅ {card.answer}")
        print()
        
        # Get quality rating
        while True:
            quality_str = input("Quality (0-5): ").strip()
            try:
                quality = int(quality_str)
                if 0 <= quality <= 5:
                    break
                print("  ⚠️  Please enter a number between 0 and 5")
            except ValueError:
                print("  ⚠️  Please enter a number")
        
        # Update card using SM-2
        updated_card = calculate_next_review(quality, card)
        
        # Update in database
        for j, db_card in enumerate(db["cards"]):
            if db_card.id == card.id:
                db["cards"][j] = updated_card
                break
        
        # Show feedback
        if quality < 3:
            print(f"  📅 You'll see this card again today")
        else:
            next_date = datetime.fromisoformat(updated_card.next_review)
            days = updated_card.interval
            if days == 1:
                print(f"  📅 Next review: tomorrow")
            else:
                print(f"  📅 Next review: in {days} days ({next_date.strftime('%Y-%m-%d')})")
        
        reviewed += 1
    
    # Save all updates
    save_cards(db)
    
    print(f"\n{'='*70}")
    print(f"✅ Review session complete! Reviewed {reviewed} card(s)")
    print(f"{'='*70}")


def list_cards(track_filter: Optional[str] = None, due_only: bool = False) -> None:
    """
    List all knowledge cards, optionally filtered.
    
    Args:
        track_filter: Optional track name to filter by
        due_only: If True, only show cards due for review
    """
    db = load_cards()
    cards = db["cards"]
    
    if track_filter:
        cards = [c for c in cards if track_filter.lower() in c.track.lower()]
    
    if due_only:
        now = datetime.now()
        cards = [c for c in cards if datetime.fromisoformat(c.next_review) <= now]
    
    if not cards:
        if track_filter:
            print(f"\n📋 No cards for track: {track_filter}")
        elif due_only:
            print("\n📋 No cards due for review")
        else:
            print("\n📋 No cards yet. Add one with: make srs-add")
        return
    
    print("\n" + "="*70)
    print("KNOWLEDGE CARDS")
    print("="*70)
    
    # Group by track
    tracks = {}
    for card in cards:
        if card.track not in tracks:
            tracks[card.track] = []
        tracks[card.track].append(card)
    
    now = datetime.now()
    
    for track, track_cards in sorted(tracks.items()):
        due_count = sum(1 for c in track_cards 
                       if datetime.fromisoformat(c.next_review) <= now)
        
        print(f"\n🏁 {track} ({len(track_cards)} cards, {due_count} due)")
        
        for card in sorted(track_cards, key=lambda c: c.id):
            next_date = datetime.fromisoformat(card.next_review)
            is_due = next_date <= now
            
            status = "🔴 DUE" if is_due else f"📅 {next_date.strftime('%Y-%m-%d')}"
            
            # Calculate retention rate
            if card.total_reviews > 0:
                retention = (card.correct_reviews / card.total_reviews) * 100
                retention_str = f"{retention:.0f}%"
            else:
                retention_str = "New"
            
            print(f"  #{card.id}: {card.question[:60]}...")
            print(f"       {status} | {card.category} | Retention: {retention_str} | Reviews: {card.total_reviews}")
    
    print()


def view_card(card_id: int) -> None:
    """
    View detailed information about a knowledge card.
    
    Args:
        card_id: ID of the card
    """
    db = load_cards()
    card = None
    
    for c in db["cards"]:
        if c.id == card_id:
            card = c
            break
    
    if not card:
        print(f"❌ Error: Card #{card_id} not found")
        sys.exit(1)
    
    print("\n" + "="*70)
    print(f"KNOWLEDGE CARD #{card.id}")
    print("="*70)
    
    print(f"\n🏁 Track: {card.track}")
    print(f"📂 Category: {card.category}")
    print(f"📅 Created: {card.created_at[:10]}")
    
    print(f"\n❓ Question:")
    print(f"   {card.question}")
    
    print(f"\n✅ Answer:")
    print(f"   {card.answer}")
    
    print(f"\n📊 SM-2 Statistics:")
    print(f"   Easiness Factor: {card.easiness_factor:.2f}")
    print(f"   Interval: {card.interval} days")
    print(f"   Repetitions: {card.repetitions}")
    
    now = datetime.now()
    next_date = datetime.fromisoformat(card.next_review)
    is_due = next_date <= now
    
    if is_due:
        print(f"   Next Review: 🔴 DUE NOW")
    else:
        days_until = (next_date - now).days
        print(f"   Next Review: {next_date.strftime('%Y-%m-%d')} (in {days_until} days)")
    
    if card.last_reviewed:
        print(f"   Last Reviewed: {card.last_reviewed[:10]}")
    
    print(f"\n📈 Performance:")
    print(f"   Total Reviews: {card.total_reviews}")
    print(f"   Correct Reviews: {card.correct_reviews}")
    
    if card.total_reviews > 0:
        retention = (card.correct_reviews / card.total_reviews) * 100
        print(f"   Retention Rate: {retention:.1f}%")
    
    print()


def show_statistics() -> None:
    """
    Show overall statistics about the spaced repetition system.
    """
    db = load_cards()
    cards = db["cards"]
    
    if not cards:
        print("\n📋 No cards yet. Add one with: make srs-add")
        return
    
    print("\n" + "="*70)
    print("SPACED REPETITION STATISTICS")
    print("="*70)
    
    # Overall stats
    total_cards = len(cards)
    now = datetime.now()
    due_cards = sum(1 for c in cards if datetime.fromisoformat(c.next_review) <= now)
    
    print(f"\n📊 Overall:")
    print(f"   Total Cards: {total_cards}")
    print(f"   Due for Review: {due_cards}")
    print(f"   Up to Date: {total_cards - due_cards}")
    
    # By track
    tracks = {}
    for card in cards:
        if card.track not in tracks:
            tracks[card.track] = []
        tracks[card.track].append(card)
    
    print(f"\n🏁 By Track:")
    for track, track_cards in sorted(tracks.items()):
        due = sum(1 for c in track_cards if datetime.fromisoformat(c.next_review) <= now)
        print(f"   {track}: {len(track_cards)} cards ({due} due)")
    
    # By category
    from collections import Counter
    categories = Counter(c.category for c in cards)
    
    print(f"\n📂 By Category:")
    for cat, count in categories.most_common():
        print(f"   {cat}: {count}")
    
    # Performance stats
    reviewed_cards = [c for c in cards if c.total_reviews > 0]
    
    if reviewed_cards:
        total_reviews = sum(c.total_reviews for c in reviewed_cards)
        correct_reviews = sum(c.correct_reviews for c in reviewed_cards)
        
        print(f"\n📈 Performance:")
        print(f"   Total Reviews: {total_reviews}")
        print(f"   Correct Reviews: {correct_reviews}")
        
        if total_reviews > 0:
            overall_retention = (correct_reviews / total_reviews) * 100
            print(f"   Overall Retention: {overall_retention:.1f}%")
        
        avg_ef = sum(c.easiness_factor for c in reviewed_cards) / len(reviewed_cards)
        print(f"   Average Easiness Factor: {avg_ef:.2f}")
    
    # Upcoming reviews
    future_cards = [c for c in cards if datetime.fromisoformat(c.next_review) > now]
    if future_cards:
        next_card = min(future_cards, key=lambda c: c.next_review)
        next_date = datetime.fromisoformat(next_card.next_review)
        days_until = (next_date - now).days
        
        print(f"\n📅 Next Review:")
        if days_until == 0:
            print(f"   Later today")
        elif days_until == 1:
            print(f"   Tomorrow")
        else:
            print(f"   In {days_until} days ({next_date.strftime('%Y-%m-%d')})")
    
    print()


def print_usage():
    """Print usage information."""
    print("""
Spaced Repetition System for Track Knowledge
=============================================

Usage:
    python tools/spaced_repetition.py add
        Add a new knowledge card
    
    python tools/spaced_repetition.py review
        Review due cards
    
    python tools/spaced_repetition.py list [--track TRACK] [--due]
        List all cards (optionally filtered)
    
    python tools/spaced_repetition.py view <card_id>
        View card details
    
    python tools/spaced_repetition.py stats
        Show statistics

Examples:
    # Add a new card
    python tools/spaced_repetition.py add
    
    # Review due cards
    python tools/spaced_repetition.py review
    
    # List all cards
    python tools/spaced_repetition.py list
    
    # List cards for specific track
    python tools/spaced_repetition.py list --track "Summit Point"
    
    # List only due cards
    python tools/spaced_repetition.py list --due
    
    # View card #1
    python tools/spaced_repetition.py view 1
    
    # Show statistics
    python tools/spaced_repetition.py stats

Makefile shortcuts:
    make srs-add
    make srs-review
    make srs-list
    make srs-stats
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "add":
        add_card()
    
    elif command == "review":
        review_cards()
    
    elif command == "list":
        track_filter = None
        due_only = False
        
        if "--track" in sys.argv:
            track_idx = sys.argv.index("--track")
            if track_idx + 1 < len(sys.argv):
                track_filter = sys.argv[track_idx + 1]
        
        if "--due" in sys.argv:
            due_only = True
        
        list_cards(track_filter, due_only)
    
    elif command == "view":
        if len(sys.argv) < 3:
            print("❌ Usage: python tools/spaced_repetition.py view <card_id>")
            sys.exit(1)
        
        try:
            card_id = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Card ID must be a number")
            sys.exit(1)
        
        view_card(card_id)
    
    elif command == "stats":
        show_statistics()
    
    else:
        print(f"❌ Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
