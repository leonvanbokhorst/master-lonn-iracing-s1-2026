"""
Configuration loader for iRacing telemetry tools.

Uses config.toml in the project root. Falls back to defaults if not found.
"""

import tomllib
from pathlib import Path
from dataclasses import dataclass, fields
from typing import Optional, Any, Type, TypeVar
from collections.abc import Mapping

T = TypeVar("T")

# Find config.toml relative to this file
CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


@dataclass
class PedalsConfig:
    throttle_on: float = 0.05
    throttle_full: float = 0.95
    brake_on: float = 0.01


@dataclass
class OverlapConfig:
    throttle_min: float = 0.02
    min_duration_sec: float = 0.4


@dataclass
class LapsConfig:
    min_time: float = 48.0
    max_time: float = 90.0
    exclude_first_lap: bool = True


@dataclass
class VisualizationConfig:
    dpi: int = 150
    trace_alpha: float = 0.65


@dataclass
class TelemetryConfig:
    sample_rate: int = 60


@dataclass
class Config:
    telemetry: TelemetryConfig
    pedals: PedalsConfig
    overlap: OverlapConfig
    laps: LapsConfig
    visualization: VisualizationConfig


# Shared color constants for consistent styling
COLORS = {
    'first': '#E94F37',    # Red
    'best': '#1B998B',     # Teal
    'latest': '#F6AE2D',   # Yellow/Gold
    'muted': '#D1D5DB',    # Gray (non-journey events)
    'throttle': '#1B998B',
    'brake': '#E94F37',
    'coasting': '#94A3B8',
}


def _build_section(cls: Type[T], raw: Mapping[str, Any] | None) -> T:
    """Filter a raw config mapping down to fields defined on the dataclass.
    
    Ignores unknown/misspelled keys to avoid TypeError on config changes.
    """
    if not isinstance(raw, Mapping):
        raw_dict: dict[str, Any] = {}
    else:
        raw_dict = dict(raw)
    
    allowed_keys = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in raw_dict.items() if k in allowed_keys}
    return cls(**filtered)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from TOML file."""
    path = config_path or CONFIG_PATH
    
    if path.exists():
        with open(path, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}
    
    return Config(
        telemetry=_build_section(TelemetryConfig, data.get("telemetry")),
        pedals=_build_section(PedalsConfig, data.get("pedals")),
        overlap=_build_section(OverlapConfig, data.get("overlap")),
        laps=_build_section(LapsConfig, data.get("laps")),
        visualization=_build_section(VisualizationConfig, data.get("visualization")),
    )


# Singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the singleton config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


# Convenience accessors
def pedals() -> PedalsConfig:
    return get_config().pedals


def overlap() -> OverlapConfig:
    return get_config().overlap


def laps() -> LapsConfig:
    return get_config().laps


def visualization() -> VisualizationConfig:
    return get_config().visualization


def telemetry() -> TelemetryConfig:
    return get_config().telemetry

