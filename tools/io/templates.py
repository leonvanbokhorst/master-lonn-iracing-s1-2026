"""Template loading utilities for CLI tools."""

from pathlib import Path


_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def load_template(name: str, default: str | None = None) -> str:
    """Return template contents, falling back to provided default."""
    template_path = _TEMPLATES_DIR / name
    if template_path.exists():
        return template_path.read_text()
    if default is None:
        raise FileNotFoundError(f"Template {name} not found in {_TEMPLATES_DIR}")
    return default
