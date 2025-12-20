# Schema Integration Strategy: Zero-Disruption Migration Plan

## Executive Summary

Based on deep analysis of the existing codebase, **the current system does not parse YAML frontmatter at all**. This is excellent news: it means we can add new frontmatter fields with **zero risk of breaking existing workflows**. The integration strategy leverages this fact to enable a gradual, opt-in adoption model.

---

## Integration Principles

### 1. Backward Compatibility First
- All new features are **opt-in**
- Existing workflows continue unchanged
- Old event files work perfectly without new fields
- New tools gracefully handle missing data

### 2. Additive, Not Destructive
- Never modify existing data structures
- Only add new fields/files
- Preserve all existing content when updating files

### 3. Graceful Degradation
- Tools work with partial data
- Missing fields use sensible defaults
- Clear error messages when data is truly required

### 4. Incremental Adoption
- Start with new events only
- Optionally backfill old events
- No "big bang" migration required

---

## Strategy 1: Frontmatter Extension (RECOMMENDED)

### Approach

Add new frontmatter fields to event markdown files. Since existing tools don't parse frontmatter, this is completely safe.

### Implementation Pattern

**Current Event File:**
```yaml
---
event: 12
week: "01"
date: "2025-12-16"
type: "race"
---
```

**Enhanced Event File:**
```yaml
---
event: 12
week: "01"
date: "2025-12-16"
type: "race"

# New fields (optional, only added when used)
mental_rehearsal:
  pre_session: true
  duration_minutes: 5
  focus: "T1-T3 transitions"
  confidence_rating: 4

race_scenarios:
  pre_race_planning:
    - scenario: "P2 dives inside at T1"
      planned_response: "Give space, repass at T6"
      occurred: true

practice_structure:
  type: "interleaved"
  blocks:
    - laps: [1, 2, 3, 4, 5]
      focus: "baseline"
---
```

### Safe Update Mechanism

**File: `tools/frontmatter_utils.py`** (new utility module)

```python
"""
Utility functions for safe frontmatter manipulation.
Handles both YAML parsing and preservation of existing content.
"""

import yaml
from pathlib import Path
from typing import Any, Optional

def parse_event_file(file_path: Path) -> tuple[dict, str]:
    """
    Parse event markdown file into frontmatter dict and body content.
    
    Returns:
        (frontmatter_dict, body_content)
    """
    content = file_path.read_text()
    
    if not content.startswith("---"):
        # No frontmatter, return empty dict and full content
        return {}, content
    
    try:
        # Split on --- delimiters
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        
        frontmatter_str = parts[1]
        body = parts[2]
        
        # Parse YAML
        frontmatter = yaml.safe_load(frontmatter_str) or {}
        
        return frontmatter, body
    
    except yaml.YAMLError as e:
        print(f"⚠️  Warning: Could not parse frontmatter in {file_path.name}: {e}")
        return {}, content

def update_event_frontmatter(
    file_path: Path,
    updates: dict[str, Any],
    merge: bool = True
) -> None:
    """
    Update event file frontmatter with new fields.
    
    Args:
        file_path: Path to event markdown file
        updates: Dictionary of fields to add/update
        merge: If True, merge with existing frontmatter. If False, replace.
    """
    frontmatter, body = parse_event_file(file_path)
    
    if merge:
        # Deep merge: preserve existing fields, add new ones
        frontmatter = deep_merge(frontmatter, updates)
    else:
        # Replace: use updates as new frontmatter
        frontmatter = updates
    
    # Write back
    write_event_file(file_path, frontmatter, body)

def write_event_file(file_path: Path, frontmatter: dict, body: str) -> None:
    """
    Write event file with frontmatter and body.
    Ensures proper YAML formatting and content preservation.
    """
    # Serialize frontmatter to YAML
    frontmatter_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True
    )
    
    # Ensure body starts with newline if it doesn't
    if body and not body.startswith("\n"):
        body = "\n" + body
    
    # Construct full content
    content = f"---\n{frontmatter_str}---{body}"
    
    # Write to file
    file_path.write_text(content)

def deep_merge(base: dict, updates: dict) -> dict:
    """
    Deep merge two dictionaries.
    Updates are merged into base, preserving nested structures.
    """
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Overwrite or add new key
            result[key] = value
    
    return result

def get_frontmatter_field(
    file_path: Path,
    field_path: str,
    default: Any = None
) -> Any:
    """
    Get a specific field from frontmatter using dot notation.
    
    Example:
        get_frontmatter_field(event_file, "mental_rehearsal.pre_session", False)
    
    Args:
        file_path: Path to event file
        field_path: Dot-separated path to field (e.g., "mental_rehearsal.confidence")
        default: Default value if field doesn't exist
    
    Returns:
        Field value or default
    """
    frontmatter, _ = parse_event_file(file_path)
    
    # Navigate nested dict using dot notation
    keys = field_path.split(".")
    value = frontmatter
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value
```

