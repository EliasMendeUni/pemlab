"""Figures for measurement data and fits (they only create the figure)."""

from collections.abc import Callable
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pemlab.data import PlotData
from pemlab.fit import FitResult
from pemlab.formulas import fit_expression_text, normalize_unit, split_unit
from pemlab.plotstyle import FitStyle, LayoutStyle, PointStyle


@dataclass
class PointsLayer:
    """Measured points (with error bars if the data has a y uncertainty)."""

    data: PlotData
    points: PointStyle


@dataclass
class CurveLayer:
    """A curve y(x): a fit or an analytic function. `x_range` None: the range of all points."""

    function: Callable[[np.ndarray], np.ndarray]
    style: FitStyle
    label: str | None
    x_range: tuple[float, float] | None = None


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


def _draw_curve(ax: Axes, layer: CurveLayer, x_range: tuple[float, float], log: bool) -> None:
    low, high = layer.x_range or x_range
    space = np.geomspace if log and low > 0 else np.linspace
    xs = space(low, high, layer.style.points)
    ax.plot(
        xs,
        np.broadcast_to(layer.function(xs), xs.shape),  # a constant is a horizontal line
        color=layer.style.color,
        linewidth=layer.style.linewidth,
        linestyle=layer.style.linestyle,
        label=layer.label,
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


def _label_axes(ax: Axes, x_label: str, y_label: str, layout: LayoutStyle) -> None:
    """Axis labels (the layout overrides the given default texts), scales, limits and grid."""
    ax.set_xlabel(layout.xlabel if layout.xlabel is not None else x_label)
    ax.set_ylabel(layout.ylabel if layout.ylabel is not None else y_label)
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


def fit_label(data: PlotData, function, result: FitResult) -> str:
    """Legend text of a fit: formula and the fitted parameters."""
    formula_text = fit_expression_text(function, quantity_to_mathtext(data.x[0]))
    return f"Fit: {quantity_to_mathtext(data.y[0])} = {formula_text}\n{result.parameters_text()}"


def make_figure(
    layers: list[PointsLayer | CurveLayer], layout: LayoutStyle | None = None
) -> Figure:
    """One figure with all layers in the order given (colors follow matplotlib's color cycle).

    Axis names come from the first points layer, the y names of all of them are joined.
    The legend is shown by default if there is a curve or more than one set of points.
    """
    layout = layout or LayoutStyle()
    point_layers = [layer for layer in layers if isinstance(layer, PointsLayer)]
    if not point_layers:
        raise ValueError("Ein Plot braucht mindestens eine Messreihe (Punkte).")
    x_name = point_layers[0].data.x[0]
    y_names = list(dict.fromkeys(layer.data.y[0] for layer in point_layers))
    x_all = np.concatenate([layer.data.x[1] for layer in point_layers])
    x_range = (float(x_all.min()), float(x_all.max()))
    has_curve = len(point_layers) < len(layers)

    with _font_context(layout):
        fig, ax = plt.subplots(figsize=layout.figsize, layout="constrained")
        for layer in layers:
            if isinstance(layer, PointsLayer):
                _draw_measurements(ax, layer.data, layer.points)
            else:
                _draw_curve(ax, layer, x_range, layout.xscale == "log")
        y_label = ", ".join(name_to_mathtext(name) for name in y_names)
        _label_axes(ax, name_to_mathtext(x_name), y_label, layout)
        _add_legend(ax, layout, default=has_curve or len(point_layers) > 1)
    return fig


def make_data_figure(
    data: PlotData,
    points: PointStyle | None = None,
    layout: LayoutStyle | None = None,
) -> Figure:
    return make_figure([PointsLayer(data, points or PointStyle())], layout)


def make_fit_figure(
    data: PlotData,
    function,
    result: FitResult,
    formula_text: str,
    points: PointStyle | None = None,
    fit: FitStyle | None = None,
    layout: LayoutStyle | None = None,
) -> Figure:
    fit = fit or FitStyle()
    label = fit.label
    if label is None:
        label = (
            f"Fit: {quantity_to_mathtext(data.y[0])} = {formula_text}\n{result.parameters_text()}"
        )
    x = data.x[1]
    layers = [
        PointsLayer(data, points or PointStyle()),
        CurveLayer(
            lambda xs: function(xs, *result.values), fit, label, (float(x.min()), float(x.max()))
        ),
    ]
    return make_figure(layers, layout)
