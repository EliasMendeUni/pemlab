"""Analysis of csv data: plots and regressions that end up in the build folder."""

from collections.abc import Callable
from pathlib import Path

from pemlab.artifacts import Artifact, PlotArtifact
from pemlab.calculation import collect_calculations
from pemlab.data import EditCsv, PlotData
from pemlab.fit import FitResult, fit_function
from pemlab.formulas import column_symbol, fit_expression_latex, fit_expression_text
from pemlab.latex import (
    calculations_section_to_tex,
    fit_formula_to_tex,
    fit_result_to_tex,
    name_to_tex,
)
from pemlab.plotting import make_data_figure, make_fit_figure, name_to_mathtext


def _used_columns(data: PlotData) -> list[str]:
    columns = [data.x[0], data.y[0]]
    if data.y_sigma is not None:
        columns.append(data.y_sigma[0])
    return columns


def _default_caption(data: PlotData) -> str:
    return f"{name_to_tex(data.y[0])} vs. {name_to_tex(data.x[0])}"


def _fit_section(function, data: PlotData, result: FitResult) -> str:
    x_symbol = column_symbol(data.x[0])
    formula_tex = fit_formula_to_tex(
        data.y[0], fit_expression_latex(function, x_symbol), fit_expression_text(function, x_symbol)
    )
    return fit_result_to_tex(result, formula_tex)


class Analysis:
    """Plots and fits for one csv table (a path or an EditCsv)."""

    def __init__(
        self,
        source: str | Path | EditCsv,
        register: Callable[[Artifact], None] | None = None,
    ):
        self.table = source if isinstance(source, EditCsv) else EditCsv(source)
        self._register = register

    def make_PlotData(self, x: str, y: str, y_sigma: str | None = None) -> PlotData:
        """Select columns by name, e.g. make_PlotData("I [A]", "U [V]", "sigma_U [V]")."""
        sigma = None if y_sigma is None else (y_sigma, self.table.column(y_sigma))
        return PlotData((x, self.table.column(x)), (y, self.table.column(y)), sigma)

    def plot_data(self, name: str, data: PlotData, caption: str | None = None) -> None:
        self._add_plot(name, make_data_figure(data), data, caption, notes=[])

    def regression(
        self, name: str, function, data: PlotData, p0=None, caption: str | None = None
    ) -> FitResult:
        """Fit `function(x, *parameters)` to the data and add the plot with the results."""
        sigma = None if data.y_sigma is None else data.y_sigma[1]
        result = fit_function(function, data.x[1], data.y[1], sigma, p0)
        print(result.summary())

        formula_text = fit_expression_text(function, name_to_mathtext(data.x[0]))
        figure = make_fit_figure(data, function, result, formula_text)
        self._add_plot(name, figure, data, caption, [_fit_section(function, data, result)])
        return result

    def _add_plot(self, name, figure, data: PlotData, caption, notes: list[str]) -> None:
        calculations = collect_calculations(self.table.calculations, _used_columns(data))
        notes = [*notes, calculations_section_to_tex(calculations)]
        artifact = PlotArtifact(name, figure, caption or _default_caption(data), notes)
        if self._register is not None:
            self._register(artifact)
