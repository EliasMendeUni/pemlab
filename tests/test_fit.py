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
