"""Tables: write data as LaTeX (booktabs) tables."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pathlib import Path
from csvtex import create_latex_table, save_latex_table

@dataclass
class PlotData:
    x: tuple[str, np.ndarray]
    y: tuple[str, np.ndarray]
    y_sigma: tuple[str, np.ndarray]

def get_csv_data(file: str | Path) -> list[tuple[str, np.ndarray]]:
    df = pd.read_csv(Path(file))
    return [(c, df[c].to_numpy()) for c in df.columns]

class LatexConverter:
    def __init__(self, build_folder: str | Path):
        self.build_path = Path(build_folder)
        
    def table_from_file(self, input_path: str | Path) -> str:
        input_path = Path(input_path)
        name = input_path.stem  # "data/table.csv" -> "table"
        return create_latex_table(input_path, caption=name, label=f"tab:{name}")

    def save_table_to_file(self, table: str, input_path: str | Path, output_folder: str | Path):
        input_path = Path(input_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        name = input_path.stem
        output_path = output_folder / f"{name}.tex"
        output_path.unlink(missing_ok=True)
        save_latex_table(table, output_path)

    def build_table_from_file(self, input_path: str | Path):
        table = self.table_from_file(Path(input_path))
        self.save_table_to_file(table, Path(input_path), self.build_path)

    def build_tables_from_folder(self, input_folder: str | Path):
        input_path = Path(input_folder)
        csv_files = sorted(input_path.glob("*.csv"))
        for file in csv_files:
            self.build_table_from_file(file)

class EditCsv:
    """Load raw data from a csv file, add computed columns and save as a new csv."""

    def __init__(self, file: str | Path):
        self.df = pd.read_csv(Path(file))

    def _values(self, column: str) -> np.ndarray:
        return self.df[column].to_numpy(dtype=float)

    def add_column(self, name: str, function, *columns: str) -> "EditCsv":
        """New column `name` = function(*columns), e.g. add_column("P [W]", lambda U, I: U * I, "U [V]", "I [A]")."""
        self.df[name] = function(*(self._values(c) for c in columns))
        return self

    def add_uncertainty(self, name: str, function, columns: list[str],
                        sigmas: list[str | float]) -> "EditCsv":
        """New column `name` with the Gaussian error propagation of function(*columns).

        `sigmas` has one entry per column: the name of a sigma column, or a constant
        (e.g. the device accuracy) if the column has no sigma column in the file.
        Partial derivatives are computed numerically.
        """
        values = [self._values(c) for c in columns]
        sigma_values = [self._values(s) if isinstance(s, str) else np.full_like(values[0], s)
                        for s in sigmas]

        variance = np.zeros_like(values[0])
        for i, (value, sigma) in enumerate(zip(values, sigma_values)):
            h = 1e-6 * np.where(value == 0, 1.0, np.abs(value))
            shifted_up = values[:i] + [value + h] + values[i + 1:]
            shifted_down = values[:i] + [value - h] + values[i + 1:]
            derivative = (function(*shifted_up) - function(*shifted_down)) / (2 * h)
            variance += (derivative * sigma) ** 2

        self.df[name] = np.sqrt(variance)
        return self

    def save(self, output_path: str | Path) -> Path:
        """Write the csv (never the raw file: pass a different path)."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(output_path, index=False)
        return output_path

