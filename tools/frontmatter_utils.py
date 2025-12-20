"""
Frontmatter Utility Module
===========================

Safe utilities for parsing and updating YAML frontmatter in event markdown files.

This module provides robust functions for:
- Parsing frontmatter from markdown files
- Updating frontmatter with new fields (deep merge)
- Writing frontmatter back to files safely
- Retrieving nested fields with dot notation

All functions handle missing frontmatter gracefully and preserve existing content.

Usage:
    from frontmatter_utils import parse_event_file, update_event_frontmatter
    
    # Read frontmatter
    frontmatter, body = parse_event_file(Path("event.md"))
    
    # Update frontmatter
    update_event_frontmatter(Path("event.md"), {
        "mental_rehearsal": {"pre_session": True}
    })

Author: Manus AI
Date: 2025-12-19
License: MIT
"""

import yaml
from pathlib import Path
from typing import Any, Optional
from copy import deepcopy


def parse_event_file(file_path: Path) -> tuple[dict, str]:
    """
    Parse event markdown file into frontmatter dict and body content.
    
    Safely handles files with or without frontmatter. If frontmatter parsing
    fails, returns empty dict and full content.
    
    Args:
        file_path: Path to event markdown file
    
    Returns:
        Tuple of (frontmatter_dict, body_content)
        - frontmatter_dict: Parsed YAML frontmatter as dict (empty if none)
        - body_content: Markdown content after frontmatter
    
    Example:
        >>> frontmatter, body = parse_event_file(Path("event.md"))
        >>> print(frontmatter["event"])
        12
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = file_path.read_text(encoding="utf-8")
    
    # Check if file starts with frontmatter delimiter
    if not content.startswith("---"):
        # No frontmatter, return empty dict and full content
        return {}, content
    
    try:
        # Split on --- delimiters
        # Expected format: ---\nfrontmatter\n---\nbody
        parts = content.split("---", 2)
        
        if len(parts) < 3:
            # Malformed frontmatter, return empty dict and full content
            return {}, content
        
        frontmatter_str = parts[1]
        body = parts[2]
        
        # Parse YAML
        frontmatter = yaml.safe_load(frontmatter_str)
        
        # Handle case where frontmatter is empty or None
        if frontmatter is None:
            frontmatter = {}
        
        return frontmatter, body
    
    except yaml.YAMLError as e:
        print(f"⚠️  Warning: Could not parse YAML frontmatter in {file_path.name}: {e}")
        print(f"   Returning empty frontmatter dict.")
        return {}, content
    
    except Exception as e:
        print(f"⚠️  Warning: Unexpected error parsing {file_path.name}: {e}")
        return {}, content


def update_event_frontmatter(
    file_path: Path,
    updates: dict[str, Any],
    merge: bool = True
) -> None:
    """
    Update event file frontmatter with new fields.
    
    By default, performs a deep merge: existing fields are preserved,
    new fields are added, and nested dicts are merged recursively.
    
    Args:
        file_path: Path to event markdown file
        updates: Dictionary of fields to add/update
        merge: If True (default), merge with existing frontmatter.
               If False, replace frontmatter entirely with updates.
    
    Raises:
        FileNotFoundError: If file doesn't exist
    
    Example:
        >>> update_event_frontmatter(Path("event.md"), {
        ...     "mental_rehearsal": {"pre_session": True, "confidence": 4}
        ... })
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Parse existing file
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
    
    Args:
        file_path: Path to event markdown file
        frontmatter: Dictionary to serialize as YAML frontmatter
        body: Markdown body content
    
    Example:
        >>> write_event_file(
        ...     Path("event.md"),
        ...     {"event": 1, "week": "01"},
        ...     "\\n# Event #1\\n\\nContent here."
        ... )
    """
    # Serialize frontmatter to YAML
    frontmatter_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=80
    )
    
    # Ensure body starts with newline if it doesn't
    if body and not body.startswith("\n"):
        body = "\n" + body
    
    # Construct full content
    content = f"---\n{frontmatter_str}---{body}"
    
    # Write to file
    file_path.write_text(content, encoding="utf-8")


def deep_merge(base: dict, updates: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Updates are merged into base, preserving nested structures.
    For nested dicts, merges recursively. For other types, updates overwrite.
    
    Args:
        base: Base dictionary
        updates: Dictionary with updates to merge in
    
    Returns:
        New dictionary with merged content (does not modify inputs)
    
    Example:
        >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> updates = {"b": {"d": 4, "e": 5}, "f": 6}
        >>> deep_merge(base, updates)
        {'a': 1, 'b': {'c': 2, 'd': 4, 'e': 5}, 'f': 6}
    """
    result = deepcopy(base)
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Overwrite or add new key
            result[key] = deepcopy(value)
    
    return result


