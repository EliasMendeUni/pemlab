"""Csv data: reading, editing with documented calculations, LaTeX tables."""

import keyword
import re
from dataclasses import asdict, dataclass
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
    symbol_latex,
    to_latex,
)
from pemlab.latex import (
    calculations_section_to_tex,
    column_latex,
    escape_latex,
    table_float_to_tex,
)
from pemlab.numberstyle import NumberStyle


def _numbers_dict(numbers: NumberStyle | None) -> dict | None:
    return None if numbers is None else asdict(numbers)


def _distinguish_old_symbol(expression, inputs: dict[str, str], old_name: str, new_name: str):
    """Display only: a variable holding the old column that would look like the new column
    (I for I [mA] -> I [A]) is shown with the old unit as index (I_mA)."""
    left = column_latex(new_name)
    unit = split_unit(old_name)[1]
    suffix = re.sub(r"\W", "", unit or "") or "old"
    for variable, column in inputs.items():
        if column == old_name and symbol_latex(variable) == left:
            expression = rename_symbol(expression, variable, f"{variable}_{suffix}")
    return expression


@dataclass
class PlotData:
    x: tuple[str, np.ndarray]
    y: tuple[str, np.ndarray]
    y_sigma: tuple[str, np.ndarray] | None = None


def get_csv_data(file: str | Path) -> list[tuple[str, np.ndarray]]:
    df = pd.read_csv(Path(file))
    return [(c, df[c].to_numpy()) for c in df.columns]


def _variable_name(column: str) -> str:
    """Python variable name for a column: '$\\sigma_{U_{out}}$ [V]' -> 'sigma_U_out'."""
    name = re.sub(r"\W+", "_", column_symbol(column)).strip("_") or "column"
    if name[0].isdigit():
        name = f"_{name}"
    return f"{name}_" if keyword.iskeyword(name) else name


def _unique_variable_name(column: str, stem: str, used: dict[str, str]) -> str:
    """The plain name if it is free (or already means this column), else a more specific one."""
    name = _variable_name(column)
    unit = re.sub(r"\W+", "", split_unit(column)[1] or "")
    file_part = re.sub(r"\W+", "_", stem)
    candidates = [name, *([f"{name}_{unit}"] if unit else []), f"{name}_{file_part}"]
    for candidate in candidates:
        if used.get(candidate, column) == column:
            return candidate
    counter = 2
    while f"{name}_{counter}" in used:
        counter += 1
    return f"{name}_{counter}"


def _python_string(text: str) -> str:
    """Source code for a string: r"..." if it has backslashes, so it can be copied as it is."""
    if '"' in text or text.endswith("\\"):
        return repr(text)
    return f'r"{text}"' if "\\" in text else f'"{text}"'


