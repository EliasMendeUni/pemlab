"""Tests of the error propagation of a single value (`propagate`, `Project.propagate`)."""

import numpy as np
import pytest

from pemlab import NumberStyle, Project, propagate
from pemlab.latex import propagation_to_tex

R_2 = (1e5, 1e3, "R_2 [Ohm]")
R_11 = (1e4, 100, "R_11 [Ohm]")
U_e1 = (0.5, 1e-3, "U_e1 [V]")


def amplifier(R_2, R_11, U_e1):
    return -R_2 / R_11 * U_e1


def test_value_and_uncertainty_follow_gauss():
    result = propagate(amplifier, "U_a [V]", R_2=R_2, R_11=R_11, U_e1=U_e1)
    # relative errors 1 %, 1 % and 0.2 % of -5 V
    assert result.value == pytest.approx(-5.0)
    assert result.error == pytest.approx(5.0 * np.sqrt(0.01**2 + 0.01**2 + 0.002**2))


def test_a_number_alone_is_exact():
    result = propagate(amplifier, R_2=R_2, R_11=1e4, U_e1=0.5)
    assert result.error == pytest.approx(5.0 * 0.01)
    assert [p.symbol for p in result.parameters if p.sigma is None] == ["R_11", "U_e1"]
    assert result.derivatives.keys() == {"R_2"}


@pytest.mark.parametrize("sigma", [None, 0])
def test_an_uncertainty_of_none_or_zero_is_exact_too(sigma):
    result = propagate(amplifier, R_2=R_2, R_11=(1e4, sigma), U_e1=0.5)
    assert result.error == pytest.approx(0.05)


def test_the_name_defaults_to_the_argument_name_and_may_carry_the_unit():
    result = propagate(amplifier, R_2=R_2, R_11=(1e4, 100), U_e1=(0.5, None, "U_e1 [V]"))
    assert [p.name for p in result.parameters] == ["R_2 [Ohm]", "R_11", "U_e1 [V]"]
    assert [p.unit for p in result.parameters] == ["Ohm", None, "V"]
    assert result.unit is None


def test_parameters_are_in_the_order_of_the_call():
    result = propagate(amplifier, U_e1=U_e1, R_11=R_11, R_2=R_2)
    assert [p.symbol for p in result.parameters] == ["U_e1", "R_11", "R_2"]


def test_formula_as_text_gives_the_same_as_a_function():
    text = propagate("-R_2 / R_11 * U_e1", R_2=R_2, R_11=R_11, U_e1=0.5)
    function = propagate(amplifier, R_2=R_2, R_11=R_11, U_e1=0.5)
    assert (text.value, text.error) == pytest.approx((function.value, function.error))


def test_the_shares_of_the_variance_add_up_to_one():
    result = propagate(amplifier, R_2=R_2, R_11=R_11, U_e1=U_e1)
    assert sum(result.share(p) for p in result.parameters) == pytest.approx(1.0)


def test_the_unit_of_the_result_comes_from_its_name():
    assert propagate(amplifier, "U_a [V]", R_2=R_2, R_11=1e4, U_e1=0.5).unit == "V"


def test_summary_shows_value_error_and_contributions():
    text = propagate(amplifier, "U_a [V]", R_2=R_2, R_11=1e4, U_e1=0.5).summary()
    assert "U_a = -5.000 ± 0.050 V" in text
    assert "R_2" in text and "100 % of the variance" in text
    assert "without uncertainty: R_11, U_e1" in text


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"R_2": R_2, "R_11": R_11}, "U_e1=\\(Wert, Fehler\\)"),  # a parameter is missing
        ({"R_2": R_2, "R_11": R_11, "U_e1": U_e1, "x": 1.0}, "kommt in der Formel nicht vor"),
        ({"R_2": R_2, "R_11": 1e4, "U_e1": 0.5, "R_3": (1.0, 0.1)}, "R_3"),  # not in formula
        ({"R_2": (1e5, -1.0), "R_11": R_11, "U_e1": U_e1}, ">= 0"),
        ({"R_2": 1e5, "R_11": 1e4, "U_e1": 0.5}, "braucht einen Fehler"),  # no uncertainty at all
        ({"R_2": (1e5,), "R_11": R_11, "U_e1": U_e1}, "Wert, Fehler"),
        ({"R_2": (1e5, 1e3, 7), "R_11": R_11, "U_e1": U_e1}, "Text"),
    ],
)
def test_wrong_input_gets_a_helpful_error(parameters, message):
    with pytest.raises(ValueError, match=message):
        propagate(amplifier, **parameters)


def test_a_function_that_cannot_be_differentiated_is_refused():
    def not_one_expression(R_2, R_11, U_e1):
        gain = R_2 / R_11
        print(gain)
        return -gain * U_e1

    with pytest.raises(ValueError, match="lässt sich nicht ableiten"):
        propagate(not_one_expression, R_2=R_2, R_11=1e4, U_e1=0.5)


def test_tex_with_the_calculation_has_formula_derivatives_and_result():
    result = propagate(amplifier, "U_a [V]", R_2=R_2, R_11=R_11, U_e1=(0.5, None, "U_e1 [V]"))
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
    result = propagate("a * 1e-9", "U [V]", a=(2.848, 0.0037))
    assert r"{2.8480 +- 0.0037 e-9}{V}" in propagation_to_tex(result)


def test_project_writes_the_artifact_and_returns_the_result(tmp_path, capsys):
    lab = Project(tmp_path / "build", numbers=NumberStyle())
    result = lab.propagate(
        "gain", amplifier, result="U_a [V]", show=True, R_2=R_2, R_11=1e4, U_e1=0.5
    )
    lab.build()

    assert result.value == pytest.approx(-5.0)
    assert "U_a = -5.000 ± 0.050 V" in capsys.readouterr().out
    tex = (tmp_path / "build" / "propagations" / "gain" / "gain.tex").read_text(encoding="utf-8")
    assert r"\partial" in tex
