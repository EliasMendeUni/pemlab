"""A plot that is updated while the measurement runs."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Callable, Union

import matplotlib.pyplot as plt

from pemlab.instruments.sweep import Sweep
from pemlab.plotstyle import LayoutStyle, PointStyle
from pemlab.plotting import _font_context, name_to_mathtext

Quantity = Union[str, Callable[[dict], float]]


class LivePlot:
    """Points of a sweep, drawn after every `sweep.add(...)`.

    `x` and `y` are a column name or a function of the row (a dict of column name -> value), e.g.
    `y=lambda r: r["U_a [V]"] / r["U_e [V]"]`. For a function give the axis label in `layout`.
    Styles are the same as for the final plots. Needs an interactive matplotlib backend.

        plot = LivePlot(sweep, x="f [Hz]", y="U_a [V]", layout=LayoutStyle(xscale="log"))
        ...
        plot.show()   # after the measurement: keep the window open
    """

    def __init__(
        self,
        sweep: Sweep,
        x: Quantity,
        y: Quantity,
        points: PointStyle | None = None,
        layout: LayoutStyle | None = None,
    ):
        points = points or PointStyle(connect_points=True)
        self.layout = layout or LayoutStyle()
        self.sweep, self.x, self.y = sweep, x, y

        plt.ion()
        with _font_context(self.layout):
            self.fig, self.ax = plt.subplots(figsize=self.layout.figsize, layout="constrained")
            (self.line,) = self.ax.plot(
                [],
                [],
                marker=points.marker,
                markersize=points.marker_size,
                color=points.marker_color,
                alpha=points.marker_alpha,
                linestyle="-" if points.connect_points else "none",
                label=points.label,
            )
            self.ax.set_xlabel(self._label(self.layout.xlabel, x))
            self.ax.set_ylabel(self._label(self.layout.ylabel, y))
            if self.layout.title is not None:
                self.ax.set_title(self.layout.title)
            self.ax.set_xscale(self.layout.xscale)
            self.ax.set_yscale(self.layout.yscale)
            if self.layout.xlim is not None:
                self.ax.set_xlim(self.layout.xlim)
            if self.layout.ylim is not None:
                self.ax.set_ylim(self.layout.ylim)
            self.ax.grid(self.layout.grid)
            if self.layout.legend:
                self.ax.legend(loc=self.layout.legend_loc)

        sweep.on_row(self.update)
        sweep._live.append(self)
        with warnings.catch_warnings():  # a non-interactive backend (notebook, tests) just skips
            warnings.simplefilter("ignore", UserWarning)
            self.fig.show()

    @staticmethod
    def _label(given: str | None, quantity: Quantity) -> str:
        if given is not None:
            return given
        return name_to_mathtext(quantity) if isinstance(quantity, str) else ""

    @staticmethod
    def _value(quantity: Quantity, row: dict) -> float:
        return row[quantity] if isinstance(quantity, str) else quantity(row)

    def update(self, sweep: Sweep | None = None) -> None:
        """Redraw with all rows so far (called automatically after every `add`)."""
        rows = self.sweep.rows_as_dicts()
        self.line.set_data(
            [self._value(self.x, r) for r in rows], [self._value(self.y, r) for r in rows]
        )
        self.ax.relim()
        self.ax.autoscale_view()
        plt.pause(0.001)  # draws and lets the window handle its events

    def save(self, path: str | Path) -> Path:
        """Save the current state of the plot (pdf, png, ...)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=self.layout.png_dpi)
        return path

    def show(self) -> None:
        """Keep the window open until it is closed."""
        plt.ioff()
        plt.show()
