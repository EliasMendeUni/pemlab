"""Analysis of csv data: plots and regressions that end up in the build folder."""

from collections.abc import Callable
from pathlib import Path

from pemlab.artifacts import Artifact, MeanArtifact, PlotArtifact
from pemlab.calculation import collect_calculations
from pemlab.data import EditCsv, PlotData
from pemlab.fit import FitResult, fit_function
from pemlab.formulas import column_symbol, fit_expression_latex, fit_expression_text
from pemlab.latex import (
    calculations_section_to_tex,
    column_latex,
    fit_formula_to_tex,
    fit_result_to_tex,
    mean_result_to_tex,
    name_to_tex,
)
from pemlab.numberstyle import NumberStyle
from pemlab.plotstyle import FitStyle, LayoutStyle, PointStyle
from pemlab.plotting import make_data_figure, make_fit_figure, quantity_to_mathtext
from pemlab.stats import MeanResult, mean_of


def _used_columns(data: PlotData) -> list[str]:
    columns = [data.x[0], data.y[0]]
    if data.y_sigma is not None:
        columns.append(data.y_sigma[0])
    return columns


def _default_caption(data: PlotData) -> str:
    return f"{name_to_tex(data.y[0])} vs. {name_to_tex(data.x[0])}"


def _fit_section(function, data: PlotData, result: FitResult, numbers: NumberStyle | None) -> str:
    formula_tex = fit_formula_to_tex(
        data.y[0],
        fit_expression_latex(function, column_latex(data.x[0])),
        fit_expression_text(function, column_symbol(data.x[0])),
    )
    return fit_result_to_tex(result, formula_tex, numbers)


class Analysis:
    """Plots and fits for one csv table (a path or an EditCsv).

    `points`, `fit` and `layout` are the looks of all plots of this analysis (see `PointStyle`,
    `FitStyle`, `LayoutStyle`); the same arguments of a single plot override them one by one.
    What is not given anywhere uses the defaults of the style classes. `numbers` (a `NumberStyle`)
    is how fit results and means are rounded and written.
    """

    def __init__(
        self,
        source: str | Path | EditCsv,
        register: Callable[[Artifact], None] | None = None,
        points: PointStyle | None = None,
        fit: FitStyle | None = None,
        layout: LayoutStyle | None = None,
        numbers: NumberStyle | None = None,
    ):
        self.table = source if isinstance(source, EditCsv) else EditCsv(source)
        self._register = register
        self.numbers = numbers
        self.points = points
        self.fit = fit
        self.layout = layout

    def make_PlotData(self, x: str, y: str, y_sigma: str | None = None) -> PlotData:
        """Select columns by name, e.g. make_PlotData("I [A]", "U [V]", "sigma_U [V]")."""
        sigma = None if y_sigma is None else (y_sigma, self.table.column(y_sigma))
        return PlotData((x, self.table.column(x)), (y, self.table.column(y)), sigma)

    def plot_data(
        self,
        name: str,
        data: PlotData,
        caption: str | None = None,
        points: PointStyle | None = None,
        layout: LayoutStyle | None = None,
    ) -> None:
        points, layout = points or self.points, layout or self.layout
        figure = make_data_figure(data, points, layout)
        self._add_plot(name, figure, data, caption, [], layout)

    def regression(
        self,
        name: str,
        function,
        data: PlotData,
        p0=None,
        caption: str | None = None,
        points: PointStyle | None = None,
        fit: FitStyle | None = None,
        layout: LayoutStyle | None = None,
        numbers: NumberStyle | None = None,
    ) -> FitResult:
        """Fit `function(x, *parameters)` to the data and add the plot with the results."""
        points, fit = points or self.points, fit or self.fit
        layout, numbers = layout or self.layout, numbers or self.numbers
        sigma = None if data.y_sigma is None else data.y_sigma[1]
        result = fit_function(function, data.x[1], data.y[1], sigma, p0)
        print(result.summary(numbers))

        formula_text = fit_expression_text(function, quantity_to_mathtext(data.x[0]))
        figure = make_fit_figure(data, function, result, formula_text, points, fit, layout)
        notes = [_fit_section(function, data, result, numbers)]
        self._add_plot(name, figure, data, caption, notes, layout)
        return result

    def mean(
        self,
        name: str,
        column: str,
        sigma: str | None = None,
        reference: float | None = None,
        caption: str | None = None,
        numbers: NumberStyle | None = None,
    ) -> MeanResult:
        """Mean of a column with standard deviation and uncertainty of the mean.

        Without `sigma` this is the arithmetic mean with the standard error s/sqrt(n). With
        `sigma` (a column of uncertainties) it is the weighted mean with chi-squared per degree
        of freedom. `reference` (e.g. a literature value) adds the deviation from it.
        The result is also written to the build folder as a table.
        """
        numbers = numbers or self.numbers
        values = self.table.column(column)
        sigmas = None if sigma is None else self.table.column(sigma)
        result = mean_of(values, sigmas, reference)
        print(result.summary(numbers))

        used = [column] if sigma is None else [column, sigma]
        calculations = collect_calculations(self.table.calculations, used)
        notes = [calculations_section_to_tex(calculations)]
        caption = caption or f"Mean of {name_to_tex(column)}"
        tex = mean_result_to_tex(result, column, caption, f"tab:mean_{name}", notes, numbers)
        self._publish(MeanArtifact(name, tex))
        return result

    def _add_plot(
        self, name, figure, data: PlotData, caption, notes: list[str], layout: LayoutStyle | None
    ) -> None:
        calculations = collect_calculations(self.table.calculations, _used_columns(data))
        notes = [*notes, calculations_section_to_tex(calculations)]
        caption = caption or _default_caption(data)
        self._publish(PlotArtifact(name, figure, caption, notes, (layout or LayoutStyle()).png_dpi))

    def _publish(self, artifact: Artifact) -> None:
        if self._register is not None:
            self._register(artifact)
