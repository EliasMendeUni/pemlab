"""A plot that is updated while the measurement runs."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

import matplotlib.pyplot as plt

from pemlab_instruments.sweep import Sweep

Quantity = Union[str, Callable[[dict], float]]


@dataclass(frozen=True)
class LiveStyle:
    """Look of a `LivePlot`. Every field has a default, name only what you want to change."""

    marker: str = "o"
    marker_size: float = 3.0
    color: Optional[str] = None  # None: the color cycle of matplotlib
    connect: bool = True  # draw a line between the points
    label: Optional[str] = None  # legend text; None: no legend
    figsize: Tuple[float, float] = (6.0, 4.0)  # inches
    xlabel: Optional[str] = None  # None: name of the column
    ylabel: Optional[str] = None
    title: Optional[str] = None
    xscale: str = "linear"  # "linear", "log", ...
    yscale: str = "linear"
    xlim: Optional[Tuple[float, float]] = None
    ylim: Optional[Tuple[float, float]] = None
    grid: bool = True
    font_size: Optional[float] = None  # None: matplotlib default
    dpi: int = 200  # resolution of `LivePlot.save` for png files


class LivePlot:
    """Points of a sweep, drawn after every `sweep.add(...)`.

    `x` and `y` are a column name or a function of the row (a dict of column name -> value), e.g.
    `y=lambda r: r["U_a [V]"] / r["U_e [V]"]`. For a function give the axis label in `style`.
    Needs an interactive matplotlib backend.

        plot = LivePlot(sweep, x="f [Hz]", y="U_a [V]", style=LiveStyle(xscale="log"))
        ...
        plot.show()   # after the measurement: keep the window open
    """

    def __init__(self, sweep: Sweep, x: Quantity, y: Quantity, style: Optional[LiveStyle] = None):
        self.style = style or LiveStyle()
        style = self.style
        self.sweep, self.x, self.y = sweep, x, y

        plt.ion()
        font = {} if style.font_size is None else {"font.size": style.font_size}
        with plt.rc_context(font):
            self.fig, self.ax = plt.subplots(figsize=style.figsize, layout="constrained")
            (self.line,) = self.ax.plot(
                [],
                [],
                marker=style.marker,
                markersize=style.marker_size,
                color=style.color,
                linestyle="-" if style.connect else "none",
                label=style.label,
            )
            self.ax.set_xlabel(self._label(style.xlabel, x))
            self.ax.set_ylabel(self._label(style.ylabel, y))
            if style.title is not None:
                self.ax.set_title(style.title)
            self.ax.set_xscale(style.xscale)
            self.ax.set_yscale(style.yscale)
            if style.xlim is not None:
                self.ax.set_xlim(style.xlim)
            if style.ylim is not None:
                self.ax.set_ylim(style.ylim)
            self.ax.grid(style.grid)
            if style.label is not None:
                self.ax.legend()

        sweep.on_row(self.update)
        sweep._live.append(self)
        with warnings.catch_warnings():  # a non-interactive backend (notebook, tests) just skips
            warnings.simplefilter("ignore", UserWarning)
            self.fig.show()

    @staticmethod
    def _label(given: Optional[str], quantity: Quantity) -> str:
        if given is not None:
            return given
        return quantity if isinstance(quantity, str) else ""

    @staticmethod
    def _value(quantity: Quantity, row: dict) -> float:
        return row[quantity] if isinstance(quantity, str) else quantity(row)

    def update(self, sweep: Optional[Sweep] = None) -> None:
        """Redraw with all rows so far (called automatically after every `add`)."""
        rows = self.sweep.rows_as_dicts()
        self.line.set_data(
            [self._value(self.x, r) for r in rows], [self._value(self.y, r) for r in rows]
        )
        self.ax.relim()
        self.ax.autoscale_view()
        plt.pause(0.001)  # draws and lets the window handle its events

    def save(self, path: Union[str, Path]) -> Path:
        """Save the current state of the plot (pdf, png, ...)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=self.style.dpi)
        return path

    def show(self) -> None:
        """Keep the window open until it is closed."""
        plt.ioff()
        plt.show()
