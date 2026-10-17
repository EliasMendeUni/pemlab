"""Calculations behind computed csv columns, stored as json next to the csv."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Calculation:
    """How one csv column was computed."""

    column: str
    kind: str  # "column" or "uncertainty"
    formula: str  # formula as written by the user
    inputs: dict[str, str]  # symbol -> column used as input
    sigmas: dict[str, str | float]  # uncertainty only: symbol -> sigma column or constant
    latex: str  # expression that computes the column, as LaTeX

    @property
    def dependencies(self) -> list[str]:
        sigma_columns = [s for s in self.sigmas.values() if isinstance(s, str)]
        return [*self.inputs.values(), *sigma_columns]


def calculations_path(csv_path: str | Path) -> Path:
    """'iv.csv' -> 'iv.calc.json'"""
    return Path(csv_path).with_suffix(".calc.json")


def save_calculations(path: str | Path, calculations: list[Calculation]) -> None:
    data = [asdict(c) for c in calculations]
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_calculations(path: str | Path) -> list[Calculation]:
    """Empty list if there is no calculation file (raw data)."""
    path = Path(path)
    if not path.exists():
        return []
    return [Calculation(**entry) for entry in json.loads(path.read_text(encoding="utf-8"))]


def collect_calculations(calculations: list[Calculation], columns: list[str]) -> list[Calculation]:
    """Calculations that produced `columns`, including their inputs, dependencies first."""
    by_column = {c.column: c for c in calculations}
    ordered: list[Calculation] = []

    def visit(column: str) -> None:
        calculation = by_column.get(column)
        if calculation is None or calculation in ordered:
            return
        for dependency in calculation.dependencies:
            visit(dependency)
        ordered.append(calculation)

    for column in columns:
        visit(column)
    return ordered
