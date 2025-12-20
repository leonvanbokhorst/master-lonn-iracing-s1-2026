"""
Unit Tests for Frontmatter Utility Module
==========================================

Comprehensive test suite for frontmatter_utils.py.

Run with:
    python -m pytest tests/test_frontmatter_utils.py -v

Author: Manus AI
Date: 2025-12-19
"""

import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from frontmatter_utils import (
    parse_event_file,
    update_event_frontmatter,
    write_event_file,
    deep_merge,
    get_frontmatter_field,
    validate_event_file,
    list_event_files,
    get_all_frontmatter_fields,
    add_frontmatter_field
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_event_file(temp_dir):
    """Create a sample event file with frontmatter."""
    event_file = temp_dir / "test-event.md"
    content = """---
event: 1
week: "01"
date: "2025-12-11"
type: "solo"
---

# Event #1 – 2025-12-11 – solo

Some content here.
"""
    event_file.write_text(content)
    return event_file


@pytest.fixture
def minimal_event_file(temp_dir):
    """Create an event file with minimal frontmatter."""
    event_file = temp_dir / "minimal-event.md"
    content = """---
event: 1
---

# Minimal Event
"""
    event_file.write_text(content)
    return event_file


@pytest.fixture
def no_frontmatter_file(temp_dir):
    """Create a file without frontmatter."""
    event_file = temp_dir / "no-frontmatter.md"
    content = """# Event Without Frontmatter

This file has no YAML frontmatter.
"""
    event_file.write_text(content)
    return event_file


# ============================================================================
# Test: parse_event_file
# ============================================================================

def test_parse_event_with_frontmatter(sample_event_file):
    """Test parsing event file with complete frontmatter."""
    frontmatter, body = parse_event_file(sample_event_file)
    
    assert frontmatter["event"] == 1
    assert frontmatter["week"] == "01"
    assert frontmatter["date"] == "2025-12-11"
    assert frontmatter["type"] == "solo"
    assert "# Event #1" in body
    assert "Some content here." in body


def test_parse_event_without_frontmatter(no_frontmatter_file):
    """Test parsing event file without frontmatter."""
    frontmatter, body = parse_event_file(no_frontmatter_file)
    
    assert frontmatter == {}
    assert "# Event Without Frontmatter" in body
    assert "This file has no YAML frontmatter." in body


def test_parse_event_with_empty_frontmatter(temp_dir):
    """Test parsing event file with empty frontmatter."""
    event_file = temp_dir / "empty-frontmatter.md"
    content = """---
---

# Content
"""
    event_file.write_text(content)
    
    frontmatter, body = parse_event_file(event_file)
    
    assert frontmatter == {}
    assert "# Content" in body


def test_parse_event_file_not_found(temp_dir):
    """Test parsing non-existent file raises FileNotFoundError."""
    non_existent = temp_dir / "does-not-exist.md"
    
    with pytest.raises(FileNotFoundError):
        parse_event_file(non_existent)


def test_parse_event_with_malformed_yaml(temp_dir):
    """Test parsing file with malformed YAML returns empty dict."""
    event_file = temp_dir / "malformed.md"
    content = """---
event: 1
week: [unclosed list
---

# Content
"""
    event_file.write_text(content)
    
    frontmatter, body = parse_event_file(event_file)
    
    # Should return empty dict and full content on YAML error
    assert frontmatter == {}
    assert "event: 1" in body


def test_parse_event_preserves_body_formatting(sample_event_file):
    """Test that body content is preserved exactly."""
    frontmatter, body = parse_event_file(sample_event_file)
    
    # Body should start with newline after ---
    assert body.startswith("\n")
    assert body.count("\n") >= 3  # Multiple lines preserved


# ============================================================================
# Test: write_event_file
# ============================================================================

def test_write_event_file_creates_valid_format(temp_dir):
    """Test writing event file creates valid YAML frontmatter."""
    event_file = temp_dir / "new-event.md"
    
    frontmatter = {
        "event": 1,
        "week": "01",
        "date": "2025-12-11",
        "type": "solo"
    }
    body = "\n# Event #1\n\nContent here.\n"
    
    write_event_file(event_file, frontmatter, body)
    
    # Read back and verify
    content = event_file.read_text()
    
    assert content.startswith("---\n")
    assert "event: 1" in content
    assert "week: '01'" in content or 'week: "01"' in content
    assert "---\n\n# Event #1" in content


def test_write_event_file_adds_newline_to_body(temp_dir):
    """Test that write_event_file adds newline to body if missing."""
    event_file = temp_dir / "test.md"
    
    frontmatter = {"event": 1}
    body = "# Content"  # No leading newline
    
    write_event_file(event_file, frontmatter, body)
    
    content = event_file.read_text()
    assert "---\n\n# Content" in content


def test_write_event_file_preserves_unicode(temp_dir):
    """Test that unicode characters are preserved."""
    event_file = temp_dir / "unicode.md"
    
    frontmatter = {"event": 1, "note": "Testing σ and 🏎️"}
    body = "\n# Content with émojis 🎯\n"
    
    write_event_file(event_file, frontmatter, body)
    
    # Read back
    frontmatter_read, body_read = parse_event_file(event_file)
    
    assert frontmatter_read["note"] == "Testing σ and 🏎️"
    assert "🎯" in body_read


# ============================================================================
# Test: deep_merge
# ============================================================================

def test_deep_merge_simple():
    """Test deep merge with simple non-nested dicts."""
    base = {"a": 1, "b": 2}
    updates = {"b": 3, "c": 4}
    
    result = deep_merge(base, updates)
    
    assert result == {"a": 1, "b": 3, "c": 4}
    # Ensure original dicts are not modified
    assert base == {"a": 1, "b": 2}
    assert updates == {"b": 3, "c": 4}


def test_deep_merge_nested():
    """Test deep merge with nested dicts."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    updates = {"b": {"d": 4, "e": 5}, "f": 6}
    
    result = deep_merge(base, updates)
    
    assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}


def test_deep_merge_deeply_nested():
    """Test deep merge with deeply nested structures."""
    base = {
        "level1": {
            "level2": {
                "level3": {"a": 1, "b": 2}
            }
        }
    }
    updates = {
        "level1": {
            "level2": {
                "level3": {"b": 3, "c": 4}
            }
        }
    }
    
    result = deep_merge(base, updates)
    
    assert result["level1"]["level2"]["level3"] == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_overwrites_non_dict():
    """Test that non-dict values are overwritten, not merged."""
    base = {"a": [1, 2, 3]}
    updates = {"a": [4, 5]}
    
    result = deep_merge(base, updates)
    
    assert result == {"a": [4, 5]}


def test_deep_merge_empty_dicts():
    """Test deep merge with empty dicts."""
    assert deep_merge({}, {"a": 1}) == {"a": 1}
    assert deep_merge({"a": 1}, {}) == {"a": 1}
    assert deep_merge({}, {}) == {}


# ============================================================================
# Test: update_event_frontmatter
# ============================================================================

def test_update_frontmatter_merge_mode(sample_event_file):
    """Test updating frontmatter with merge mode (default)."""
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"pre_session": True, "confidence": 4}
    })
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    # Original fields preserved
    assert frontmatter["event"] == 1
    assert frontmatter["week"] == "01"
    
    # New field added
    assert frontmatter["mental_rehearsal"]["pre_session"] == True
    assert frontmatter["mental_rehearsal"]["confidence"] == 4


def test_update_frontmatter_replace_mode(sample_event_file):
    """Test updating frontmatter with replace mode."""
    update_event_frontmatter(
        sample_event_file,
        {"new_field": "value"},
        merge=False
    )
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    # Old fields should be gone
    assert "event" not in frontmatter
    assert "week" not in frontmatter
    
    # Only new field present
    assert frontmatter == {"new_field": "value"}


def test_update_frontmatter_nested_merge(sample_event_file):
    """Test updating nested frontmatter fields."""
    # Add initial nested structure
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"pre_session": True, "confidence": 3}
    })
    
    # Update part of nested structure
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"confidence": 5}
    })
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    # Both fields should be present
    assert frontmatter["mental_rehearsal"]["pre_session"] == True
    assert frontmatter["mental_rehearsal"]["confidence"] == 5


def test_update_frontmatter_preserves_body(sample_event_file):
    """Test that updating frontmatter doesn't modify body."""
    _, original_body = parse_event_file(sample_event_file)
    
    update_event_frontmatter(sample_event_file, {"new_field": "value"})
    
    _, updated_body = parse_event_file(sample_event_file)
    
    assert original_body == updated_body


def test_update_frontmatter_file_not_found(temp_dir):
    """Test updating non-existent file raises FileNotFoundError."""
    non_existent = temp_dir / "does-not-exist.md"
    
    with pytest.raises(FileNotFoundError):
        update_event_frontmatter(non_existent, {"field": "value"})


# ============================================================================
# Test: get_frontmatter_field
# ============================================================================

def test_get_frontmatter_field_simple(sample_event_file):
    """Test getting a simple top-level field."""
    event = get_frontmatter_field(sample_event_file, "event")
    
    assert event == 1


def test_get_frontmatter_field_nested(sample_event_file):
    """Test getting a nested field with dot notation."""
    # Add nested structure
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"pre_session": True, "confidence": 4}
    })
    
    confidence = get_frontmatter_field(
        sample_event_file,
        "mental_rehearsal.confidence"
    )
    
    assert confidence == 4


