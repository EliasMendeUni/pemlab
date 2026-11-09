"""Tests of the fit functions."""

import numpy as np
import pytest

from pemlab.fit import fit_exponential


def test_fit_exponential_recovers_the_parameters():
    t = np.linspace(-1, 5, 300)
    u = 1.0 + 4.0 * np.exp(-np.clip(t, 0, None) / 0.8)  # discharging starts at t=0
    result = fit_exponential(t, u, t_start=0)
    values = dict(zip(result.parameter_names, result.values, strict=True))
    assert values["U_0"] == pytest.approx(5.0, abs=1e-3)
    assert values["U_inf"] == pytest.approx(1.0, abs=1e-3)
    assert values["tau"] == pytest.approx(0.8, abs=1e-3)
    rising = fit_exponential(t[t >= 0], 2.0 - 2.0 * np.exp(-t[t >= 0] / 0.5))
    assert dict(zip(rising.parameter_names, rising.values, strict=True))["tau"] == pytest.approx(
        0.5, abs=1e-3
    )


# --- uncertainty of x ---


def straight(x, a, b):
    return a * x + b


def decay(x, a, tau):
    return a * np.exp(-x / tau)


def test_x_uncertainty_enlarges_the_errors_by_the_effective_sigma():
    from pemlab.fit import fit_function

    x = np.linspace(0, 10, 12)
    y = 2 * x + 1
    sigma_y, sigma_x, slope = 0.1, 0.05, 2.0
    without = fit_function(straight, x, y, np.full(12, sigma_y), p0=[1, 0])
    sigma_xs = np.full(12, sigma_x)
    with_x = fit_function(straight, x, y, np.full(12, sigma_y), p0=[1, 0], x_sigma=sigma_xs)
    ratio = np.sqrt(1 + (slope * sigma_x / sigma_y) ** 2)  # sigma_eff / sigma_y
    assert with_x.errors == pytest.approx(without.errors * ratio, rel=1e-6)
    assert with_x.values == pytest.approx([2.0, 1.0])
    assert with_x.x_errors_used and not without.x_errors_used
    assert with_x.chi2 == pytest.approx(0, abs=1e-9)


def test_x_uncertainty_alone_weights_the_points():
    from pemlab.fit import fit_function

    x = np.linspace(0, 4, 10)
    y = 3 * np.exp(-x / 2)
    result = fit_function(decay, x, y, p0=[1, 1], x_sigma=np.full(10, 0.05))
    assert result.values == pytest.approx([3.0, 2.0], rel=1e-6)
    assert result.chi2 is not None and result.dof == 8


def test_the_result_is_self_consistent_for_a_curved_function():
    from pemlab.fit import _effective_sigma, fit_function

    rng = np.random.default_rng(3)
    x = np.linspace(0, 4, 15)
    y = 3 * np.exp(-x / 2) + 0.02 * rng.standard_normal(15)
    sigma_y, sigma_x = np.full(15, 0.02), np.full(15, 0.1)
    result = fit_function(decay, x, y, sigma_y, p0=[1, 1], x_sigma=sigma_x)
    sigma = _effective_sigma(decay, x, result.values, sigma_y, sigma_x)
    again = fit_function(decay, x, y, sigma, p0=result.values)  # weights fixed at the result
    assert again.values == pytest.approx(result.values, rel=1e-6)
    assert result.chi2 == pytest.approx(again.chi2, rel=1e-6)


def test_a_point_without_any_uncertainty_is_reported():
    from pemlab.fit import fit_function

    x = np.linspace(0, 4, 5)
    with pytest.raises(ValueError, match="Unsicherheit 0"):
        fit_function(straight, x, 2 * x, x_sigma=np.zeros(5), p0=[1, 0])
