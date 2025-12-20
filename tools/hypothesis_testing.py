#!/usr/bin/env python3
"""
Hypothesis Testing Framework
=============================

Interactive tool for managing the hypothesis-driven learning cycle:
formulate → test → analyze → conclude.

Based on the scientific method applied to skill acquisition, enabling
systematic experimentation and evidence-based improvement.

Usage:
    # Create a new hypothesis
    python tools/hypothesis_testing.py create
    
    # Link hypothesis to an event (testing phase)
    python tools/hypothesis_testing.py test <hypothesis_id> <event_file>
    
    # Conclude a hypothesis after testing
    python tools/hypothesis_testing.py conclude <hypothesis_id>
    
    # List all hypotheses
    python tools/hypothesis_testing.py list [--status STATUS]
    
    # View hypothesis details
    python tools/hypothesis_testing.py view <hypothesis_id>

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from frontmatter_utils import (
    update_event_frontmatter,
    get_frontmatter_field,
    parse_event_file
)

# Hypothesis database file
HYPOTHESIS_DB = Path("coaching/hypotheses.json")


def load_hypotheses() -> Dict:
    """
    Load hypotheses from JSON database.
    
    Returns:
        Dictionary of hypotheses
    """
    if not HYPOTHESIS_DB.exists():
        return {"hypotheses": [], "next_id": 1}
    
    with open(HYPOTHESIS_DB, 'r') as f:
        return json.load(f)


def save_hypotheses(data: Dict) -> None:
    """
    Save hypotheses to JSON database.
    
    Args:
        data: Hypotheses data dictionary
    """
    HYPOTHESIS_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(HYPOTHESIS_DB, 'w') as f:
        json.dump(data, f, indent=2)


def create_hypothesis() -> None:
    """
    Interactive prompts to create a new hypothesis.
    """
    print("\n" + "="*70)
    print("CREATE NEW HYPOTHESIS")
    print("="*70)
    print("\nThe hypothesis-driven learning cycle:")
    print("  1. Formulate: State a testable hypothesis")
    print("  2. Test: Apply it in practice sessions")
    print("  3. Analyze: Review the results")
    print("  4. Conclude: Accept, reject, or refine")
    print()
    
    # Hypothesis statement
    print("State your hypothesis (be specific and testable):")
    print("  Examples:")
    print("    - 'Braking 10m earlier in T1 will improve exit speed'")
    print("    - 'Higher apex speed in T3 requires earlier throttle application'")
    print("    - 'Maintaining patience in traffic reduces incidents by 50%'")
    hypothesis = input("Hypothesis: ").strip()
    
    if not hypothesis:
        print("❌ Hypothesis cannot be empty")
        return
    
    # Area of focus
    print("\nWhat area does this hypothesis focus on?")
    print("  Examples: 'braking', 'throttle control', 'racecraft', 'consistency'")
    area = input("Focus area: ").strip()
    
    # Specific corners or sections
    print("\nWhich corners/sections will you test this on? (comma-separated)")
    print("  Examples: 'T1, T2' or 'all' or 'T6-T7 complex'")
    corners_input = input("Corners: ").strip()
    
    if corners_input.lower() == "all":
        corners = "all"
    else:
        corners = [c.strip() for c in corners_input.split(",") if c.strip()]
    
    # Success criteria
    print("\nWhat would constitute success? (measurable criteria)")
    print("  Examples:")
    print("    - 'Lap time improvement of 0.2s'")
    print("    - 'Exit speed increase of 3 mph'")
    print("    - 'Zero incidents over 3 races'")
    success_criteria = input("Success criteria: ").strip()
    
    # Planned test duration
    print("\nHow many sessions will you test this hypothesis?")
    print("  Recommended: 3-5 sessions for reliable data")
    while True:
        sessions_str = input("Number of sessions: ").strip()
        try:
            planned_sessions = int(sessions_str)
            if planned_sessions > 0:
                break
            print("  ⚠️  Must be positive")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    # Notes
    print("\nAny additional notes? (optional, press Enter to skip)")
    notes = input("Notes: ").strip()
    
    # Create hypothesis record
    db = load_hypotheses()
    hypothesis_id = db["next_id"]
    
    hypothesis_record = {
        "id": hypothesis_id,
        "hypothesis": hypothesis,
        "area": area,
        "corners": corners,
        "success_criteria": success_criteria,
        "planned_sessions": planned_sessions,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "tested_events": [],
        "conclusion": None,
        "concluded_at": None
    }
    
    if notes:
        hypothesis_record["notes"] = notes
    
    db["hypotheses"].append(hypothesis_record)
    db["next_id"] += 1
    
    save_hypotheses(db)
    
    print(f"\n✅ Hypothesis #{hypothesis_id} created")
    print(f"\nNext steps:")
    print(f"  1. Test it in practice: make hypothesis-test ID={hypothesis_id} EVENT=...")
    print(f"  2. After {planned_sessions} sessions, conclude: make hypothesis-conclude ID={hypothesis_id}")


def link_hypothesis_to_event(hypothesis_id: int, event_file: Path) -> None:
    """
    Link a hypothesis to an event (testing phase).
    
    Args:
        hypothesis_id: ID of the hypothesis
        event_file: Path to event markdown file
    """
    if not event_file.exists():
        print(f"❌ Error: File not found: {event_file}")
        sys.exit(1)
    
    # Load hypotheses
    db = load_hypotheses()
    hypothesis = None
    for h in db["hypotheses"]:
        if h["id"] == hypothesis_id:
            hypothesis = h
            break
    
    if not hypothesis:
        print(f"❌ Error: Hypothesis #{hypothesis_id} not found")
        sys.exit(1)
    
    if hypothesis["status"] != "active":
        print(f"⚠️  Warning: Hypothesis #{hypothesis_id} is {hypothesis['status']}")
        proceed = input("Link anyway? (yes/no): ").strip().lower()
        if proceed not in ["yes", "y"]:
            print("Cancelled.")
            return
    
    print(f"\n📋 Linking hypothesis #{hypothesis_id} to event...")
    print(f"Hypothesis: {hypothesis['hypothesis']}")
    print()
    
    # Prompt for test results
    print("How did the test go?")
    print("  1 = Failed completely")
    print("  2 = Mostly failed")
    print("  3 = Mixed results")
    print("  4 = Mostly successful")
    print("  5 = Completely successful")
    
    while True:
        result_str = input("Result (1-5): ").strip()
        try:
            result = int(result_str)
            if 1 <= result <= 5:
                break
            print("  ⚠️  Please enter a number between 1 and 5")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    # Observations
    print("\nWhat did you observe during this test?")
    observations = input("Observations: ").strip()
    
    # Update event frontmatter
    event_name = event_file.stem
    test_record = {
        "hypothesis_id": hypothesis_id,
        "hypothesis": hypothesis["hypothesis"],
        "result": result,
        "observations": observations,
        "tested_at": datetime.now().isoformat()
    }
    
    update_event_frontmatter(event_file, {
        "hypothesis_test": test_record
    })
    
    # Update hypothesis database
    hypothesis["tested_events"].append({
        "event": event_name,
        "result": result,
        "observations": observations,
        "tested_at": test_record["tested_at"]
    })
    
    save_hypotheses(db)
    
    print(f"\n✅ Hypothesis test recorded")
    print(f"   Event: {event_name}")
    print(f"   Result: {result}/5")
    
    # Check if enough sessions completed
    sessions_completed = len(hypothesis["tested_events"])
    planned = hypothesis["planned_sessions"]
    
    if sessions_completed >= planned:
        print(f"\n🎯 You've completed {sessions_completed}/{planned} planned sessions!")
        print(f"   Ready to conclude: make hypothesis-conclude ID={hypothesis_id}")


def conclude_hypothesis(hypothesis_id: int) -> None:
    """
    Conclude a hypothesis after testing.
    
    Args:
        hypothesis_id: ID of the hypothesis
    """
    db = load_hypotheses()
    hypothesis = None
    hyp_index = None
    
    for i, h in enumerate(db["hypotheses"]):
        if h["id"] == hypothesis_id:
            hypothesis = h
            hyp_index = i
            break
    
    if not hypothesis:
        print(f"❌ Error: Hypothesis #{hypothesis_id} not found")
        sys.exit(1)
    
    if hypothesis["status"] != "active":
        print(f"⚠️  Warning: Hypothesis #{hypothesis_id} is already {hypothesis['status']}")
        proceed = input("Conclude anyway? (yes/no): ").strip().lower()
        if proceed not in ["yes", "y"]:
            print("Cancelled.")
            return
    
    print("\n" + "="*70)
    print(f"CONCLUDE HYPOTHESIS #{hypothesis_id}")
    print("="*70)
    print(f"\nHypothesis: {hypothesis['hypothesis']}")
    print(f"Area: {hypothesis['area']}")
    print(f"Success criteria: {hypothesis['success_criteria']}")
    print(f"\nSessions completed: {len(hypothesis['tested_events'])}/{hypothesis['planned_sessions']}")
    
    if hypothesis["tested_events"]:
        print("\nTest results:")
        total_score = 0
        for test in hypothesis["tested_events"]:
            print(f"  - {test['event']}: {test['result']}/5")
            total_score += test["result"]
        
        avg_score = total_score / len(hypothesis["tested_events"])
        print(f"\nAverage result: {avg_score:.2f}/5")
    else:
        print("\n⚠️  No test sessions recorded yet")
    
    print("\n" + "-"*70)
    print("\nBased on your testing, what is your conclusion?")
    print("  1 = Rejected (hypothesis was incorrect)")
    print("  2 = Partially confirmed (needs refinement)")
    print("  3 = Confirmed (hypothesis was correct)")
    
    while True:
        conclusion_str = input("Conclusion (1-3): ").strip()
        try:
            conclusion_code = int(conclusion_str)
            if 1 <= conclusion_code <= 3:
                break
            print("  ⚠️  Please enter 1, 2, or 3")
        except ValueError:
            print("  ⚠️  Please enter a number")
    
    conclusion_map = {
        1: "rejected",
        2: "partially_confirmed",
        3: "confirmed"
    }
    
    conclusion_status = conclusion_map[conclusion_code]
    
    # Summary of findings
    print("\nSummarize your findings:")
    findings = input("Findings: ").strip()
    
    # Next steps
    print("\nWhat are the next steps based on this conclusion?")
    print("  Examples:")
    print("    - 'Continue using this technique'")
    print("    - 'Refine: brake 5m earlier instead of 10m'")
    print("    - 'Abandon this approach, try different line'")
    next_steps = input("Next steps: ").strip()
    
    # Update hypothesis
    hypothesis["status"] = conclusion_status
    hypothesis["conclusion"] = {
        "findings": findings,
        "next_steps": next_steps,
        "concluded_at": datetime.now().isoformat()
    }
    hypothesis["concluded_at"] = datetime.now().isoformat()
    
    db["hypotheses"][hyp_index] = hypothesis
    save_hypotheses(db)
    
    print(f"\n✅ Hypothesis #{hypothesis_id} concluded as: {conclusion_status}")
    print(f"\nNext steps: {next_steps}")


def list_hypotheses(status_filter: Optional[str] = None) -> None:
    """
    List all hypotheses, optionally filtered by status.
    
    Args:
        status_filter: Optional status to filter by
    """
    db = load_hypotheses()
    hypotheses = db["hypotheses"]
    
    if status_filter:
        hypotheses = [h for h in hypotheses if h["status"] == status_filter]
    
    if not hypotheses:
        if status_filter:
            print(f"\n📋 No hypotheses with status: {status_filter}")
        else:
            print("\n📋 No hypotheses yet. Create one with: make hypothesis-create")
        return
    
    print("\n" + "="*70)
    print("HYPOTHESES")
    print("="*70)
    
    # Group by status
    active = [h for h in hypotheses if h["status"] == "active"]
    confirmed = [h for h in hypotheses if h["status"] == "confirmed"]
    partially = [h for h in hypotheses if h["status"] == "partially_confirmed"]
    rejected = [h for h in hypotheses if h["status"] == "rejected"]
    
    if active:
        print(f"\n🔬 ACTIVE ({len(active)})")
        for h in active:
            sessions = f"{len(h['tested_events'])}/{h['planned_sessions']}"
            print(f"  #{h['id']}: {h['hypothesis']}")
            print(f"       Sessions: {sessions} | Area: {h['area']}")
    
    if confirmed:
        print(f"\n✅ CONFIRMED ({len(confirmed)})")
        for h in confirmed:
            print(f"  #{h['id']}: {h['hypothesis']}")
            if h.get("conclusion"):
                print(f"       Next steps: {h['conclusion']['next_steps']}")
    
    if partially:
        print(f"\n⚠️  PARTIALLY CONFIRMED ({len(partially)})")
        for h in partially:
            print(f"  #{h['id']}: {h['hypothesis']}")
            if h.get("conclusion"):
                print(f"       Next steps: {h['conclusion']['next_steps']}")
    
    if rejected:
        print(f"\n❌ REJECTED ({len(rejected)})")
        for h in rejected:
            print(f"  #{h['id']}: {h['hypothesis']}")
            if h.get("conclusion"):
                print(f"       Findings: {h['conclusion']['findings']}")
    
    print()


def view_hypothesis(hypothesis_id: int) -> None:
    """
    View detailed information about a hypothesis.
    
    Args:
        hypothesis_id: ID of the hypothesis
    """
    db = load_hypotheses()
    hypothesis = None
    
    for h in db["hypotheses"]:
        if h["id"] == hypothesis_id:
            hypothesis = h
            break
    
    if not hypothesis:
        print(f"❌ Error: Hypothesis #{hypothesis_id} not found")
        sys.exit(1)
    
    print("\n" + "="*70)
    print(f"HYPOTHESIS #{hypothesis['id']}")
    print("="*70)
    
    print(f"\n📋 Statement: {hypothesis['hypothesis']}")
    print(f"🎯 Area: {hypothesis['area']}")
    
    corners = hypothesis['corners']
    if corners == "all":
        print(f"🏁 Corners: All")
    elif corners:
        print(f"🏁 Corners: {', '.join(corners)}")
    
    print(f"✅ Success criteria: {hypothesis['success_criteria']}")
    print(f"📊 Status: {hypothesis['status'].replace('_', ' ').title()}")
    print(f"📅 Created: {hypothesis['created_at'][:10]}")
    
    if hypothesis.get("notes"):
        print(f"📝 Notes: {hypothesis['notes']}")
    
    # Test sessions
    print(f"\n🔬 TEST SESSIONS ({len(hypothesis['tested_events'])}/{hypothesis['planned_sessions']})")
    
    if hypothesis["tested_events"]:
        total_score = 0
        for test in hypothesis["tested_events"]:
            print(f"\n  Event: {test['event']}")
            print(f"  Result: {test['result']}/5")
            print(f"  Observations: {test['observations']}")
            print(f"  Tested: {test['tested_at'][:10]}")
            total_score += test["result"]
        
        avg_score = total_score / len(hypothesis["tested_events"])
        print(f"\n  Average result: {avg_score:.2f}/5")
    else:
        print("  No test sessions yet")
    
    # Conclusion
    if hypothesis.get("conclusion"):
        print(f"\n📝 CONCLUSION")
        print(f"  Findings: {hypothesis['conclusion']['findings']}")
        print(f"  Next steps: {hypothesis['conclusion']['next_steps']}")
        print(f"  Concluded: {hypothesis['concluded_at'][:10]}")
    
    print()


def print_usage():
    """Print usage information."""
    print("""
