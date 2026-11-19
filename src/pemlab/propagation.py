"""Gaussian error propagation for a single value: the result and what contributes to it."""

import re
from collections.abc import Callable
from dataclasses import dataclass

import sympy

from pemlab.formulas import (
    column_symbol,
    evaluate,
    function_expression,
    function_variables,
    parse_formula,
    split_unit,
)
from pemlab.numberstyle import NumberStyle


def _symbol(name: str) -> str:
    """Name of a parameter in the formula: 'R_2 [Ohm]' -> 'R_2'."""
    return re.sub(r"\W+", "_", column_symbol(name)).strip("_")


@dataclass
class Parameter:
    """One quantity the result depends on."""

    name: str  # as given, e.g. 'R_2 [Ohm]'
    symbol: str  # its name in the formula, e.g. 'R_2'
    value: float
    sigma: float | None  # None: no uncertainty given, the parameter counts as exact
    derivative: float  # df/dx at the values

    @property
    def unit(self) -> str | None:
        return split_unit(self.name)[1]

    @property
    def contribution(self) -> float | None:
        """|df/dx| * sigma: what this parameter adds to the uncertainty of the result."""
        return None if self.sigma is None else abs(self.derivative) * self.sigma


@dataclass
class PropagationResult:
    """Value of a formula with its uncertainty from Gaussian error propagation."""

    result: str  # name of the result with its unit, e.g. 'U_a [V]'
    value: float
    error: float
    parameters: list[Parameter]
    expression: sympy.Expr
    derivatives: dict[str, sympy.Expr]  # symbol -> df/dx, only for parameters with an uncertainty

    @property
    def unit(self) -> str | None:
        return split_unit(self.result)[1]

    @property
    def relative_error(self) -> float | None:
        """Uncertainty in percent of the value (None for the value 0)."""
        return None if self.value == 0 else self.error / abs(self.value) * 100

    @property
    def uncertain_parameters(self) -> list[Parameter]:
        return [p for p in self.parameters if p.sigma is not None]

    def share(self, parameter: Parameter) -> float:
        """Fraction of the variance of the result that comes from this parameter (0 to 1)."""
        if parameter.sigma is None:
            return 0.0
        return parameter.contribution**2 / self.error**2

    def formatted(self, numbers: NumberStyle | None = None) -> tuple[str, str]:
        """Value and uncertainty as rounded strings."""
        return (numbers or NumberStyle()).value_error(self.value, self.error)

    def summary(self, numbers: NumberStyle | None = None) -> str:
        numbers = numbers or NumberStyle()
        value, error = self.formatted(numbers)
        unit = f" {self.unit}" if self.unit else ""
        relative = self.relative_error
        head = f"{column_symbol(self.result)} = {value} ± {error}{unit}"
        if relative is not None:
            head += f"  ({relative:.2g} %)"
        lines = [head]
        for p in self.uncertain_parameters:
            shown = f"{numbers.number(p.value)} ± {numbers.number(p.sigma, numbers.error_digits)}"
            lines.append(
                f"  {p.symbol} = {shown}: contribution {numbers.number(p.contribution, 2)}"
                f" ({self.share(p) * 100:.0f} % of the variance)"
            )
        exact = [p.symbol for p in self.parameters if p.sigma is None]
        if exact:
            lines.append(f"  without uncertainty: {', '.join(exact)}")
        return "\n".join(lines)


def _expression(formula: str | Callable) -> sympy.Expr:
    if isinstance(formula, str):
        return parse_formula(formula)
    expression = function_expression(formula)
    uses_other_names = expression is not None and {
        str(symbol) for symbol in expression.free_symbols
    } - set(function_variables(formula))  # e.g. a variable computed on an earlier line
    if expression is None or uses_other_names:
        raise ValueError(
            "Die Funktion lässt sich nicht ableiten (nur ein einzelner Ausdruck aus den "
            "Argumenten, z. B. lambda R, U: U / R). Gib die Formel sonst als Text an."
        )
    return expression


def propagate(
    formula: str | Callable,
    values: dict[str, float],
    sigmas: dict[str, float] | None = None,
    result: str = "f",
) -> PropagationResult:
    """Value of `formula` and its uncertainty by Gaussian error propagation (uncorrelated).

    `formula` is a text ("-R_2 * (U_1 / R_1 + U_2 / R_2)") or a function whose arguments are
    the parameters. `values` gives the value of every parameter, the key may carry the unit
    (`{"R_2 [Ohm]": 1e5}`); `sigmas` gives the uncertainty of the parameters that have one.
    A parameter without an entry in `sigmas` (or with 0) counts as exact and is left out of
    the propagation. `result` is the name and unit of the result, e.g. "U_a [V]".
    """
    sigmas = sigmas or {}
    expression = _expression(formula)
    if callable(formula):
        arguments = set(function_variables(formula))
    else:
        arguments = {str(symbol) for symbol in expression.free_symbols}

    names = {_symbol(key): key for key in values}
    if len(names) != len(values):
        raise ValueError(f"Zwei Parameter heißen gleich: {sorted(values)}")
    if missing := arguments - set(names):
        raise ValueError(f"Zu {sorted(missing)} fehlt der Wert. Angegeben: {sorted(names)}")
    if unused := set(names) - arguments:
        raise ValueError(f"{sorted(unused)} kommt in der Formel nicht vor ({sorted(arguments)}).")
    sigma_of = {_symbol(key): float(sigma) for key, sigma in sigmas.items()}
    if unknown := set(sigma_of) - set(names):
        raise ValueError(f"Unsicherheit für {sorted(unknown)}, das es nicht als Parameter gibt.")
    if any(s < 0 for s in sigma_of.values()):
        raise ValueError("Unsicherheiten müssen >= 0 sein.")

    point = {symbol: float(values[key]) for symbol, key in names.items()}
    parameters = []
    derivatives = {}
    for symbol in names:  # in the order of `values`
        derivative = sympy.diff(expression, sympy.Symbol(symbol))
        sigma = sigma_of.get(symbol) or None  # 0 means exact
        if sigma is not None:
            derivatives[symbol] = derivative
        slope = float(evaluate(derivative, point))
        parameters.append(Parameter(names[symbol], symbol, point[symbol], sigma, slope))
    if not derivatives:
        raise ValueError("Mindestens ein Parameter braucht eine Unsicherheit (sigmas).")

    variance = sum(p.contribution**2 for p in parameters if p.sigma is not None)
    return PropagationResult(
        result,
        float(evaluate(expression, point)),
        float(variance**0.5),
        parameters,
        expression,
        derivatives,
    )
