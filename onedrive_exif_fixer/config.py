from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


@dataclass(frozen=True)
class Config:
    """Configuration data for the EXIF fixer.

    Parameters
    ----------
    date_formats
        Ordered list of date formats recognized when parsing EXIF, filenames, and
        folder names.
    """

    date_formats: tuple[str, ...]


def load_config(path: Path) -> Config:
    """Load configuration from a JSON file.

    Parameters
    ----------
    path
        Path to the JSON configuration file.

    Returns
    -------
    Config
        Parsed configuration.
    """

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    date_formats = _parse_date_formats(raw.get("date_formats"))
    return Config(date_formats=date_formats)


def _parse_date_formats(raw_formats: Iterable[str] | None) -> tuple[str, ...]:
    if not raw_formats:
        raise ValueError("Config must include non-empty 'date_formats'.")
    formats = tuple(raw_formats)
    if any(not isinstance(item, str) or not item.strip() for item in formats):
        raise ValueError("All date_formats entries must be non-empty strings.")
    return formats