Hypothesis Testing Framework
=============================

Usage:
    python tools/hypothesis_testing.py create
        Create a new hypothesis
    
    python tools/hypothesis_testing.py test <id> <event_file>
        Link hypothesis to an event (testing phase)
    
    python tools/hypothesis_testing.py conclude <id>
        Conclude a hypothesis after testing
    
    python tools/hypothesis_testing.py list [--status STATUS]
        List all hypotheses (optionally filtered)
    
    python tools/hypothesis_testing.py view <id>
        View hypothesis details

Examples:
    # Create hypothesis
    python tools/hypothesis_testing.py create
    
    # Test hypothesis #1 in an event
    python tools/hypothesis_testing.py test 1 weeks/week02/events/01-2025-12-20-solo.md
    
    # Conclude hypothesis #1
    python tools/hypothesis_testing.py conclude 1
    
    # List active hypotheses
    python tools/hypothesis_testing.py list --status active
    
    # View hypothesis #1
    python tools/hypothesis_testing.py view 1

Makefile shortcuts:
    make hypothesis-create
    make hypothesis-test ID=1 EVENT=weeks/week02/events/01-2025-12-20-solo.md
    make hypothesis-conclude ID=1
    make hypothesis-list
    make hypothesis-view ID=1
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        create_hypothesis()
    
    elif command == "test":
        if len(sys.argv) < 4:
            print("❌ Usage: python tools/hypothesis_testing.py test <id> <event_file>")
            sys.exit(1)
        
        try:
            hypothesis_id = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Hypothesis ID must be a number")
            sys.exit(1)
        
        event_file = Path(sys.argv[3])
        link_hypothesis_to_event(hypothesis_id, event_file)
    
    elif command == "conclude":
        if len(sys.argv) < 3:
            print("❌ Usage: python tools/hypothesis_testing.py conclude <id>")
            sys.exit(1)
        
        try:
            hypothesis_id = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Hypothesis ID must be a number")
            sys.exit(1)
        
        conclude_hypothesis(hypothesis_id)
    
    elif command == "list":
        status_filter = None
        if len(sys.argv) > 2 and sys.argv[2] == "--status":
            if len(sys.argv) > 3:
                status_filter = sys.argv[3]
        
        list_hypotheses(status_filter)
    
    elif command == "view":
        if len(sys.argv) < 3:
            print("❌ Usage: python tools/hypothesis_testing.py view <id>")
            sys.exit(1)
        
        try:
            hypothesis_id = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Hypothesis ID must be a number")
            sys.exit(1)
        
        view_hypothesis(hypothesis_id)
    
    else:
        print(f"❌ Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
