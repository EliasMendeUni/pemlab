"""Fits: linear regression with optional weights."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _column(df: pd.DataFrame, key: str | int) -> np.ndarray:
    """Return a column as float array; ``key`` is a column name or position."""
    series = df.iloc[:, key] if isinstance(key, int) else df[key]
    return series.to_numpy(dtype=float)


def _line(x, slope, intercept):
    return slope * x + intercept


class LinearFit:
    """Linear regression ``y = slope * x + intercept``.

    With ``sigma_y`` the fit is weighted and the uncertainties are taken as
    absolute (``chi2`` is available). Without it, all points count equally and
    parameter errors are estimated from the scatter.

    Attributes
    ----------
    slope, intercept, slope_err, intercept_err : fit parameters and 1-sigma errors.
    chi2, ndf : chi-squared (None if unweighted) and degrees of freedom.
    r2 : coefficient of determination.
    residuals : ``y - fit(x)``.
    """

    def __init__(self, x, y, sigma_y=None):
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.sigma_y = None if sigma_y is None else np.asarray(sigma_y, dtype=float)

        if self.x.ndim != 1 or self.x.shape != self.y.shape:
            raise ValueError("x and y must be 1D arrays of equal length.")
        if self.sigma_y is not None and self.sigma_y.shape != self.x.shape:
            raise ValueError("sigma_y must have the same length as x.")
        if len(self.x) < 3:
            raise ValueError("At least 3 points are needed for a fit.")

        weighted = self.sigma_y is not None
        popt, pcov = curve_fit(
            _line, self.x, self.y, sigma=self.sigma_y, absolute_sigma=weighted
        )
        self.slope, self.intercept = (float(p) for p in popt)
        self.slope_err, self.intercept_err = (float(e) for e in np.sqrt(np.diag(pcov)))

        self.residuals = self.y - self.predict(self.x)
        self.ndf = len(self.x) - 2
        self.chi2 = float(np.sum((self.residuals / self.sigma_y) ** 2)) if weighted else None
        ss_tot = np.sum((self.y - self.y.mean()) ** 2)
        self.r2 = float(1 - np.sum(self.residuals**2) / ss_tot)

    @classmethod
    def from_csv(
        cls,
        csv_path: str | Path,
        x: str | int,
        y: str | int,
        sigma_y: str | int | None = None,
        sep: str = ",",
    ) -> LinearFit:
        """Fit columns of a CSV file; columns are given by name or position (0-based)."""
        df = pd.read_csv(csv_path, sep=sep)
        err = None if sigma_y is None else _column(df, sigma_y)
        return cls(_column(df, x), _column(df, y), err)

    @property
    def reduced_chi2(self) -> float | None:
        """chi2 / ndf; about 1 for a good fit with correct uncertainties."""
        return None if self.chi2 is None else self.chi2 / self.ndf

    def predict(self, x) -> np.ndarray:
        """Evaluate the fitted line at ``x``."""
        return _line(np.asarray(x, dtype=float), self.slope, self.intercept)

    def inverse_slope(self) -> tuple[float, float]:
        """Return ``1/slope`` and its error (e.g. R = 1/a for an I-U curve)."""
        return 1 / self.slope, self.slope_err / self.slope**2

    def summary(self) -> str:
        """Fit results as text."""
        lines = [
            f"slope     = {self.slope:.5g} +- {self.slope_err:.2g}",
            f"intercept = {self.intercept:.5g} +- {self.intercept_err:.2g}",
            f"R^2       = {self.r2:.5f}",
        ]
        if self.chi2 is not None:
            lines.append(f"chi2/ndf  = {self.chi2:.2f}/{self.ndf} = {self.reduced_chi2:.2f}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()
