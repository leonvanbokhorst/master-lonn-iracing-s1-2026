"""
Validation Script for Frontmatter Utils
========================================

Simple validation script that tests frontmatter_utils.py against
actual Week 01 event files (read-only).

This script doesn't require pytest and can be run directly.

Usage:
    python tests/validate_frontmatter_utils.py

Author: Manus AI
Date: 2025-12-19
"""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from frontmatter_utils import (
    parse_event_file,
    validate_event_file,
    list_event_files,
    get_frontmatter_field,
    get_all_frontmatter_fields
)


def test_parse_all_week01_events():
    """Test parsing all Week 01 event files."""
    print("\n" + "="*70)
    print("TEST 1: Parse all Week 01 event files")
    print("="*70)
    
    week01_dir = Path("weeks/week01")
    
    if not week01_dir.exists():
        print("❌ Week 01 directory not found")
        return False
    
    events = list_event_files(week01_dir)
    
    if not events:
        print("❌ No event files found in Week 01")
        return False
    
    print(f"✓ Found {len(events)} event files")
    
    success_count = 0
    for event_file in events:
        try:
            frontmatter, body = parse_event_file(event_file)
            
            # Check that we got something
            if not isinstance(frontmatter, dict):
                print(f"❌ {event_file.name}: frontmatter is not a dict")
                continue
            
            if not isinstance(body, str):
                print(f"❌ {event_file.name}: body is not a string")
                continue
            
            print(f"✓ {event_file.name}: Parsed successfully")
            print(f"  - Frontmatter fields: {len(frontmatter)}")
            print(f"  - Body length: {len(body)} characters")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ {event_file.name}: {e}")
    
    print(f"\n✓ Successfully parsed {success_count}/{len(events)} files")
    return success_count == len(events)


def test_validate_all_week01_events():
    """Test validation of all Week 01 event files."""
    print("\n" + "="*70)
    print("TEST 2: Validate all Week 01 event files")
    print("="*70)
    
    week01_dir = Path("weeks/week01")
    events = list_event_files(week01_dir)
    
    valid_count = 0
    for event_file in events:
        is_valid, errors = validate_event_file(event_file)
        
        if is_valid:
            print(f"✓ {event_file.name}: Valid")
            valid_count += 1
        else:
            print(f"⚠️  {event_file.name}: Validation issues:")
            for error in errors:
                print(f"   - {error}")
    
    print(f"\n✓ {valid_count}/{len(events)} files are valid")
    return valid_count > 0


def test_get_fields_from_week01():
    """Test retrieving specific fields from Week 01 events."""
    print("\n" + "="*70)
    print("TEST 3: Retrieve specific fields from Week 01 events")
    print("="*70)
    
    week01_dir = Path("weeks/week01")
    events = list_event_files(week01_dir)
    
    if not events:
        print("❌ No events to test")
        return False
    
    # Test with first event
    event_file = events[0]
    
    print(f"\nTesting with: {event_file.name}")
    
    # Get all fields
    fields = get_all_frontmatter_fields(event_file)
    print(f"✓ Top-level fields: {fields}")
    
    # Get specific fields
    event_num = get_frontmatter_field(event_file, "event", default="N/A")
    week = get_frontmatter_field(event_file, "week", default="N/A")
    event_type = get_frontmatter_field(event_file, "type", default="N/A")
    
    print(f"✓ Event number: {event_num}")
    print(f"✓ Week: {week}")
    print(f"✓ Type: {event_type}")
    
    # Test getting non-existent field (should return default)
    nonexistent = get_frontmatter_field(event_file, "nonexistent_field", default="DEFAULT")
    
    if nonexistent == "DEFAULT":
        print(f"✓ Non-existent field returns default: {nonexistent}")
        return True
    else:
        print(f"❌ Non-existent field did not return default")
        return False


def test_frontmatter_structure():
    """Test the structure of frontmatter in Week 01 events."""
    print("\n" + "="*70)
    print("TEST 4: Analyze frontmatter structure across Week 01")
    print("="*70)
    
    week01_dir = Path("weeks/week01")
    events = list_event_files(week01_dir)
    
    # Collect all unique fields
    all_fields = set()
    field_counts = {}
    
    for event_file in events:
        fields = get_all_frontmatter_fields(event_file)
        all_fields.update(fields)
        
        for field in fields:
            field_counts[field] = field_counts.get(field, 0) + 1
    
    print(f"\n✓ Unique fields found across all events: {len(all_fields)}")
    print("\nField usage:")
    for field in sorted(all_fields):
        count = field_counts[field]
        percentage = (count / len(events)) * 100
        print(f"  - {field:20s}: {count:2d}/{len(events):2d} events ({percentage:5.1f}%)")
    
    # Check for required fields
    required = ["event", "week", "date", "type"]
    missing_required = set(required) - all_fields
    
    if missing_required:
        print(f"\n⚠️  Some events missing required fields: {missing_required}")
    else:
        print(f"\n✓ All required fields present: {required}")
    
    return True


def test_read_only_safety():
    """Verify that read operations don't modify files."""
    print("\n" + "="*70)
    print("TEST 5: Verify read-only safety")
    print("="*70)
    
    week01_dir = Path("weeks/week01")
    events = list_event_files(week01_dir)
    
    if not events:
        print("❌ No events to test")
        return False
    
    event_file = events[0]
    
    # Get original modification time
    original_mtime = event_file.stat().st_mtime
    
    # Perform read operations
    frontmatter, body = parse_event_file(event_file)
    fields = get_all_frontmatter_fields(event_file)
    is_valid, errors = validate_event_file(event_file)
    value = get_frontmatter_field(event_file, "event")
    
    # Check modification time hasn't changed
    new_mtime = event_file.stat().st_mtime
    
    if original_mtime == new_mtime:
        print(f"✓ File not modified by read operations: {event_file.name}")
        return True
    else:
        print(f"❌ File was modified by read operations!")
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("FRONTMATTER UTILS VALIDATION")
    print("Testing against actual Week 01 event files (read-only)")
    print("="*70)
    
    tests = [
        ("Parse all Week 01 events", test_parse_all_week01_events),
        ("Validate all Week 01 events", test_validate_all_week01_events),
        ("Get fields from Week 01", test_get_fields_from_week01),
        ("Analyze frontmatter structure", test_frontmatter_structure),
        ("Verify read-only safety", test_read_only_safety),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All validation tests passed!")
        print("The frontmatter_utils module is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
