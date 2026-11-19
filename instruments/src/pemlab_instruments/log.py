"""A table of measured values that is saved as csv file for lab.edit_csv(...)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pemlab_instruments.files import timestamped_path


class MeasurementLog:
    """Rows of measured values. Column names as everywhere in pemlab: "U [V]", "I [mA]"."""

    def __init__(self, *columns: str):
        if not columns:
            raise ValueError("Mindestens ein Spaltenname nötig, z. B. MeasurementLog('U [V]').")
        self.columns = list(columns)
        self.rows: list[tuple[float, ...]] = []

    @classmethod
    def from_arrays(cls, columns: list[str], *arrays: np.ndarray) -> MeasurementLog:
        """A log from whole columns, e.g. a scope trace: from_arrays(["t [s]", "U [V]"], t, u)."""
        log = cls(*columns)
        for row in zip(*arrays):
            log.add(*row)
        return log

    def add(self, *values: float) -> None:
        """Add one row, one value per column."""
        if len(values) != len(self.columns):
            raise ValueError(f"{len(values)} Werte für die Spalten {self.columns}")
        self.rows.append(tuple(float(value) for value in values))

    def to_arrays(self) -> dict[str, np.ndarray]:
        """The columns as arrays: {"U [V]": array([...]), ...}."""
        data = np.array(self.rows, dtype=float).reshape(len(self.rows), len(self.columns))
        return {column: data[:, i] for i, column in enumerate(self.columns)}

    def save(self, path: str | Path, timestamp: bool = True) -> Path:
        """Write the csv file (the folder is created if needed) and return its real path.

        With `timestamp=True` (default) date and time are part of the file name,
        `data/hp.csv` is saved as `data/hp_2026-11-10_14-30-05.csv`, so repeating a measurement
        never overwrites the earlier file. `timestamp=False` uses the name as it is.
        """
        path = timestamped_path(path) if timestamp else Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [",".join(self.columns)]
        lines += [",".join(format(value, ".12g") for value in row) for row in self.rows]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def __len__(self) -> int:
        return len(self.rows)

    def __repr__(self) -> str:
        return f"MeasurementLog({self.columns}, {len(self)} rows)"