def test_get_frontmatter_field_deeply_nested(sample_event_file):
    """Test getting a deeply nested field."""
    update_event_frontmatter(sample_event_file, {
        "level1": {"level2": {"level3": "value"}}
    })
    
    value = get_frontmatter_field(
        sample_event_file,
        "level1.level2.level3"
    )
    
    assert value == "value"


def test_get_frontmatter_field_missing_returns_default(sample_event_file):
    """Test that missing fields return default value."""
    value = get_frontmatter_field(
        sample_event_file,
        "nonexistent.field",
        default="default_value"
    )
    
    assert value == "default_value"


def test_get_frontmatter_field_missing_nested_returns_default(sample_event_file):
    """Test that partially missing nested paths return default."""
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"pre_session": True}
    })
    
    # Field exists but nested key doesn't
    value = get_frontmatter_field(
        sample_event_file,
        "mental_rehearsal.nonexistent",
        default=None
    )
    
    assert value is None


def test_get_frontmatter_field_none_default(sample_event_file):
    """Test that default is None when not specified."""
    value = get_frontmatter_field(sample_event_file, "nonexistent")
    
    assert value is None


# ============================================================================
# Test: validate_event_file
# ============================================================================

def test_validate_event_file_valid(sample_event_file):
    """Test validation passes for valid event file."""
    is_valid, errors = validate_event_file(sample_event_file)
    
    assert is_valid == True
    assert errors == []


