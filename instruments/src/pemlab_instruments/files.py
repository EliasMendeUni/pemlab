"""File names with date and time, so a new measurement never overwrites an earlier one."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def timestamped_path(path: str | Path, when: datetime | None = None) -> Path:
    """Put the date and time before the suffix: `data/hp.csv` -> `data/hp_2026-11-10_14-30-05.csv`.

    A file that exists already is never reused: the name gets a counter (`..._2`, `..._3`),
    e.g. for two measurements within the same second. `when` is the time to use (default: now).
    """
    path = Path(path)
    stamp = (when or datetime.now()).strftime(TIME_FORMAT)
    candidate = path.with_name(f"{path.stem}_{stamp}{path.suffix}")
    counter = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_{stamp}_{counter}{path.suffix}")
        counter += 1
    return candidate
