"""Csv data: reading, editing with documented calculations, LaTeX tables."""

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from csvtex import create_latex_table, save_latex_table

from pemlab.calculation import (
    Calculation,
    calculations_path,
    load_calculations,
    save_calculations,
)
from pemlab.formulas import (
    column_symbol,
    evaluate,
    input_symbols,
    parse_formula,
    propagate_uncertainty,
    rename_symbol,
    split_unit,
    to_latex,
)
from pemlab.latex import calculations_section_to_tex, escape_latex, table_float_to_tex


def _rounded(values, decimals: int | None):
    return values if decimals is None else np.round(values, decimals)


def _distinguish_old_symbol(expression, old_name: str, new_name: str):
    """Display only: if a column keeps its symbol (I [mA] -> I [A]), the old one shows as I_mA."""
    symbol = column_symbol(old_name)
    if symbol != column_symbol(new_name):
        return expression
    unit = split_unit(old_name)[1]
    suffix = re.sub(r"\W", "", unit or "") or "old"
    return rename_symbol(expression, symbol, f"{symbol}_{suffix}")


@dataclass
class PlotData:
    x: tuple[str, np.ndarray]
    y: tuple[str, np.ndarray]
    y_sigma: tuple[str, np.ndarray] | None = None


def get_csv_data(file: str | Path) -> list[tuple[str, np.ndarray]]:
    df = pd.read_csv(Path(file))
    return [(c, df[c].to_numpy()) for c in df.columns]