### Usage Example

```python
from pathlib import Path
from frontmatter_utils import update_event_frontmatter

# Add mental rehearsal data to existing event
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

### Benefits

✅ **Zero risk**: Existing tools ignore new frontmatter fields  
✅ **Gradual adoption**: Add fields only when needed  
✅ **Human-readable**: YAML is easy to read and edit manually  
✅ **Structured data**: Easy to parse and analyze programmatically  
✅ **Git-friendly**: Changes are clear in diffs  

### Limitations

⚠️ **Manual editing risk**: Users could break YAML syntax  
⚠️ **File size growth**: Frontmatter can become large with many fields  

---

## Strategy 2: Separate Data Files (ALTERNATIVE)

### Approach

Store enhancement data in separate YAML files alongside event markdown files.

### Structure

```
weeks/week02/events/
├── 03-2025-12-20-solo.md          # Original event file (unchanged)
└── 03-2025-12-20-solo.data.yaml   # Enhancement data (new)
```

**Enhancement Data File:**
```yaml
# weeks/week02/events/03-2025-12-20-solo.data.yaml
event: 3
week: "02"
date: "2025-12-20"

mental_rehearsal:
  pre_session: true
  duration_minutes: 5
  focus: "Angst hill descent"
  confidence_rating: 4

practice_structure:
  type: "interleaved"
  blocks:
    - laps: [1, 2, 3, 4, 5]
      focus: "baseline"
```

### Benefits

✅ **Zero risk**: Original files completely untouched  
✅ **Clean separation**: Enhancement data separate from core data  
✅ **Easy rollback**: Delete `.data.yaml` files to remove enhancements  
✅ **No parsing conflicts**: No risk of breaking YAML in markdown files  

### Limitations

⚠️ **File proliferation**: Doubles number of files per event  
⚠️ **Synchronization**: Need to keep `.md` and `.data.yaml` in sync  
⚠️ **Complexity**: Tools need to load data from two files  

---

## Strategy 3: Hybrid Approach (RECOMMENDED FOR PRODUCTION)

### Approach

Combine both strategies based on data type:

**Frontmatter Extension** for:
- Small, frequently-used fields
- Data that enhances human readability
- Fields that are "part of" the event (mental rehearsal, scenarios)

**Separate Files** for:
- Large data structures
- Infrequently accessed data
- System-level data (hypotheses, spaced repetition)

### Implementation

**Event Frontmatter (Small Fields):**
```yaml
---
event: 12
week: "01"
date: "2025-12-16"
type: "race"

# Small enhancement fields
mental_rehearsal:
  pre_session: true
  confidence_rating: 4

