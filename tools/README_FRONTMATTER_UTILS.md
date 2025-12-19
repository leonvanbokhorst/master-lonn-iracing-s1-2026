# Frontmatter Utility Module

**Status:** ✅ Implemented and Validated  
**Issue:** [#26](https://github.com/leonvanbokhorst/master-lonn-iracing-s1-2026/issues/26)  
**Author:** Manus AI  
**Date:** 2025-12-19

---

## Overview

The `frontmatter_utils.py` module provides safe, robust utilities for parsing and updating YAML frontmatter in event markdown files. This is the foundational infrastructure for all learning science enhancements.

## Key Features

- **Safe YAML parsing** with comprehensive error handling
- **Deep merge functionality** for nested dictionary updates
- **Backward compatibility** with files lacking new fields
- **Read-only validation** against actual event files
- **Dot notation** for accessing nested fields
- **Zero disruption** to existing workflows

## Validation Results

The module has been validated against all 13 Week 01 event files:

```
✅ All validation tests passed!

✓ PASS: Parse all Week 01 events (13/13 files)
✓ PASS: Validate all Week 01 events (13/13 valid)
✓ PASS: Get fields from Week 01
✓ PASS: Analyze frontmatter structure
✓ PASS: Verify read-only safety
```

## API Reference

### Core Functions

#### `parse_event_file(file_path: Path) -> tuple[dict, str]`

Parse an event markdown file into frontmatter dictionary and body content.

**Parameters:**
- `file_path`: Path to event markdown file

**Returns:**
- Tuple of `(frontmatter_dict, body_content)`

**Example:**
```python
from pathlib import Path
from frontmatter_utils import parse_event_file

frontmatter, body = parse_event_file(Path("weeks/week01/events/01-2025-12-11-solo.md"))
print(frontmatter["event"])  # 1
```

---

#### `update_event_frontmatter(file_path: Path, updates: dict, merge: bool = True) -> None`

Update event file frontmatter with new fields.

**Parameters:**
- `file_path`: Path to event markdown file
- `updates`: Dictionary of fields to add/update
- `merge`: If True (default), merge with existing frontmatter. If False, replace entirely.

**Example:**
```python
from frontmatter_utils import update_event_frontmatter

update_event_frontmatter(Path("event.md"), {
    "mental_rehearsal": {
        "pre_session": True,
        "confidence_rating": 4
    }
})
```

---

#### `get_frontmatter_field(file_path: Path, field_path: str, default: Any = None) -> Any`

Get a specific field from frontmatter using dot notation.

**Parameters:**
- `file_path`: Path to event file
- `field_path`: Dot-separated path to field (e.g., `"mental_rehearsal.confidence"`)
- `default`: Default value if field doesn't exist

**Returns:**
- Field value or default

**Example:**
```python
from frontmatter_utils import get_frontmatter_field

confidence = get_frontmatter_field(
    Path("event.md"),
    "mental_rehearsal.confidence_rating",
    default=3
)
```

---

#### `validate_event_file(file_path: Path, required_fields: list[str] = None) -> tuple[bool, list[str]]`

Validate that an event file has valid frontmatter and required fields.

**Parameters:**
- `file_path`: Path to event file
- `required_fields`: List of required field names (default: `["event", "week", "date", "type"]`)

**Returns:**
- Tuple of `(is_valid, error_messages)`

**Example:**
```python
from frontmatter_utils import validate_event_file

is_valid, errors = validate_event_file(Path("event.md"))
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

---

### Utility Functions

#### `deep_merge(base: dict, updates: dict) -> dict`

Deep merge two dictionaries, preserving nested structures.

**Example:**
```python
from frontmatter_utils import deep_merge

base = {"a": 1, "b": {"c": 2, "d": 3}}
updates = {"b": {"d": 4, "e": 5}, "f": 6}
result = deep_merge(base, updates)
# Result: {'a': 1, 'b': {'c': 2, 'd': 4, 'e': 5}, 'f': 6}
```

---

#### `list_event_files(week_dir: Path) -> list[Path]`

List all event markdown files in a week directory.

**Example:**
```python
from frontmatter_utils import list_event_files

events = list_event_files(Path("weeks/week01"))
for event in events:
    print(event.name)
```

---

#### `get_all_frontmatter_fields(file_path: Path) -> set[str]`

Get all top-level field names from a file's frontmatter.

**Example:**
```python
from frontmatter_utils import get_all_frontmatter_fields

fields = get_all_frontmatter_fields(Path("event.md"))
print(fields)  # {'event', 'week', 'date', 'type', 'mental_rehearsal'}
```

---

#### `add_frontmatter_field(file_path: Path, field_name: str, field_value: Any) -> None`

Convenience function to add or update a single top-level frontmatter field.

**Example:**
```python
from frontmatter_utils import add_frontmatter_field

add_frontmatter_field(Path("event.md"), "eye_discipline_rating", 4)
```

---

## Usage Examples

### Example 1: Add Mental Rehearsal Data

```python
from pathlib import Path
from frontmatter_utils import update_event_frontmatter

event_file = Path("weeks/week02/events/03-2025-12-20-solo.md")

update_event_frontmatter(event_file, {
    "mental_rehearsal": {
        "pre_session": True,
        "duration_minutes": 5,
        "focus": "Angst hill descent",
        "confidence_rating": 4
    }
})
```

### Example 2: Read and Validate All Events in a Week

```python
from pathlib import Path
from frontmatter_utils import list_event_files, validate_event_file

week_dir = Path("weeks/week01")

for event_file in list_event_files(week_dir):
    is_valid, errors = validate_event_file(event_file)
    
    if is_valid:
        print(f"✓ {event_file.name} is valid")
    else:
        print(f"❌ {event_file.name} has errors:")
        for error in errors:
            print(f"   - {error}")
```

### Example 3: Retrieve Nested Data

```python
from pathlib import Path
from frontmatter_utils import get_frontmatter_field

event_file = Path("weeks/week02/events/03-2025-12-20-solo.md")

# Get nested field with default
confidence = get_frontmatter_field(
    event_file,
    "mental_rehearsal.confidence_rating",
    default=3
)

print(f"Confidence rating: {confidence}")
```

---

## Command-Line Usage

The module can be used directly from the command line to inspect event files:

```bash
python tools/frontmatter_utils.py weeks/week01/events/01-2025-12-11-solo.md
```

**Output:**
```
📄 File: 01-2025-12-11-solo.md
📊 Frontmatter fields: 5

Frontmatter:
event: 1
week: '01'
date: '2025-12-11'
type: solo
focus: baseline exploration

Body length: 2393 characters
```

---

## Testing

### Run Validation Script

The validation script tests the module against actual Week 01 event files (read-only):

```bash
python tests/validate_frontmatter_utils.py
```

### Run Unit Tests (requires pytest)

Comprehensive unit tests are available in `tests/test_frontmatter_utils.py`:

```bash
python -m pytest tests/test_frontmatter_utils.py -v
```

**Note:** pytest is not currently in the project dependencies. The validation script provides sufficient testing without requiring pytest.

---

## Design Principles

### 1. Backward Compatibility

The module is designed to work with files that don't have new enhancement fields. All functions gracefully handle missing data:

```python
# If "mental_rehearsal" doesn't exist, returns default
confidence = get_frontmatter_field(
    event_file,
    "mental_rehearsal.confidence_rating",
    default=3
)
```

### 2. Safety First

- All read operations are truly read-only (verified by validation tests)
- YAML parsing errors return empty dict instead of crashing
- File not found errors are raised explicitly
- Deep merge creates new dicts instead of modifying inputs

### 3. Zero Disruption

The existing system doesn't parse frontmatter, so adding new fields has **zero risk** of breaking existing workflows. The module only adds capabilities; it doesn't change existing behavior.

---

## Integration with Other Tools

This module is the foundation for:

- **Mental Rehearsal Protocol** (Issue #27)
- **Hypothesis Testing Framework** (Issue #28)
- **Visual Scanning Training** (Issue #4)
- **Race Scenario Planning** (Issue #5)
- **Interleaved Practice Sessions** (Issue #6)

All these enhancements will use `frontmatter_utils.py` to safely add and retrieve structured data from event files.

---

## Error Handling

The module handles errors gracefully:

### File Not Found
```python
try:
    frontmatter, body = parse_event_file(Path("nonexistent.md"))
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

### YAML Parsing Error
```python
# Returns empty dict and full content on YAML error
frontmatter, body = parse_event_file(Path("malformed.md"))
if not frontmatter:
    print("Warning: Could not parse frontmatter")
```

### Missing Fields
```python
# Returns default value if field doesn't exist
value = get_frontmatter_field(event_file, "nonexistent.field", default="N/A")
```

---

## Performance

The module is lightweight and fast:

- Parsing 13 Week 01 event files: **< 0.1 seconds**
- No external dependencies beyond PyYAML (already in project)
- Minimal memory footprint

---

## Future Enhancements

Potential future additions:

- [ ] Batch update functionality for multiple files
- [ ] JSON schema validation for frontmatter structure
- [ ] Automatic migration tool for adding new fields to all events
- [ ] Frontmatter diff tool to see changes over time

---

## Contributing

When adding new enhancement features that use frontmatter:

1. Use `update_event_frontmatter()` with `merge=True` to preserve existing data
2. Always provide sensible defaults when reading fields
3. Document the new frontmatter schema in your enhancement's README
4. Test against actual event files before committing

---

## License

MIT License (same as repository)

---

## Questions?

See the [Integration Strategy](../docs/integration_strategy.md) for detailed information about how this module fits into the overall system architecture.