def get_frontmatter_field(
    file_path: Path,
    field_path: str,
    default: Any = None
) -> Any:
    """
    Get a specific field from frontmatter using dot notation.
    
    Supports nested field access with dots (e.g., "mental_rehearsal.confidence").
    Returns default value if field doesn't exist at any level.
    
    Args:
        file_path: Path to event file
        field_path: Dot-separated path to field (e.g., "mental_rehearsal.confidence")
        default: Default value if field doesn't exist (default: None)
    
    Returns:
        Field value or default
    
    Example:
        >>> confidence = get_frontmatter_field(
        ...     Path("event.md"),
        ...     "mental_rehearsal.confidence_rating",
        ...     default=3
        ... )
        >>> print(confidence)
        4
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


def validate_event_file(file_path: Path, required_fields: list[str] = None) -> tuple[bool, list[str]]:
    """
    Validate that an event file has valid frontmatter and required fields.
    
    Args:
        file_path: Path to event file
        required_fields: List of required field names (default: ["event", "week", "date", "type"])
    
    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if file is valid, False otherwise
        - error_messages: List of error messages (empty if valid)
    
    Example:
        >>> is_valid, errors = validate_event_file(Path("event.md"))
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
    if required_fields is None:
        required_fields = ["event", "week", "date", "type"]
    
    errors = []
    
    # Check file exists
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]
    
    # Parse frontmatter
    try:
        frontmatter, _ = parse_event_file(file_path)
    except Exception as e:
        return False, [f"Failed to parse file: {e}"]
    
    # Check required fields
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: '{field}'")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def list_event_files(week_dir: Path) -> list[Path]:
    """
    List all event markdown files in a week directory.
    
    Args:
        week_dir: Path to week directory (e.g., weeks/week01)
    
    Returns:
        Sorted list of event file paths
    
    Example:
        >>> events = list_event_files(Path("weeks/week01"))
        >>> for event in events:
        ...     print(event.name)
    """
    events_dir = week_dir / "events"
    
    if not events_dir.exists():
        return []
    
    # Get all .md files, sorted
    return sorted(events_dir.glob("*.md"))


def get_all_frontmatter_fields(file_path: Path) -> set[str]:
    """
    Get all top-level field names from a file's frontmatter.
    
    Useful for discovering what fields are present in a file.
    
    Args:
        file_path: Path to event file
    
    Returns:
        Set of top-level field names
    
    Example:
        >>> fields = get_all_frontmatter_fields(Path("event.md"))
        >>> print(fields)
        {'event', 'week', 'date', 'type', 'mental_rehearsal'}
    """
    frontmatter, _ = parse_event_file(file_path)
    return set(frontmatter.keys())


# Convenience function for common use case
def add_frontmatter_field(
    file_path: Path,
    field_name: str,
    field_value: Any
) -> None:
    """
    Add or update a single top-level frontmatter field.
    
    This is a convenience wrapper around update_event_frontmatter
    for the common case of updating a single field.
    
    Args:
        file_path: Path to event file
        field_name: Name of field to add/update
        field_value: Value to set
    
    Example:
        >>> add_frontmatter_field(
        ...     Path("event.md"),
        ...     "eye_discipline_rating",
        ...     4
        ... )
    """
    update_event_frontmatter(file_path, {field_name: field_value}, merge=True)


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python frontmatter_utils.py <event_file.md>")
        print("  Displays frontmatter from the specified file.")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    try:
        frontmatter, body = parse_event_file(file_path)
        
        print(f"📄 File: {file_path.name}")
        print(f"📊 Frontmatter fields: {len(frontmatter)}")
        print("\nFrontmatter:")
        print(yaml.dump(frontmatter, default_flow_style=False))
        print(f"\nBody length: {len(body)} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
