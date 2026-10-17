"""Figures for measurement data and fits (they only create the figure)."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pemlab.data import PlotData
from pemlab.fit import FitResult


def _draw_measurements(ax: Axes, data: PlotData) -> None:
    _, x = data.x
    _, y = data.y
    if data.y_sigma is None:
        ax.plot(x, y, "o", label="Messdaten")
    else:
        ax.errorbar(x, y, yerr=data.y_sigma[1], fmt="o", capsize=3, label="Messdaten")


def _label_axes(ax: Axes, data: PlotData) -> None:
    ax.set_xlabel(data.x[0])
    ax.set_ylabel(data.y[0])
    ax.grid(True)


def make_data_figure(data: PlotData) -> Figure:
    fig, ax = plt.subplots()
    _draw_measurements(ax, data)
    _label_axes(ax, data)
    return fig


def make_fit_figure(data: PlotData, function, result: FitResult, formula_text: str) -> Figure:
    fig, ax = plt.subplots()
    _draw_measurements(ax, data)

    x = data.x[1]
    xs = np.linspace(x.min(), x.max(), 200)
    label = f"Fit: {data.y[0]} = {formula_text}\n{result.parameters_text()}"
    ax.plot(xs, function(xs, *result.values), label=label)

    _label_axes(ax, data)
    ax.legend()
    return fig
