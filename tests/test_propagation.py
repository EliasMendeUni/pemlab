"""Tests of the error propagation of a single value (`propagate`, `Project.propagate`)."""

import numpy as np
import pytest

from pemlab import NumberStyle, Project, propagate
from pemlab.latex import propagation_to_tex

VALUES = {"R_2 [Ohm]": 1e5, "R_11 [Ohm]": 1e4, "U_e1 [V]": 0.5}


def amplifier(R_2, R_11, U_e1):
    return -R_2 / R_11 * U_e1


def test_value_and_uncertainty_follow_gauss():
    result = propagate(amplifier, VALUES, {"R_2": 1e3, "R_11": 100, "U_e1 [V]": 1e-3}, "U_a [V]")
    # relative errors 1 %, 1 % and 0.2 % of -5 V
    assert result.value == pytest.approx(-5.0)
    assert result.error == pytest.approx(5.0 * np.sqrt(0.01**2 + 0.01**2 + 0.002**2))


def test_a_parameter_without_uncertainty_counts_as_exact():
    result = propagate(amplifier, VALUES, {"R_2": 1e3})
    assert result.error == pytest.approx(5.0 * 0.01)
    exact = [p.symbol for p in result.parameters if p.sigma is None]
    assert exact == ["R_11", "U_e1"]
    assert result.derivatives.keys() == {"R_2"}


def test_a_zero_uncertainty_is_exact_too():
    assert propagate(amplifier, VALUES, {"R_2": 1e3, "R_11": 0}).error == pytest.approx(0.05)


def test_formula_as_text_gives_the_same_as_a_function():
    text = propagate("-R_2 / R_11 * U_e1", VALUES, {"R_2": 1e3, "R_11": 100})
    function = propagate(amplifier, VALUES, {"R_2": 1e3, "R_11": 100})
    assert (text.value, text.error) == pytest.approx((function.value, function.error))


def test_the_shares_of_the_variance_add_up_to_one():
    result = propagate(amplifier, VALUES, {"R_2": 1e3, "R_11": 100, "U_e1": 1e-3})
    assert sum(result.share(p) for p in result.parameters) == pytest.approx(1.0)


def test_unit_and_symbol_come_from_the_names():
    result = propagate(amplifier, VALUES, {"R_2": 1e3}, "U_a [V]")
    assert result.unit == "V"
    assert [p.unit for p in result.parameters] == ["Ohm", "Ohm", "V"]  # order of `values`


def test_summary_shows_value_error_and_contributions():
    text = propagate(amplifier, VALUES, {"R_2": 1e3}, "U_a [V]").summary()
    assert "U_a = -5.000 ± 0.050 V" in text
    assert "R_2" in text and "100 % of the variance" in text
    assert "without uncertainty: R_11, U_e1" in text


@pytest.mark.parametrize(
    ("values", "sigmas", "message"),
    [
        ({"R_2": 1.0, "R_11": 1.0}, {"R_2": 0.1}, "U_e1"),  # a value is missing
        ({**VALUES, "x": 1.0}, {"R_2": 0.1}, "kommt in der Formel nicht vor"),
        (VALUES, {"R_3": 0.1}, "nicht als Parameter"),
        (VALUES, {"R_2": -1.0}, ">= 0"),
        (VALUES, {}, "Mindestens ein Parameter"),
    ],
)
def test_wrong_input_gets_a_helpful_error(values, sigmas, message):
    with pytest.raises(ValueError, match=message):
        propagate(amplifier, values, sigmas)


def test_a_function_that_cannot_be_differentiated_is_refused():
    def not_one_expression(R_2, R_11, U_e1):
        gain = R_2 / R_11
        print(gain)
        return -gain * U_e1

    with pytest.raises(ValueError, match="lässt sich nicht ableiten"):
        propagate(not_one_expression, VALUES, {"R_2": 1.0})


def test_tex_with_the_calculation_has_formula_derivatives_and_result():
    result = propagate(amplifier, VALUES, {"R_2": 1e3, "R_11": 100}, "U_a [V]")
    short = propagation_to_tex(result, show=False)
    long = propagation_to_tex(result, show=True)

    assert r"\SI[uncertainty-mode=separate]{-5.000 +- 0.071}{V}" in short
    assert r"\partial" not in short
    assert r"R_{2}$ & \SI{1.000e5}{\ohm} & \SI{1000}{\ohm}" in short
    assert r"U_{e1}$ & \SI{0.5000}{V} & --" in short  # without an uncertainty: a dash

    assert r"\frac{\partial U_{a}}{\partial R_{2}}" in long
    assert r"\sigma_{U_{a}}^{2}" in long
    assert long.endswith(short.splitlines()[-1] + "\n")  # the same result line in both


def test_tex_writes_the_exponent_once_behind_the_uncertainty():
    result = propagate("a * 1e-9", {"a": 2.848}, {"a": 0.0037}, "U [V]")
    tex = propagation_to_tex(result)
    assert r"{2.8480 +- 0.0037 e-9}{V}" in tex


def test_project_writes_the_artifact_and_returns_the_result(tmp_path, capsys):
    lab = Project(tmp_path / "build", numbers=NumberStyle())
    result = lab.propagate("gain", amplifier, VALUES, {"R_2": 1e3}, result="U_a [V]", show=True)
    lab.build()

    assert result.value == pytest.approx(-5.0)
    assert "U_a = -5.000 ± 0.050 V" in capsys.readouterr().out
    tex = (tmp_path / "build" / "propagations" / "gain" / "gain.tex").read_text(encoding="utf-8")
    assert r"\partial" in tex
