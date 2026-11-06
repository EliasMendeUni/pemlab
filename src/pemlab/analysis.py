"""Analysis of csv data: plots and regressions that end up in the build folder."""

from collections.abc import Callable
from pathlib import Path

from pemlab.artifacts import Artifact, MeanArtifact
from pemlab.calculation import collect_calculations
from pemlab.data import EditCsv, PlotData
from pemlab.fit import FitResult, fit_function
from pemlab.latex import calculations_section_to_tex, mean_result_to_tex, name_to_tex
from pemlab.numberstyle import NumberStyle
from pemlab.plotstyle import FitStyle, LayoutStyle, PointStyle
from pemlab.stats import MeanResult, mean_of
from pemlab.visualize import Regression, Visualize


def _used_columns(data: PlotData) -> list[str]:
    columns = [data.x[0], data.y[0]]
    if data.y_sigma is not None:
        columns.append(data.y_sigma[0])
    return columns


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
        data = PlotData((x, self.table.column(x)), (y, self.table.column(y)), sigma)
        data.calculations = collect_calculations(self.table.calculations, _used_columns(data))
        return data

    def make_regression(
        self, function, data: PlotData, p0=None, numbers: NumberStyle | None = None
    ) -> Regression:
        """Fit `function(x, *parameters)` to the data; `plot.add(regression)` draws it.

        The result with the parameters and their uncertainties is `regression.result`.
        """
        numbers = numbers or self.numbers
        sigma = None if data.y_sigma is None else data.y_sigma[1]
        result = fit_function(function, data.x[1], data.y[1], sigma, p0)
        print(result.summary(numbers))
        return Regression(function, data, result, numbers)

    def visualize(self, name: str, caption: str | None = None, layout: LayoutStyle | None = None):
        """An empty `Visualize` plot with the styles of this analysis, written by `build()`."""
        return Visualize(
            name, caption, layout or self.layout, self.points, self.fit, self.numbers,
            self._register,
        )

    def plot_data(
        self,
        name: str,
        data: PlotData,
        caption: str | None = None,
        points: PointStyle | None = None,
        layout: LayoutStyle | None = None,
    ) -> Visualize:
        """The measured points as one plot (for several layers in one plot use `visualize`)."""
        return self.visualize(name, caption, layout).add(data, points=points)

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
        regression = self.make_regression(function, data, p0, numbers)
        plot = self.visualize(name, caption, layout).add(regression, points=points, fit=fit)
        plot._preview()
        return regression.result

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

    def _publish(self, artifact: Artifact) -> None:
        if self._register is not None:
            self._register(artifact)
