#!/usr/bin/env python3
"""
Mental Rehearsal Protocol Tool
===============================

Interactive tool for tracking pre-session mental rehearsal (visualization)
and post-session mental replay (corrections rehearsal).

Based on motor imagery research showing that mental practice enhances
skill acquisition and performance when combined with physical practice.

Usage:
    # Pre-session mental rehearsal
    python tools/mental_rehearsal.py pre <event_file>
    
    # Post-session mental replay
    python tools/mental_rehearsal.py post <event_file>
    
    # View rehearsal data
    python tools/mental_rehearsal.py view <event_file>

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
from pathlib import Path
from datetime import datetime

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from frontmatter_utils import (
    update_event_frontmatter,
    get_frontmatter_field,
    parse_event_file
)


def prompt_pre_session_rehearsal() -> dict:
    """
    Interactive prompts for pre-session mental rehearsal.
    
    Returns:
        Dictionary with pre-session rehearsal data
    """
    print("\n" + "="*70)
    print("PRE-SESSION MENTAL REHEARSAL")
    print("="*70)
    print("\nMental rehearsal (visualization) before a session helps activate")
    print("the neural pathways you'll use during actual practice.")
    print()
    
    # Duration
    print("How long did you spend on mental rehearsal? (minutes)")
    print("  Recommended: 3-5 minutes")
    while True:
        duration_str = input("Duration (minutes): ").strip()
        try:
            duration = int(duration_str)
            if duration > 0:
                break
            print("  ⚠️  Duration must be positive")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    # Focus area
    print("\nWhat did you focus on during visualization?")
    print("  Examples:")
    print("    - 'T1-T3 transitions and braking points'")
    print("    - 'Smooth throttle application in T6-T7'")
    print("    - 'Maintaining patience in traffic'")
    focus = input("Focus area: ").strip()
    
    # Specific corners
    print("\nWhich corners did you mentally rehearse? (comma-separated)")
    print("  Examples: 'T1, T3, T6' or 'all' or 'none'")
    corners_input = input("Corners: ").strip()
    
    if corners_input.lower() == "all":
        corners = "all"
    elif corners_input.lower() == "none":
        corners = []
    else:
        corners = [c.strip() for c in corners_input.split(",") if c.strip()]
    
    # Confidence rating
    print("\nHow confident do you feel going into this session?")
    print("  1 = Very uncertain, 5 = Very confident")
    while True:
        confidence_str = input("Confidence (1-5): ").strip()
        try:
            confidence = int(confidence_str)
            if 1 <= confidence <= 5:
                break
            print("  ⚠️  Please enter a number between 1 and 5")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    # Notes
    print("\nAny additional notes? (optional, press Enter to skip)")
    notes = input("Notes: ").strip()
    
    data = {
        "pre_session": True,
        "duration_minutes": duration,
        "focus": focus,
        "corners_rehearsed": corners,
        "confidence_rating": confidence,
        "timestamp": datetime.now().isoformat()
    }
    
    if notes:
        data["notes"] = notes
    
    print("\n✓ Pre-session rehearsal recorded")
    return data


def prompt_post_session_replay() -> dict:
    """
    Interactive prompts for post-session mental replay.
    
    Returns:
        Dictionary with post-session replay data
    """
    print("\n" + "="*70)
    print("POST-SESSION MENTAL REPLAY")
    print("="*70)
    print("\nMental replay after a session helps consolidate learning and")
    print("correct mistakes by rehearsing the proper technique mentally.")
    print()
    
    # Did they do replay?
    print("Did you perform mental replay after this session?")
    replay_input = input("Yes/No: ").strip().lower()
    
    if replay_input not in ["yes", "y"]:
        return {
            "post_session": False,
            "timestamp": datetime.now().isoformat()
        }
    
    # Duration
    print("\nHow long did you spend on mental replay? (minutes)")
    print("  Recommended: 2-5 minutes")
    while True:
        duration_str = input("Duration (minutes): ").strip()
        try:
            duration = int(duration_str)
            if duration > 0:
                break
            print("  ⚠️  Duration must be positive")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    # Corrections rehearsed
    print("\nWhat corrections did you mentally rehearse?")
    print("  Examples:")
    print("    - 'Earlier braking in T1, smoother turn-in'")
    print("    - 'Higher apex speed in T3 with better line'")
    print("    - 'More patient throttle application in T6'")
    corrections = input("Corrections: ").strip()
    
    # Specific corners
    print("\nWhich corners did you replay with corrections? (comma-separated)")
    print("  Examples: 'T1, T3' or 'all'")
    corners_input = input("Corners: ").strip()
    
    if corners_input.lower() == "all":
        corners = "all"
    else:
        corners = [c.strip() for c in corners_input.split(",") if c.strip()]
    
    # Clarity rating
    print("\nHow clear was your mental replay?")
    print("  1 = Vague/difficult, 5 = Very clear and vivid")
    while True:
        clarity_str = input("Clarity (1-5): ").strip()
        try:
            clarity = int(clarity_str)
            if 1 <= clarity <= 5:
                break
            print("  ⚠️  Please enter a number between 1 and 5")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    # Notes
    print("\nAny additional notes? (optional, press Enter to skip)")
    notes = input("Notes: ").strip()
    
    data = {
        "post_session": True,
        "duration_minutes": duration,
        "corrections_rehearsed": corrections,
        "corners_replayed": corners,
        "clarity_rating": clarity,
        "timestamp": datetime.now().isoformat()
    }
    
    if notes:
        data["notes"] = notes
    
    print("\n✓ Post-session replay recorded")
    return data


def add_pre_session_rehearsal(event_file: Path) -> None:
    """
    Add pre-session mental rehearsal data to event file.
    
    Args:
        event_file: Path to event markdown file
    """
    if not event_file.exists():
        print(f"❌ Error: File not found: {event_file}")
        sys.exit(1)
    
    # Check if pre-session data already exists
    existing = get_frontmatter_field(event_file, "mental_rehearsal.pre_session")
    if existing:
        print("⚠️  Warning: Pre-session rehearsal data already exists for this event")
        overwrite = input("Overwrite? (yes/no): ").strip().lower()
        if overwrite not in ["yes", "y"]:
            print("Cancelled.")
            return
    
    # Prompt for data
    data = prompt_pre_session_rehearsal()
    
    # Merge with any existing mental_rehearsal data to preserve post-session fields
    existing_mental_rehearsal = get_frontmatter_field(event_file, "mental_rehearsal") or {}
    merged_mental_rehearsal = {**existing_mental_rehearsal, **data}
    
    # Update frontmatter
    update_event_frontmatter(event_file, {
        "mental_rehearsal": merged_mental_rehearsal
    })
    
    print(f"\n✅ Mental rehearsal data added to {event_file.name}")


def add_post_session_replay(event_file: Path) -> None:
    """
    Add post-session mental replay data to event file.
    
    Args:
        event_file: Path to event markdown file
    """
    if not event_file.exists():
        print(f"❌ Error: File not found: {event_file}")
        sys.exit(1)
    
    # Check if post-session data already exists
    existing = get_frontmatter_field(event_file, "mental_rehearsal.post_session")
    if existing is not None:
        print("⚠️  Warning: Post-session replay data already exists for this event")
        overwrite = input("Overwrite? (yes/no): ").strip().lower()
        if overwrite not in ["yes", "y"]:
            print("Cancelled.")
            return
    
    # Get existing mental_rehearsal data
    existing_data = get_frontmatter_field(event_file, "mental_rehearsal", default={})
    
    # Prompt for data
    data = prompt_post_session_replay()
    
    # Merge with existing data
    merged_data = {**existing_data, **data}
    
    # Update frontmatter
    update_event_frontmatter(event_file, {
        "mental_rehearsal": merged_data
    })
    
    print(f"\n✅ Mental replay data added to {event_file.name}")


def view_rehearsal_data(event_file: Path) -> None:
    """
    Display mental rehearsal data from event file.
    
    Args:
        event_file: Path to event markdown file
    """
    if not event_file.exists():
        print(f"❌ Error: File not found: {event_file}")
        sys.exit(1)
    
    frontmatter, _ = parse_event_file(event_file)
    
    print("\n" + "="*70)
    print(f"MENTAL REHEARSAL DATA: {event_file.name}")
    print("="*70)
    
    rehearsal_data = frontmatter.get("mental_rehearsal")
    
    if not rehearsal_data:
        print("\n❌ No mental rehearsal data found for this event")
        return
    
    # Pre-session data
    if rehearsal_data.get("pre_session"):
        print("\n📋 PRE-SESSION REHEARSAL")
        print(f"  Duration: {rehearsal_data.get('duration_minutes', 'N/A')} minutes")
        print(f"  Focus: {rehearsal_data.get('focus', 'N/A')}")
        
        corners = rehearsal_data.get('corners_rehearsed', [])
        if corners == "all":
            print(f"  Corners: All")
        elif corners:
            print(f"  Corners: {', '.join(corners)}")
        else:
            print(f"  Corners: None specified")
        
        print(f"  Confidence: {rehearsal_data.get('confidence_rating', 'N/A')}/5")
        
        if "notes" in rehearsal_data:
            print(f"  Notes: {rehearsal_data['notes']}")
    
    # Post-session data
    if rehearsal_data.get("post_session") is True:
        print("\n📋 POST-SESSION REPLAY")
        print(f"  Duration: {rehearsal_data.get('duration_minutes', 'N/A')} minutes")
        print(f"  Corrections: {rehearsal_data.get('corrections_rehearsed', 'N/A')}")
        
        corners = rehearsal_data.get('corners_replayed', [])
        if corners == "all":
            print(f"  Corners: All")
        elif corners:
            print(f"  Corners: {', '.join(corners)}")
        else:
            print(f"  Corners: None specified")
        
        print(f"  Clarity: {rehearsal_data.get('clarity_rating', 'N/A')}/5")
        
        if "notes" in rehearsal_data:
            print(f"  Notes: {rehearsal_data['notes']}")
    elif rehearsal_data.get("post_session") is False:
        print("\n📋 POST-SESSION REPLAY")
        print("  No replay performed")
    
    print()


def print_usage():
    """Print usage information."""
    print("""
Mental Rehearsal Protocol Tool
===============================

Usage:
    python tools/mental_rehearsal.py pre <event_file>
        Record pre-session mental rehearsal (visualization)
    
    python tools/mental_rehearsal.py post <event_file>
        Record post-session mental replay (corrections)
    
    python tools/mental_rehearsal.py view <event_file>
        View mental rehearsal data for an event

Examples:
    # Before a practice session
    python tools/mental_rehearsal.py pre weeks/week02/events/01-2025-12-20-solo.md
    
    # After a practice session
    python tools/mental_rehearsal.py post weeks/week02/events/01-2025-12-20-solo.md
    
    # View data
    python tools/mental_rehearsal.py view weeks/week02/events/01-2025-12-20-solo.md

Makefile shortcuts:
    make rehearsal-pre EVENT=weeks/week02/events/01-2025-12-20-solo.md
    make rehearsal-post EVENT=weeks/week02/events/01-2025-12-20-solo.md
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    event_file = Path(sys.argv[2])
    
    if command == "pre":
        add_pre_session_rehearsal(event_file)
    elif command == "post":
        add_post_session_replay(event_file)
    elif command == "view":
        view_rehearsal_data(event_file)
    else:
        print(f"❌ Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
