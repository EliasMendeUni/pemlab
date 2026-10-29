"""Styles of the plots: PointStyle (data), FitStyle (fit curve) and LayoutStyle (axes, figure).

Every field has a default, so you only name what you want to change. `None` means automatic:
names come from the columns, colors from matplotlib's color cycle. `dataclasses.replace(style,
grid=False)` makes a changed copy of a style.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PointStyle:
    """Measured points and their error bars."""

    marker: str = "o"
    marker_size: float = 3.0  # in points
    marker_color: str | None = None
    marker_alpha: float = 1.0  # < 1 helps with many overlapping points
    connect_points: bool = False  # draw a line between the points
    label: str | None = "Messdaten"  # legend text; None: no legend entry

    # used when the data has a y uncertainty
    capsize: float = 2.0
    errorbar_linewidth: float = 0.8

    def __post_init__(self) -> None:
        if self.marker_size <= 0:
            raise ValueError(f"marker_size muss > 0 sein, nicht {self.marker_size}")
        if not 0 <= self.marker_alpha <= 1:
            raise ValueError(f"marker_alpha muss in [0, 1] liegen, nicht {self.marker_alpha}")


@dataclass(frozen=True)
class FitStyle:
    """The fit curve (only used by plots with a fit)."""

    color: str | None = None
    linewidth: float = 1.5
    linestyle: str = "-"
    points: int = 200  # resolution of the curve
    label: str | None = None  # None: formula and parameters

    def __post_init__(self) -> None:
        if self.points < 2:
            raise ValueError(f"points muss >= 2 sein, nicht {self.points}")


@dataclass(frozen=True)
class LayoutStyle:
    """Figure, axes, legend and fonts."""

    figsize: tuple[float, float] = (6.0, 4.0)  # inches
    xlabel: str | None = None  # None: from the column name
    ylabel: str | None = None
    title: str | None = None
    xscale: str = "linear"  # "linear", "log", ...
    yscale: str = "linear"
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    grid: bool = True
    legend: bool | None = None  # None: legend for fit plots, none for plain data plots
    legend_loc: str = "best"
    font_size: float | None = None  # None: matplotlib default; applies to all text of the plot
    png_dpi: int = 200  # resolution of the png next to the pdf