def test_validate_event_file_missing_required_field(minimal_event_file):
    """Test validation fails for missing required fields."""
    is_valid, errors = validate_event_file(minimal_event_file)
    
    assert is_valid == False
    assert len(errors) == 3  # Missing week, date, type
    assert any("week" in err for err in errors)
    assert any("date" in err for err in errors)
    assert any("type" in err for err in errors)


def test_validate_event_file_custom_required_fields(sample_event_file):
    """Test validation with custom required fields."""
    is_valid, errors = validate_event_file(
        sample_event_file,
        required_fields=["event", "mental_rehearsal"]
    )
    
    assert is_valid == False
    assert len(errors) == 1
    assert "mental_rehearsal" in errors[0]


def test_validate_event_file_not_found(temp_dir):
    """Test validation fails for non-existent file."""
    non_existent = temp_dir / "does-not-exist.md"
    
    is_valid, errors = validate_event_file(non_existent)
    
    assert is_valid == False
    assert len(errors) == 1
    assert "not found" in errors[0].lower()


# ============================================================================
# Test: list_event_files
# ============================================================================

def test_list_event_files(temp_dir):
    """Test listing event files in a week directory."""
    week_dir = temp_dir / "week01"
    events_dir = week_dir / "events"
    events_dir.mkdir(parents=True)
    
    # Create some event files
    (events_dir / "01-2025-12-11-solo.md").write_text("# Event 1")
    (events_dir / "02-2025-12-12-solo.md").write_text("# Event 2")
    (events_dir / "03-2025-12-13-race.md").write_text("# Event 3")
    
    events = list_event_files(week_dir)
    
    assert len(events) == 3
    assert all(e.suffix == ".md" for e in events)
    assert events[0].name == "01-2025-12-11-solo.md"
    assert events[2].name == "03-2025-12-13-race.md"


