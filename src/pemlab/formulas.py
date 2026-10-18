"""Formulas: analytic (sympy) evaluation and error propagation, fit function expressions."""

import inspect
import re

import numpy as np
import sympy
from sympy.parsing.sympy_parser import parse_expr

_FUNCTION_NAMES = {
    "Abs", "abs", "sqrt", "exp", "log", "ln", "pi",
    "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh",
}


_UNIT_PATTERN = re.compile(r"^(.*?)\s*\[(.*)\]\s*$")
_UNIT_ALIASES = {"Ohm": r"\Omega", "ohm": r"\Omega"}


def split_unit(column: str) -> tuple[str, str | None]:
    """'U [V]' -> ('U', 'V'); a name without brackets has no unit."""
    match = _UNIT_PATTERN.match(column)
    if match is None:
        return column.strip(), None
    return match.group(1).strip(), match.group(2).strip()


def normalize_unit(unit: str) -> str:
    """'Ohm' -> '\\Omega'; other units unchanged."""
    return _UNIT_ALIASES.get(unit, unit)


def column_symbol(column: str) -> str:
    """Name used in formulas: no unit, no math markup. '$R_i$ [\\Omega]' -> 'R_i'."""
    base, _ = split_unit(column)
    return re.sub(r"[$\\{}]", "", base)


def symbol_latex(name: str) -> str:
    """'U_L' -> 'U_{L}', 'I_eff_mA' -> 'I_{eff,mA}', 'sigma_U_L' -> '\\sigma_{U_{L}}'."""
    base, _, subscript = name.partition("_")
    if base == "sigma" and subscript:
        return rf"\sigma_{{{symbol_latex(subscript)}}}"
    latex = sympy.latex(sympy.Symbol(base))
    return f"{latex}_{{{subscript.replace('_', ',')}}}" if subscript else latex


def rename_symbol(expression: sympy.Expr, old: str, new: str) -> sympy.Expr:
    return expression.subs(sympy.Symbol(old), sympy.Symbol(new))


def formula_names(text: str) -> list[str]:
    """Variable names in a formula string (functions like sqrt excluded)."""
    names = re.findall(r"(?<![\w.])[A-Za-z_]\w*", text)
    return sorted({name for name in names if name not in _FUNCTION_NAMES})


def parse_formula(text: str) -> sympy.Expr:
    """Parse e.g. 'U * I'. Every name is a plain symbol (so 'I' is not the imaginary unit)."""
    symbols = {name: sympy.Symbol(name) for name in formula_names(text)}
    return parse_expr(text, local_dict=symbols)


def input_symbols(expression: sympy.Expr) -> list[str]:
    return sorted(str(symbol) for symbol in expression.free_symbols)


def propagate_uncertainty(expression: sympy.Expr) -> sympy.Expr:
    """Gaussian error propagation: sqrt(sum((df/dx_i * sigma_x_i)^2)), derived analytically."""
    terms = []
    for name in input_symbols(expression):
        sigma = sympy.Symbol(f"sigma_{name}", positive=True)
        terms.append((sympy.diff(expression, sympy.Symbol(name)) * sigma) ** 2)
    return sympy.sqrt(sum(terms))


def evaluate(expression: sympy.Expr, values: dict[str, np.ndarray | float]):
    """Evaluate with numpy; `values` maps symbol names to arrays or numbers."""
    symbols = sorted(expression.free_symbols, key=str)
    function = sympy.lambdify(symbols, expression, modules="numpy")
    return function(*(values[str(symbol)] for symbol in symbols))


def to_latex(expression: sympy.Expr) -> str:
    names = {symbol: symbol_latex(str(symbol)) for symbol in expression.free_symbols}
    return sympy.latex(expression, mul_symbol="dot", symbol_names=names)


def _first_argument(function) -> str:
    return next(iter(inspect.signature(function).parameters))


def _return_expression(function) -> str | None:
    """Text after `return` in the function's source (None if the source is not available)."""
    try:
        lines = inspect.getsource(function).splitlines()
    except (OSError, TypeError):
        return None
    for line in reversed(lines):
        line = line.strip()
        if line.startswith("return "):
            return line.removeprefix("return ")
    return None


def _rename_argument(expression: str, argument: str, new_name: str) -> str:
    return re.sub(rf"\b{re.escape(argument)}\b", lambda _: new_name, expression)


def fit_expression_text(function, x_name: str) -> str:
    """Expression of a fit function with its x argument replaced by x_name."""
    expression = _return_expression(function)
    if expression is None:
        return function.__name__
    return _rename_argument(expression, _first_argument(function), x_name)


def fit_expression_latex(function, x_symbol: str) -> str | None:
    """Expression of a fit function as LaTeX, None if it cannot be parsed."""
    expression = _return_expression(function)
    if expression is None or not x_symbol.isidentifier():
        return None
    text = _rename_argument(expression.replace("np.", ""), _first_argument(function), x_symbol)
    try:
        return to_latex(parse_formula(text))
    except Exception:  # arbitrary user code: any parse problem means "show it as text instead"
        return None
