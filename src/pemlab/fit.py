"""Least-squares fit of a function to measurement data."""

import inspect
from dataclasses import dataclass
from math import floor, isfinite, log10

import numpy as np
from scipy.optimize import curve_fit


def format_value_error(value: float, error: float, digits: int = 2) -> tuple[str, str]:
    """Round the error to `digits` significant digits and the value to the same decimal place."""
    if not (isfinite(error) and error > 0):
        return f"{value:.4g}", f"{error:.2g}"
    decimals = digits - 1 - floor(log10(error))
    if decimals >= 0:
        return f"{value:.{decimals}f}", f"{error:.{decimals}f}"
    return f"{round(value, decimals):.0f}", f"{round(error, decimals):.0f}"


@dataclass(repr=False)
class FitResult:
    parameter_names: list[str]
    values: np.ndarray
    errors: np.ndarray
    chi2: float | None  # None if there was no y uncertainty
    dof: int

    def __repr__(self) -> str:
        return f"FitResult({self.parameters_text()})"

    def formatted(self) -> list[tuple[str, str, str]]:
        """(name, value, error) as rounded strings."""
        rows = zip(self.parameter_names, self.values, self.errors, strict=True)
        return [(name, *format_value_error(value, error)) for name, value, error in rows]

    def parameters_text(self) -> str:
        pairs = zip(self.parameter_names, self.values, strict=True)
        return ", ".join(f"{name}={value:.3g}" for name, value in pairs)

    def summary(self) -> str:
        lines = [f"{name} = {value} ± {error}" for name, value, error in self.formatted()]
        if self.chi2 is not None and self.dof > 0:
            lines.append(f"chi²/ndf = {self.chi2:.3g}/{self.dof} = {self.chi2 / self.dof:.3g}")
        return "\n".join(lines)


def parameter_names(function) -> list[str]:
    """Fit parameters: all arguments after the first one (x)."""
    return list(inspect.signature(function).parameters)[1:]


def chi_squared(function, x, y, y_sigma, values) -> float:
    return float(np.sum(((y - function(x, *values)) / y_sigma) ** 2))


def fit_function(function, x, y, y_sigma=None, p0=None) -> FitResult:
    names = parameter_names(function)
    if p0 is None:
        p0 = np.ones(len(names))

    values, covariance = curve_fit(
        function, x, y, p0=p0, sigma=y_sigma, absolute_sigma=y_sigma is not None
    )
    errors = np.sqrt(np.diag(covariance))
    chi2 = None if y_sigma is None else chi_squared(function, x, y, y_sigma, values)
    return FitResult(names, values, errors, chi2, dof=len(x) - len(values))
