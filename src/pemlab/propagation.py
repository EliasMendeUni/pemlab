"""Gaussian error propagation for a single value: the result and what contributes to it."""

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


def _parameter(symbol: str, spec) -> tuple[float, float | None, str]:
    """(value, uncertainty, display name) of one parameter.

    A number is an exact value, a tuple is (value, uncertainty) or (value, uncertainty, name).
    No name means the argument name; an uncertainty None or 0 means exact.
    """
    if not isinstance(spec, tuple):
        spec = (spec, None)
    if len(spec) not in (2, 3):
        raise ValueError(
            f"{symbol}: eine Zahl oder (Wert, Fehler) oder (Wert, Fehler, Name) erwartet, "
            f"nicht {spec!r}."
        )
    value, sigma, *name = spec
    if sigma is not None and sigma < 0:
        raise ValueError(f"{symbol}: der Fehler muss >= 0 sein, nicht {sigma}.")
    if name and not isinstance(name[0], str):
        raise ValueError(f"{symbol}: der Name muss Text sein, z. B. '{symbol} [V]'.")
    return float(value), (float(sigma) if sigma else None), (name[0] if name else symbol)


def propagate(formula: str | Callable, result: str = "f", **parameters) -> PropagationResult:
    """Value of `formula` and its uncertainty by Gaussian error propagation (uncorrelated).

    `formula` is a function whose arguments are the parameters, or a text. Every parameter is
    a keyword argument with the name of the function argument::

        propagate(lambda R, U: U / R, "I [A]",
                  R=(100, 1, "R [Ohm]"),     # (value, uncertainty, name with unit)
                  U=(5.0, 0.01))             # without a name: "U", no unit

    A number alone (`U=5.0`) or an uncertainty of None or 0 is an exact value; it is left out of
    the propagation. `result` is the name and unit of the result, e.g. "U_a [V]". The names
    `formula` and `result` cannot be parameter names.
    """
    expression = _expression(formula)
    if callable(formula):
        arguments = set(function_variables(formula))
    else:
        arguments = {str(symbol) for symbol in expression.free_symbols}
    if missing := arguments - set(parameters):
        example = f"{sorted(missing)[0]}=(Wert, Fehler)"
        raise ValueError(f"Zu {sorted(missing)} fehlt ein Parameter, z. B. {example}.")
    if unused := set(parameters) - arguments:
        raise ValueError(f"{sorted(unused)} kommt in der Formel nicht vor ({sorted(arguments)}).")

    specs = {symbol: _parameter(symbol, spec) for symbol, spec in parameters.items()}
    point = {symbol: value for symbol, (value, _, _) in specs.items()}
    parameter_list = []
    derivatives = {}
    for symbol, (value, sigma, name) in specs.items():  # in the order of the call
        derivative = sympy.diff(expression, sympy.Symbol(symbol))
        if sigma is not None:
            derivatives[symbol] = derivative
        slope = float(evaluate(derivative, point))
        parameter_list.append(Parameter(name, symbol, value, sigma, slope))
    if not derivatives:
        raise ValueError("Mindestens ein Parameter braucht einen Fehler: R=(Wert, Fehler).")

    variance = sum(p.contribution**2 for p in parameter_list if p.sigma is not None)
    return PropagationResult(
        result,
        float(evaluate(expression, point)),
        float(variance**0.5),
        parameter_list,
        expression,
        derivatives,
    )
