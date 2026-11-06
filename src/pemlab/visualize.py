"""Visualize: any number of data sets, fits and functions in ONE plot."""

from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from pemlab.artifacts import Artifact
from pemlab.calculation import Calculation
from pemlab.data import PlotData
from pemlab.fit import FitResult
from pemlab.formulas import column_symbol, fit_expression_latex, fit_expression_text
from pemlab.latex import (
    calculations_section_to_tex,
    column_latex,
    figure_float_to_tex,
    fit_formula_to_tex,
    fit_result_to_tex,
    name_to_tex,
)
from pemlab.numberstyle import NumberStyle
from pemlab.plotstyle import FitStyle, LayoutStyle, PointStyle
from pemlab.plotting import (
    CurveLayer,
    PointsLayer,
    fit_label,
    make_figure,
    quantity_to_mathtext,
)


@dataclass
class Regression:
    """A fit of `function(x, *parameters)` to `data`: made by `Analysis.make_regression`."""

    function: Callable
    data: PlotData
    result: FitResult
    numbers: NumberStyle | None = None


@dataclass
class _Entry:
    item: PlotData | Regression | Callable
    points: PointStyle | None
    fit: FitStyle | None
    x_range: tuple[float, float] | None


def _fit_section(regression: Regression, numbers: NumberStyle | None) -> str:
    data, function = regression.data, regression.function
    formula_tex = fit_formula_to_tex(
        data.y[0],
        fit_expression_latex(function, column_latex(data.x[0])),
        fit_expression_text(function, column_symbol(data.x[0])),
    )
    return fit_result_to_tex(regression.result, formula_tex, numbers)