def column_variables_to_text(csv_files: list[Path]) -> str:
    """Python assignments with one variable per column, grouped by csv file."""
    used: dict[str, str] = {}  # variable name -> column name
    blocks = []
    for csv_file in csv_files:
        lines = [f"# {csv_file.name}"]
        for column in pd.read_csv(csv_file, nrows=0).columns:
            name = _unique_variable_name(column, csv_file.stem, used)
            used[name] = column
            lines.append(f"{name} = {_python_string(column)}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def table_tex(
    csv_file: str | Path,
    caption: str,
    label: str,
    notes: list[str] | None = None,
    numbers: NumberStyle | None = None,
    column_numbers: dict[str, NumberStyle] | None = None,
    computed: frozenset[str] = frozenset(),
) -> str:
    """LaTeX table of a csv file with `caption` (LaTeX) and `label`; notes stay in the float.

    The numbers are shown as written in the csv unless `numbers` (or the style of a column in
    `column_numbers`) says otherwise; the csv itself is not changed. Computed columns (names in
    `computed`) are shown with `significant_digits` unless they have a style of their own.
    """
    df = pd.read_csv(Path(csv_file), dtype=str, keep_default_na=False)  # keep the written digits
    return table_float_to_tex(
        list(df.columns),
        df.values.tolist(),
        caption,
        label,
        notes or [],
        numbers,
        column_numbers,
        computed,
    )


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

    Formulas are strings with variables, e.g. "U * I". A variable is the name of a column
    without unit and math markup ("U [V]" is U, "$R_x$ [k$\\Omega$]" is R_x). A column with a
    different name is assigned explicitly (U="column name"). Calculations are stored next to the
    saved csv. `numbers` (a NumberStyle) is how the table shows its numbers; the csv keeps the
    full values.
    """

    kind = "data"

    def __init__(
        self, file: str | Path, name: str | None = None, numbers: NumberStyle | None = None
    ):
        file = Path(file)
        self.name = name or file.stem
        self.numbers = numbers
        self.df = pd.read_csv(file)
        self.calculations = load_calculations(calculations_path(file))

    def __repr__(self) -> str:
        return f"EditCsv({self.name!r}, columns={list(self.df.columns)})"

    def _repr_html_(self) -> str:
        """Notebooks show the table after every step, e.g. after add_column(...)."""
        return self.df._repr_html_()

    def column(self, name: str) -> np.ndarray:
        return self.df[name].to_numpy(dtype=float)

    def add_column(
        self,
        name: str,
        formula: str,
        *,
        numbers: NumberStyle | None = None,
        show: bool = False,
        **columns: str,
    ) -> "EditCsv":
        """New column from a formula. The variables are the names of columns:

            add_column("P [W]", "U * I")           # the columns "U [V]" and "I [A]"
            add_column("R [Ohm]", "U / I", U="U in V")   # a column with another name

        `columns` assigns a column to a variable whose name is not the name of a column.
        `numbers`: how this column is shown in the table (the csv keeps all digits).
        `show`: list the calculation under "Calculations" in the report.
        """
        expression = parse_formula(formula)
        inputs = self._bind(expression, columns)
        self.df[name] = evaluate(expression, self._input_values(inputs))
        calculation = Calculation(
            name, "column", formula, inputs, {}, to_latex(expression), show, _numbers_dict(numbers)
        )
        self._record(calculation)
        return self

    def replace_column(
        self,
        old_name: str,
        new_name: str,
        formula: str,
        *,
        numbers: NumberStyle | None = None,
        show: bool = False,
        **columns: str,
    ) -> "EditCsv":
        """Change a column in place (same position, no new column; the raw csv is untouched).

            replace_column("I [mA]", "I [A]", "I * 1e-3")

        The old column is used like any other, so "I" is the old column here.
        `numbers`, `show` and `columns` as in add_column.
        """
        if old_name not in self.df.columns:
            raise ValueError(f"Spalte '{old_name}' gibt es nicht. Vorhanden: {self._known()}")
        expression = parse_formula(formula)
        inputs = self._bind(expression, columns)
        values = evaluate(expression, self._input_values(inputs))

        position = self.df.columns.get_loc(old_name)
        self.df = self.df.drop(columns=old_name)
        self.df.insert(position, new_name, values)

        shown = _distinguish_old_symbol(expression, inputs, old_name, new_name)
        calculation = Calculation(
            new_name, "replacement", formula, inputs, {}, to_latex(shown), show,
            _numbers_dict(numbers),
        )
        self._record(calculation)
        return self

    def add_uncertainty(
        self,
        name: str,
        formula: str,
        sigmas: dict[str, str | float],
        *,
        numbers: NumberStyle | None = None,
        show: bool = False,
        **columns: str,
    ) -> "EditCsv":
        """New column with the Gaussian error propagation of `formula`.

            add_uncertainty("sigma_P [W]", "U * I", {"U": 0.01, "I": "sigma_I [A]"})

        The derivatives are computed analytically. `sigmas` gives the uncertainty of every
        variable: a number (e.g. the accuracy of a device, 0 for an exact quantity) or the name
        of a column. `numbers`, `show` and `columns` as in add_column.
        """
        expression = parse_formula(formula)
        inputs = self._bind(expression, columns)
        sigma_sources = self._bind_sigmas(list(inputs), sigmas)
        propagated = propagate_uncertainty(expression)

        values = self._input_values(inputs)
        values.update(self._sigma_values(sigma_sources))
        self.df[name] = evaluate(propagated, values)
        calculation = Calculation(
            name, "uncertainty", formula, inputs, sigma_sources, to_latex(propagated), show,
            _numbers_dict(numbers),
        )
        self._record(calculation)
        return self

    def _known(self) -> list[str]:
        return list(self.df.columns)

    def _automatic_columns(self, variables: list[str], given: dict[str, str]) -> dict[str, str]:
        """For variables without an assigned column: the column that is named like the variable."""
        by_name: dict[str, list[str]] = {}
        for column in self.df.columns:
            by_name.setdefault(_variable_name(column), []).append(column)
        found = {}
        for variable in variables:
            candidates = by_name.get(variable, []) if variable not in given else []
            if len(candidates) > 1:
                raise ValueError(
                    f"'{variable}' passt zu mehreren Spalten {candidates}. "
                    f'Gib eine davon an, z. B. {variable}="{candidates[0]}".'
                )
            if candidates:
                found[variable] = candidates[0]
        return found

    def _bind(self, expression, columns: dict[str, str]) -> dict[str, str]:
        """Check that the variables of the formula and the given columns fit together."""
        if "decimals" in columns:
            raise ValueError("decimals gibt es nicht mehr: numbers=NumberStyle(decimals=...)")
        variables = input_symbols(expression)
        columns = {**self._automatic_columns(variables, columns), **columns}
        missing = [v for v in variables if v not in columns]
        unused = [v for v in columns if v not in variables]
        unknown = [c for c in columns.values() if c not in self.df.columns]
        if missing:
            example = f'{missing[0]}="<Spaltenname>"'
            raise ValueError(
                f"Zu {missing} gibt es keine Spalte gleichen Namens. Gib sie an, z. B. {example}. "
                f"Vorhanden: {self._known()}"
            )
        if unused:
            raise ValueError(f"{unused} kommt in der Formel nicht vor (Variablen: {variables}).")
        if unknown:
            raise ValueError(f"Spalte(n) {unknown} gibt es nicht. Vorhanden: {self._known()}")
        return {variable: columns[variable] for variable in variables}

    def _bind_sigmas(
        self, variables: list[str], sigmas: dict[str, str | float]
    ) -> dict[str, str | float]:
        """One uncertainty (number or column name) for every variable, nothing more."""
        missing = [v for v in variables if v not in sigmas]
        unused = [v for v in sigmas if v not in variables]
        unknown = [s for s in sigmas.values() if isinstance(s, str) and s not in self.df.columns]
        if missing:
            raise ValueError(f"In sigmas fehlt {missing} (Zahl oder Spalte, 0 wenn exakt).")
        if unused:
            raise ValueError(f"sigmas enthält {unused}, das nicht in der Formel vorkommt.")
        if unknown:
            raise ValueError(f"Spalte(n) {unknown} gibt es nicht. Vorhanden: {self._known()}")
        return {variable: sigmas[variable] for variable in variables}

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
        column_numbers = {
            c.column: NumberStyle(**c.numbers) for c in self.calculations if c.numbers
        }
        computed = frozenset(c.column for c in self.calculations if c.kind != "replacement")
        tex = table_tex(
            csv_path,
            escape_latex(self.name),
            f"tab:{self.name}",
            notes,
            self.numbers,
            column_numbers,
            computed,
        )
        (folder / f"{self.name}.tex").write_text(tex, encoding="utf-8")
