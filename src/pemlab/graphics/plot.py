"""Plots: data and fit results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pemlab.analysis.fit import LinearFit


class FitPlot:
    """Data with error bars and fitted line, optionally with a residual panel.

    The figure is built on creation; use ``save`` or ``show``. ``fig``, ``ax``
    and ``ax_res`` (None without residuals) allow further matplotlib tweaks.
    """

    def __init__(
        self,
        fit: LinearFit,
        *,
        xlabel: str = "$x$",
        ylabel: str = "$y$",
        data_label: str = "Data",
        fit_label: str = "Linear fit",
        residuals: bool = True,
        figsize: tuple[float, float] | None = None,
    ):
        self.fit = fit
        if residuals:
            self.fig, (self.ax, self.ax_res) = plt.subplots(
                2,
                1,
                sharex=True,
                figsize=figsize or (6, 6),
                gridspec_kw={"height_ratios": [3, 1]},
            )
        else:
            self.fig, self.ax = plt.subplots(figsize=figsize or (6, 4))
            self.ax_res = None

        x_line = np.linspace(fit.x.min(), fit.x.max(), 200)
        self.ax.errorbar(fit.x, fit.y, yerr=fit.sigma_y, fmt="o", capsize=2, label=data_label)
        self.ax.plot(x_line, fit.predict(x_line), "r-", label=fit_label)
        self.ax.set_ylabel(ylabel)
        self.ax.legend()
        self.ax.grid(True)

        if self.ax_res is not None:
            self.ax_res.errorbar(fit.x, fit.residuals, yerr=fit.sigma_y, fmt="o", capsize=2)
            self.ax_res.axhline(0, color="r")
            self.ax_res.set_xlabel(xlabel)
            self.ax_res.set_ylabel("Residuals")
            self.ax_res.grid(True)
        else:
            self.ax.set_xlabel(xlabel)

        self.fig.tight_layout()

    def save(self, path: str | Path) -> Path:
        """Save the figure (format from the file extension); creates folders."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path)
        return path

    def show(self) -> None:
        """Open the figure in a window."""
        plt.show()