def test_list_event_files_empty_directory(temp_dir):
    """Test listing events in empty directory."""
    week_dir = temp_dir / "week01"
    events_dir = week_dir / "events"
    events_dir.mkdir(parents=True)
    
    events = list_event_files(week_dir)
    
    assert events == []


def test_list_event_files_no_events_directory(temp_dir):
    """Test listing events when events directory doesn't exist."""
    week_dir = temp_dir / "week01"
    week_dir.mkdir()
    
    events = list_event_files(week_dir)
    
    assert events == []


# ============================================================================
# Test: get_all_frontmatter_fields
# ============================================================================

def test_get_all_frontmatter_fields(sample_event_file):
    """Test getting all top-level field names."""
    fields = get_all_frontmatter_fields(sample_event_file)
    
    assert fields == {"event", "week", "date", "type"}


def test_get_all_frontmatter_fields_with_nested(sample_event_file):
    """Test that nested fields show only top-level key."""
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"pre_session": True, "confidence": 4}
    })
    
    fields = get_all_frontmatter_fields(sample_event_file)
    
    assert "mental_rehearsal" in fields
    assert "pre_session" not in fields  # Nested field not in top-level set


def test_get_all_frontmatter_fields_empty(no_frontmatter_file):
    """Test getting fields from file with no frontmatter."""
    fields = get_all_frontmatter_fields(no_frontmatter_file)
    
    assert fields == set()


# ============================================================================
# Test: add_frontmatter_field
# ============================================================================

def test_add_frontmatter_field_simple(sample_event_file):
    """Test adding a simple field."""
    add_frontmatter_field(sample_event_file, "eye_discipline_rating", 4)
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    assert frontmatter["eye_discipline_rating"] == 4
    # Original fields preserved
    assert frontmatter["event"] == 1


def test_add_frontmatter_field_complex(sample_event_file):
    """Test adding a complex nested field."""
    add_frontmatter_field(sample_event_file, "mental_rehearsal", {
        "pre_session": True,
        "confidence": 5
    })
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    assert frontmatter["mental_rehearsal"]["pre_session"] == True
    assert frontmatter["mental_rehearsal"]["confidence"] == 5


def test_add_frontmatter_field_overwrites_existing(sample_event_file):
    """Test that adding an existing field overwrites it."""
    add_frontmatter_field(sample_event_file, "event", 99)
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    assert frontmatter["event"] == 99


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_workflow_add_and_retrieve(sample_event_file):
    """Test complete workflow: add nested data and retrieve it."""
    # Add mental rehearsal data
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {
            "pre_session": True,
            "duration_minutes": 5,
            "focus": "T1-T3 transitions",
            "confidence_rating": 4
        }
    })
    
    # Retrieve specific field
    confidence = get_frontmatter_field(
        sample_event_file,
        "mental_rehearsal.confidence_rating"
    )
    
    assert confidence == 4
    
    # Validate file still has required fields
    is_valid, errors = validate_event_file(sample_event_file)
    assert is_valid == True


def test_multiple_updates_preserve_data(sample_event_file):
    """Test that multiple updates preserve all data."""
    # First update
    update_event_frontmatter(sample_event_file, {
        "mental_rehearsal": {"pre_session": True}
    })
    
    # Second update
    update_event_frontmatter(sample_event_file, {
        "race_scenarios": {"scenario_1": "data"}
    })
    
    # Third update
    update_event_frontmatter(sample_event_file, {
        "practice_structure": {"type": "interleaved"}
    })
    
    frontmatter, _ = parse_event_file(sample_event_file)
    
    # All updates should be present
    assert "mental_rehearsal" in frontmatter
    assert "race_scenarios" in frontmatter
    assert "practice_structure" in frontmatter
    
    # Original fields preserved
    assert frontmatter["event"] == 1
    assert frontmatter["week"] == "01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