eye_discipline_rating: 4
---
```

**Separate System Files (Large Structures):**
```
coaching/
├── hypotheses.yaml           # Hypothesis tracking
├── spaced-repetition.yaml    # Spaced repetition schedule
├── race-patterns.yaml        # Aggregated race patterns
└── coaching-context.yaml     # Coaching state
```

### Benefits

✅ **Best of both worlds**: Flexibility + safety  
✅ **Scalable**: Can handle both small and large data  
✅ **Maintainable**: Clear separation of concerns  

---

## Migration Plan

### Phase 1: Foundation (Week 2)

**Goal:** Set up infrastructure without touching existing events.

**Actions:**
1. Create `tools/frontmatter_utils.py` with safe parsing functions
2. Add PyYAML to `pyproject.toml` dependencies
3. Create new system files in `coaching/`:
   - `hypotheses.yaml` (with Week 01 patience hypothesis backfilled)
   - `spaced-repetition.yaml` (with Jefferson track added)
   - `coaching-context.yaml` (initialized with current state)
4. Test frontmatter utilities on dummy files

**Risk:** Zero (no existing files modified)

### Phase 2: New Events Only (Week 2-3)

**Goal:** Start using enhancements with new events.

**Actions:**
1. Modify `tools/templates/event-page.md` to include optional new fields (commented out)
2. Create new enhancement tools (mental_rehearsal.py, scenario_planner.py, etc.)
3. Add Makefile targets for new tools
4. Use new tools with Week 02 events going forward

**Risk:** Zero (only affects new events)

### Phase 3: Selective Backfill (Week 3-4)

**Goal:** Optionally add enhancement data to key past events.

**Actions:**
1. Create `tools/backfill_enhancements.py` to interactively add data to old events
2. Backfill Week 01 official races (Events #12, #13) with:
   - Mental rehearsal data (from memory/notes)
   - Race scenarios (from debriefs)
3. Test that old visualizations still work

**Risk:** Low (limited scope, can be reverted)

### Phase 4: Full Integration (Week 4+)

**Goal:** All new events use full enhancement suite.

**Actions:**
1. Update documentation with new workflows
2. Create visualization tools for enhancement data
3. Integrate enhancement data into coaching prompts
4. Generate weekly enhancement reports

**Risk:** Low (system is proven by this point)

---

## Rollback Strategy

If any issues arise, rollback is simple:

### Rollback Option 1: Ignore New Fields
- Existing tools already ignore new frontmatter fields
- Simply stop using new tools
- New fields remain in files but are harmless

### Rollback Option 2: Remove New Fields
```bash
# Remove all enhancement frontmatter fields
python tools/strip_enhancements.py --dry-run  # Preview changes
python tools/strip_enhancements.py            # Execute removal
```

### Rollback Option 3: Git Revert
```bash
# Revert to pre-enhancement state
git checkout <commit-before-enhancements> -- weeks/
```

---

## Testing Strategy

### Unit Tests

Create `tests/test_frontmatter_utils.py`:

```python
import pytest
from pathlib import Path
from tools.frontmatter_utils import (
    parse_event_file,
    update_event_frontmatter,
    get_frontmatter_field
)

def test_parse_event_with_frontmatter(tmp_path):
    """Test parsing event file with frontmatter."""
    event_file = tmp_path / "test-event.md"
    event_file.write_text("""---
event: 1
week: "01"
date: "2025-12-11"
type: "solo"
---

# Event #1

Some content here.
""")
    
    frontmatter, body = parse_event_file(event_file)
    
    assert frontmatter["event"] == 1
    assert frontmatter["week"] == "01"
    assert "# Event #1" in body

def test_parse_event_without_frontmatter(tmp_path):
    """Test parsing event file without frontmatter."""
    event_file = tmp_path / "test-event.md"
    event_file.write_text("# Event\n\nNo frontmatter here.")
    
    frontmatter, body = parse_event_file(event_file)
    
    assert frontmatter == {}
    assert "# Event" in body

def test_update_frontmatter_merge(tmp_path):
    """Test merging new fields into existing frontmatter."""
    event_file = tmp_path / "test-event.md"
    event_file.write_text("""---
event: 1
week: "01"
---

# Content
""")
    
    update_event_frontmatter(event_file, {
        "mental_rehearsal": {"pre_session": True}
    })
    
    frontmatter, _ = parse_event_file(event_file)
    
    assert frontmatter["event"] == 1  # Preserved
    assert frontmatter["mental_rehearsal"]["pre_session"] == True  # Added