class Visualize:
    """One plot with as many layers as you like, written to the build folder as `name`::

        plot = lab.Visualize("amplitude", layout=LayoutStyle(xscale="log"))
        plot.add(analysis.make_PlotData(f, h), points=PointStyle(label="measured"))
        plot.add(analysis.make_regression(model, other_data))      # points and fit curve
        plot.add(lambda f: 1 / np.sqrt(1 + (f0 / f) ** 2),         # an analytic function
                 fit=FitStyle(label="theory"))

    The layers are drawn in the order they are added; `layout` is the look of the whole plot,
    `points` and `fit` the default looks of the layers (a single `add` can override them).
    Data from several tables can be mixed. Set a `PointStyle(label=...)` for every set of
    points, otherwise they all appear as "Messdaten" in the legend.
    """

    kind = "plots"
    folder = None

    def __init__(
        self,
        name: str,
        caption: str | None = None,
        layout: LayoutStyle | None = None,
        points: PointStyle | None = None,
        fit: FitStyle | None = None,
        numbers: NumberStyle | None = None,
        register: Callable[[Artifact], None] | None = None,
    ):
        self.name = name
        self.caption = caption
        self.layout = layout or LayoutStyle()
        self.points = points
        self.fit = fit
        self.numbers = numbers
        self._entries: list[_Entry] = []
        if register is not None:
            register(self)

    def add(
        self,
        item: PlotData | Regression | Callable,
        points: PointStyle | None = None,
        fit: FitStyle | None = None,
        x: tuple[float, float] | None = None,
    ) -> "Visualize":
        """Add a layer. `item` is

        - `PlotData` (`analysis.make_PlotData(...)`): measured points, with error bars if the
          data has a y uncertainty; looks: `points`;
        - a `Regression` (`analysis.make_regression(...)`): the points of its data and the fit
          curve; looks: `points` and `fit`;
        - a function `f(x)` (e.g. a lambda with numpy): the curve; looks: `fit`, `x` is the range
          (default: the range of all points).
        """
        if not isinstance(item, PlotData | Regression) and not callable(item):
            raise TypeError(
                f"{type(item).__name__} lässt sich nicht plotten: PlotData, Regression oder "
                "eine Funktion erwartet."
            )
        self._entries.append(_Entry(item, points, fit, x))
        return self

    def _first_data(self) -> PlotData:
        for entry in self._entries:
            if isinstance(entry.item, PlotData):
                return entry.item
            if isinstance(entry.item, Regression):
                return entry.item.data
        raise ValueError(f"Plot '{self.name}' hat keine Messreihe (Punkte).")

    def layers(self) -> list[PointsLayer | CurveLayer]:
        layers: list[PointsLayer | CurveLayer] = []
        for entry in self._entries:
            points = entry.points or self.points or PointStyle()
            style = entry.fit or self.fit or FitStyle()
            item = entry.item
            if isinstance(item, PlotData):
                layers.append(PointsLayer(item, points))
            elif isinstance(item, Regression):
                layers.append(PointsLayer(item.data, points))
                label = style.label or fit_label(item.data, item.function, item.result)
                x_values = item.data.x[1]
                layers.append(
                    CurveLayer(
                        lambda xs, r=item: r.function(xs, *r.result.values),
                        style,
                        label,
                        (float(x_values.min()), float(x_values.max())),
                    )
                )
            else:
                data = self._first_data()
                x_name = quantity_to_mathtext(data.x[0])
                label = style.label or (
                    f"{quantity_to_mathtext(data.y[0])} = {fit_expression_text(item, x_name)}"
                )
                layers.append(CurveLayer(item, style, label, entry.x_range))
        return layers

    def figure(self) -> Figure:
        """Draw the plot (a new figure every time)."""
        if not self._entries:
            raise ValueError(f"Plot '{self.name}' ist leer: erst plot.add(...) aufrufen.")
        return make_figure(self.layers(), self.layout)

    def _caption(self) -> str:
        if self.caption is not None:
            return self.caption
        data = [e.item.data if isinstance(e.item, Regression) else e.item for e in self._entries]
        data = [d for d in data if isinstance(d, PlotData)]
        y_names = ", ".join(dict.fromkeys(name_to_tex(d.y[0]) for d in data))
        return f"{y_names} vs. {name_to_tex(data[0].x[0])}"

    def _notes(self) -> list[str]:
        regressions = [e.item for e in self._entries if isinstance(e.item, Regression)]
        notes = [_fit_section(r, r.numbers or self.numbers) for r in regressions]
        calculations: list[Calculation] = []
        for entry in self._entries:
            data = entry.item.data if isinstance(entry.item, Regression) else entry.item
            if isinstance(data, PlotData):
                new = [c for c in data.calculations if all(c is not o for o in calculations)]
                calculations += new
        return [*notes, calculations_section_to_tex(calculations)]

    def write(self, folder: Path, tex_folder: str) -> None:
        """Called by Project.build(): pdf, png and a .tex with figure, fits and calculations."""
        figure = self.figure()
        figure.savefig(folder / f"{self.name}.pdf")
        figure.savefig(folder / f"{self.name}.png", dpi=self.layout.png_dpi)
        plt.close(figure)
        tex = figure_float_to_tex(
            f"{tex_folder}/{self.name}.pdf", self._caption(), f"fig:{self.name}", self._notes()
        )
        (folder / f"{self.name}.tex").write_text(tex, encoding="utf-8")

    def show(self) -> None:
        """Open the plot in a window (a script waits until it is closed)."""
        self.figure()
        plt.show()

    def _repr_png_(self) -> bytes:
        """Notebooks show the plot when it is the last expression of a cell."""
        figure = self.figure()
        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=self.layout.png_dpi // 2)
        plt.close(figure)
        return buffer.getvalue()

    def _preview(self) -> None:
        """In a notebook: show the plot below the cell right away."""
        try:
            from IPython import get_ipython
            from IPython.display import display
        except ImportError:
            return
        if get_ipython() is not None:
            display(self)

    def __repr__(self) -> str:
        return f"Visualize({self.name!r}, {len(self._entries)} layers)"


__all__ = ["Regression", "Visualize"]