def table_tex(
    csv_file: str | Path, caption: str, label: str, notes: list[str] | None = None
) -> str:
    """LaTeX table of a csv file with `caption` (LaTeX) and `label`; notes stay in the float."""
    df = pd.read_csv(Path(csv_file), dtype=str, keep_default_na=False)  # keep the written digits
    return table_float_to_tex(list(df.columns), df.values.tolist(), caption, label, notes or [])


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
    """A csv table to which computed columns are added; every calculation is recorded.

    Formulas are strings over the column names without unit, e.g. "U * I" for the
    columns "U [V]" and "I [A]". Calculations are stored next to the saved csv.
    """

    kind = "data"

    def __init__(self, file: str | Path, name: str | None = None):
        file = Path(file)
        self.name = name or file.stem
        self.df = pd.read_csv(file)
        self.calculations = load_calculations(calculations_path(file))

    def __repr__(self) -> str:
        return f"EditCsv({self.name!r}, columns={list(self.df.columns)})"

    def _repr_html_(self) -> str:
        """Notebooks show the table after every step, e.g. after add_column(...)."""
        return self.df._repr_html_()

    def column(self, name: str) -> np.ndarray:
        return self.df[name].to_numpy(dtype=float)

    def add_column(self, name: str, formula: str, decimals: int | None = None) -> "EditCsv":
        """New column from a formula, e.g. add_column("P [W]", "U * I", decimals=3).

        `decimals`: round the values to this many decimal places (None: no rounding).
        """
        expression = parse_formula(formula)
        inputs = self._input_columns(expression)
        values = evaluate(expression, self._input_values(inputs))
        self.df[name] = _rounded(values, decimals)
        self._record(Calculation(name, "column", formula, inputs, {}, to_latex(expression)))
        return self

    def replace_column(
        self, old_name: str, new_name: str, formula: str, decimals: int | None = None
    ) -> "EditCsv":
        """Change a column in place (same position, no new column; the raw csv is untouched).

        E.g. replace_column("I [mA]", "I [A]", "I * 1e-3"): in the formula, I is the old column.
        """
        if old_name not in self.df.columns:
            columns = list(self.df.columns)
            raise ValueError(f"Spalte '{old_name}' gibt es nicht. Vorhanden: {columns}")
        expression = parse_formula(formula)
        inputs = self._input_columns(expression)
        values = _rounded(evaluate(expression, self._input_values(inputs)), decimals)

        position = self.df.columns.get_loc(old_name)
        self.df = self.df.drop(columns=old_name)
        self.df.insert(position, new_name, values)

        shown = _distinguish_old_symbol(expression, old_name, new_name)
        self._record(Calculation(new_name, "column", formula, inputs, {}, to_latex(shown)))
        return self

    def add_uncertainty(
        self,
        name: str,
        formula: str,
        sigmas: dict[str, str | float] | None = None,
        decimals: int | None = None,
    ) -> "EditCsv":
        """New column with the Gaussian error propagation of `formula`.

        The derivatives are computed analytically. The uncertainty of a symbol is taken from
        the column `sigma_<symbol>` unless `sigmas` gives a column name or a constant for it,
        e.g. sigmas={"U": 0.01} for the accuracy of a device.
        `decimals`: round the values to this many decimal places (None: no rounding).
        """
        expression = parse_formula(formula)
        inputs = self._input_columns(expression)
        sigma_sources = {symbol: self._sigma_source(symbol, sigmas or {}) for symbol in inputs}
        propagated = propagate_uncertainty(expression)

        values = self._input_values(inputs)
        values.update(self._sigma_values(sigma_sources))
        self.df[name] = _rounded(evaluate(propagated, values), decimals)
        self._record(
            Calculation(name, "uncertainty", formula, inputs, sigma_sources, to_latex(propagated))
        )
        return self

    def _columns_by_symbol(self) -> dict[str, str]:
        symbols = [column_symbol(column) for column in self.df.columns]
        duplicates = {symbol for symbol in symbols if symbols.count(symbol) > 1}
        if duplicates:
            raise ValueError(f"Mehrere Spalten mit demselben Symbol (ohne Einheit): {duplicates}")
        return dict(zip(symbols, self.df.columns, strict=True))

    def _input_columns(self, expression) -> dict[str, str]:
        by_symbol = self._columns_by_symbol()
        missing = [s for s in input_symbols(expression) if s not in by_symbol]
        if missing:
            known = sorted(by_symbol)
            raise ValueError(f"Keine Spalte für {missing}. Vorhandene Symbole: {known}")
        return {symbol: by_symbol[symbol] for symbol in input_symbols(expression)}

    def _sigma_source(self, symbol: str, given: dict[str, str | float]) -> str | float:
        if symbol in given:
            return given[symbol]
        sigma_column = self._columns_by_symbol().get(f"sigma_{symbol}")
        if sigma_column is None:
            raise ValueError(
                f"Keine Unsicherheit für '{symbol}': Spalte 'sigma_{symbol} [..]' fehlt, "
                f"gib sie mit sigmas={{'{symbol}': Wert oder Spaltenname}} an."
            )
        return sigma_column

    def _input_values(self, inputs: dict[str, str]) -> dict[str, np.ndarray]:
        return {symbol: self.column(column) for symbol, column in inputs.items()}

    def _sigma_values(self, sources: dict[str, str | float]) -> dict[str, np.ndarray | float]:
        return {
            f"sigma_{symbol}": self.column(source) if isinstance(source, str) else source
            for symbol, source in sources.items()
        }

    def _record(self, calculation: Calculation) -> None:
        """Keep one calculation per column (recomputing a column replaces its calculation)."""
        others = [c for c in self.calculations if c.column != calculation.column]
        self.calculations = [*others, calculation]

    def save(self, csv_path: str | Path) -> Path:
        """Write the csv and its calculations (iv.csv + iv.calc.json)."""
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(csv_path, index=False, float_format="%.12g")  # no 0.018000000000000002
        save_calculations(calculations_path(csv_path), self.calculations)
        return csv_path

    def write(self, folder: Path, tex_folder: str) -> None:
        """Called by Project.build(): csv, calculations and a .tex with table and formulas."""
        csv_path = self.save(folder / f"{self.name}.csv")
        notes = [calculations_section_to_tex(self.calculations)]
        tex = table_tex(csv_path, escape_latex(self.name), f"tab:{self.name}", notes)
        (folder / f"{self.name}.tex").write_text(tex, encoding="utf-8")