def test_get_nested_field(tmp_path):
    """Test getting nested frontmatter field."""
    event_file = tmp_path / "test-event.md"
    event_file.write_text("""---
mental_rehearsal:
  pre_session: true
  confidence_rating: 4
---

# Content
""")
    
    confidence = get_frontmatter_field(
        event_file,
        "mental_rehearsal.confidence_rating",
        default=3
    )
    
    assert confidence == 4

def test_get_missing_field_returns_default(tmp_path):
    """Test that missing fields return default value."""
    event_file = tmp_path / "test-event.md"
    event_file.write_text("""---
event: 1
---

# Content
""")
    
    value = get_frontmatter_field(
        event_file,
        "mental_rehearsal.pre_session",
        default=False
    )
    
    assert value == False
```

### Integration Tests

```bash
# Test with actual Week 01 files (read-only)
python -m pytest tests/test_integration.py -v

# Test new tool with dummy event
make test-mental-rehearsal WEEK=99 EVENT=99
```

### Validation Script

Create `tools/validate_schema.py`:

```python
"""
Validate that all event files have valid YAML frontmatter.
"""

from pathlib import Path
from frontmatter_utils import parse_event_file

def validate_all_events():
    """Validate all event files in the repository."""
    errors = []
    
    for week_dir in sorted(Path("weeks").glob("week*")):
        for event_file in sorted(week_dir.glob("events/*.md")):
            try:
                frontmatter, body = parse_event_file(event_file)
                
                # Check required fields
                required = ["event", "week", "date", "type"]
                for field in required:
                    if field not in frontmatter:
                        errors.append(f"{event_file}: Missing required field '{field}'")
                
            except Exception as e:
                errors.append(f"{event_file}: {e}")
    
    if errors:
        print("❌ Validation errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ All event files valid!")
        return True

if __name__ == "__main__":
    validate_all_events()
```

---

## Dependency Management

### Add PyYAML to Project

**File: `pyproject.toml`** (add to dependencies)

```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "pyyaml>=6.0",  # NEW: For frontmatter parsing
]
```

**Install:**
```bash
uv sync
```

---

## Documentation Updates

### Update README.md

Add section on new features:

```markdown
## Enhancement Features (Optional)

The system now supports optional enhancement features for advanced learning:

- **Mental Rehearsal Protocol**: Track pre/post-session visualization
- **Hypothesis Testing**: Formalize experiments and track results
- **Spaced Repetition**: Schedule track knowledge reviews
- **Scenario Planning**: Anticipate and review race situations

See [Enhancement Guide](docs/enhancements.md) for details.

These features are completely optional. The core system works perfectly without them.
```

### Create Enhancement Guide

**File: `docs/enhancements.md`**

```markdown
# Enhancement Features Guide

This guide covers optional advanced features that extend the core logging system.

## Philosophy

All enhancements follow these principles:
- **Opt-in**: Use only what you want
- **Backward compatible**: Old events work perfectly
- **Low friction**: Minimal time investment
- **High value**: Measurable impact on learning

## Available Enhancements

1. [Mental Rehearsal Protocol](#mental-rehearsal)
2. [Hypothesis Testing Framework](#hypothesis-testing)
3. [Spaced Repetition System](#spaced-repetition)
4. [Race Scenario Planning](#scenario-planning)

...
```

---

## Conclusion

**Recommended Approach:** Hybrid Strategy with Phased Migration

This approach provides:
- ✅ **Zero risk** to existing workflows
- ✅ **Gradual adoption** at comfortable pace
- ✅ **Easy rollback** if needed
- ✅ **Scalable** for future enhancements
- ✅ **Maintainable** with clear separation of concerns

The key insight is that **the current system doesn't parse frontmatter**, making this integration remarkably safe. We can add sophisticated enhancements without any risk of breaking existing functionality.
