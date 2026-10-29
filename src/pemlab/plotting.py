"""Figures for measurement data and fits (they only create the figure)."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pemlab.data import PlotData
from pemlab.fit import FitResult
from pemlab.formulas import normalize_unit, split_unit
from pemlab.plotstyle import FitStyle, LayoutStyle, PointStyle


def _draw_measurements(ax: Axes, data: PlotData, points: PointStyle) -> None:
    _, x = data.x
    _, y = data.y
    options = {
        "marker": points.marker,
        "markersize": points.marker_size,
        "color": points.marker_color,
        "alpha": points.marker_alpha,
        "linestyle": "-" if points.connect_points else "none",
        "label": points.label,
    }
    if data.y_sigma is None:
        ax.plot(x, y, **options)
    else:
        ax.errorbar(
            x,
            y,
            yerr=data.y_sigma[1],
            capsize=points.capsize,
            elinewidth=points.errorbar_linewidth,
            **options,
        )


def _mathtext(text: str) -> str:
    """'\\Omega' (without dollar signs) becomes math text; '$R_i$' is already math."""
    return f"${text}$" if "\\" in text and "$" not in text else text


def name_to_mathtext(name: str) -> str:
    """Column name as matplotlib label: '$R_i$ [\\Omega]' renders as R_i [Ω]."""
    base, unit = split_unit(name)
    if unit is None:
        return _mathtext(base)
    return f"{_mathtext(base)} [{_mathtext(normalize_unit(unit))}]"


def quantity_to_mathtext(name: str) -> str:
    """Column name without unit as matplotlib text: '$R_i$ [\\Omega]' -> '$R_i$'."""
    return _mathtext(split_unit(name)[0])


def _label_axes(ax: Axes, data: PlotData, layout: LayoutStyle) -> None:
    ax.set_xlabel(layout.xlabel if layout.xlabel is not None else name_to_mathtext(data.x[0]))
    ax.set_ylabel(layout.ylabel if layout.ylabel is not None else name_to_mathtext(data.y[0]))
    if layout.title is not None:
        ax.set_title(layout.title)
    ax.set_xscale(layout.xscale)
    ax.set_yscale(layout.yscale)
    if layout.xlim is not None:
        ax.set_xlim(layout.xlim)
    if layout.ylim is not None:
        ax.set_ylim(layout.ylim)
    ax.grid(layout.grid)


def _font_context(layout: LayoutStyle):
    """All text created inside this context gets the font size of the layout."""
    return plt.rc_context({} if layout.font_size is None else {"font.size": layout.font_size})


def _add_legend(ax: Axes, layout: LayoutStyle, default: bool) -> None:
    if layout.legend if layout.legend is not None else default:
        ax.legend(loc=layout.legend_loc)


def make_data_figure(
    data: PlotData,
    points: PointStyle | None = None,
    layout: LayoutStyle | None = None,
) -> Figure:
    points, layout = points or PointStyle(), layout or LayoutStyle()
    with _font_context(layout):
        fig, ax = plt.subplots(figsize=layout.figsize, layout="constrained")
        _draw_measurements(ax, data, points)
        _label_axes(ax, data, layout)
        _add_legend(ax, layout, default=False)
    return fig


def make_fit_figure(
    data: PlotData,
    function,
    result: FitResult,
    formula_text: str,
    points: PointStyle | None = None,
    fit: FitStyle | None = None,
    layout: LayoutStyle | None = None,
) -> Figure:
    points, fit, layout = points or PointStyle(), fit or FitStyle(), layout or LayoutStyle()
    with _font_context(layout):
        fig, ax = plt.subplots(figsize=layout.figsize, layout="constrained")
        _draw_measurements(ax, data, points)

        x = data.x[1]
        xs = np.linspace(x.min(), x.max(), fit.points)
        label = fit.label
        if label is None:
            label = (
                f"Fit: {quantity_to_mathtext(data.y[0])} = {formula_text}\n"
                f"{result.parameters_text()}"
            )
        ax.plot(
            xs,
            function(xs, *result.values),
            color=fit.color,
            linewidth=fit.linewidth,
            linestyle=fit.linestyle,
            label=label,
        )

        _label_axes(ax, data, layout)
        _add_legend(ax, layout, default=True)
    return fig
