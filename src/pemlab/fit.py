"""Least-squares fit of a function to measurement data."""

import inspect
from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from pemlab.numberstyle import NumberStyle


@dataclass(repr=False)
class FitResult:
    parameter_names: list[str]
    values: np.ndarray
    errors: np.ndarray
    chi2: float | None  # None if there was no y uncertainty
    dof: int

    def __repr__(self) -> str:
        return f"FitResult({self.parameters_text()})"

    def formatted(self, numbers: NumberStyle | None = None) -> list[tuple[str, str, str]]:
        """(name, value, error) as rounded strings; `values` and `errors` stay exact."""
        numbers = numbers or NumberStyle()
        rows = zip(self.parameter_names, self.values, self.errors, strict=True)
        return [(name, *numbers.value_error(value, error)) for name, value, error in rows]

    def parameters_text(self) -> str:
        pairs = zip(self.parameter_names, self.values, strict=True)
        return ", ".join(f"{name}={value:.3g}" for name, value in pairs)

    def summary(self, numbers: NumberStyle | None = None) -> str:
        lines = [f"{name} = {value} ± {error}" for name, value, error in self.formatted(numbers)]
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


def exponential(x, U_0, U_inf, tau):
    return U_inf + (U_0 - U_inf) * np.exp(-x / tau)


def _exponential_start_values(x, y) -> list[float]:
    """Rough U_0, U_inf and tau (time until 1/e of the step is left) as start of the fit."""
    u_inf = float(np.mean(y[-max(1, len(y) // 10):]))
    u_0 = float(y[0])
    left = np.flatnonzero(np.abs(y - u_inf) <= np.exp(-1) * abs(u_0 - u_inf))
    tau = float(x[left[0]] - x[0]) if len(left) else 0.0
    return [u_0, u_inf, tau if tau > 0 else float(x[-1] - x[0]) / 5]


def fit_exponential(x, y, sigma=None, t_start=None) -> FitResult:
    """Fit y = U_inf + (U_0 - U_inf) * exp(-t/tau), e.g. a capacitor charging or discharging.

    Only points from `t_start` on are used (default: the first point), and the time is counted
    from there, so U_0 is the value at `t_start`. Parameters: U_0, U_inf, tau.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    start = x[0] if t_start is None else t_start
    keep = x >= start
    x, y = x[keep] - start, y[keep]
    sigma = None if sigma is None else np.asarray(sigma, dtype=float)[keep]
    return fit_function(exponential, x, y, sigma, p0=_exponential_start_values(x, y))
