"""A table of measured values that is saved as csv file for lab.edit_csv(...)."""

from pathlib import Path

import numpy as np
import pandas as pd


class MeasurementLog:
    """Rows of measured values. Column names as everywhere in pemlab: "U [V]", "I [mA]"."""

    def __init__(self, *columns: str):
        if not columns:
            raise ValueError("Mindestens ein Spaltenname nötig, z. B. MeasurementLog('U [V]').")
        self.columns = list(columns)
        self.rows: list[tuple[float, ...]] = []

    @classmethod
    def from_arrays(cls, columns: list[str], *arrays: np.ndarray) -> "MeasurementLog":
        """A log from whole columns, e.g. a scope trace: from_arrays(["t [s]", "U [V]"], t, u)."""
        log = cls(*columns)
        for row in zip(*arrays, strict=True):
            log.add(*row)
        return log

    def add(self, *values: float) -> None:
        """Add one row, one value per column."""
        if len(values) != len(self.columns):
            raise ValueError(f"{len(values)} Werte für die Spalten {self.columns}")
        self.rows.append(tuple(float(value) for value in values))

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=self.columns)

    def save(self, path: str | Path) -> Path:
        """Write the csv file (the folder is created if needed) and return its path."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(path, index=False, float_format="%.12g")
        return path

    def __len__(self) -> int:
        return len(self.rows)

    def __repr__(self) -> str:
        return f"MeasurementLog({self.columns}, {len(self)} rows)"
