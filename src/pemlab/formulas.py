"""Formulas: analytic (sympy) evaluation and error propagation, fit function expressions."""

import ast
import inspect
import linecache
import re

import numpy as np
import sympy
from sympy.parsing.sympy_parser import parse_expr

_FUNCTION_NAMES = {
    "Abs", "abs", "sqrt", "exp", "log", "ln", "pi",
    "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh",
    "degrees", "radians", "log10",
}


_NUMPY_NAMES = {"arcsin": "asin", "arccos": "acos", "arctan": "atan"}  # numpy -> sympy
_EXTRA_FUNCTIONS = {  # numpy functions that sympy does not know under this name
    "degrees": lambda x: x * 180 / sympy.pi,
    "radians": lambda x: x * sympy.pi / 180,
    "log10": lambda x: sympy.log(x) / sympy.log(10),
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
    return parse_expr(text, local_dict={**_EXTRA_FUNCTIONS, **symbols})


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


def to_latex(expression: sympy.Expr, names: dict[str, str] | None = None) -> str:
    """LaTeX of an expression; `names` gives the LaTeX of single symbols (e.g. a column)."""
    names = names or {}
    symbol_names = {
        symbol: names.get(str(symbol), symbol_latex(str(symbol)))
        for symbol in expression.free_symbols
    }
    return sympy.latex(expression, mul_symbol="dot", symbol_names=symbol_names)


def _first_argument(function) -> str:
    return next(iter(inspect.signature(function).parameters))


def function_variables(function) -> list[str]:
    """Names of the arguments of a function or lambda, in the order of the definition."""
    parameters = inspect.signature(function).parameters.values()
    if any(p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD, p.KEYWORD_ONLY) for p in parameters):
        raise ValueError("Die Funktion darf nur normale Argumente haben, z. B. lambda U, I: U * I")
    return [p.name for p in parameters]


def _definition(function) -> tuple[ast.AST, str] | None:
    """The syntax tree node (def or lambda) that defines `function`, and the source it is from."""
    code = getattr(function, "__code__", None)
    if code is None:
        return None
    source = "".join(linecache.getlines(code.co_filename))  # also works for notebook cells
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    arguments = list(code.co_varnames[: code.co_argcount])
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda) and node.lineno == code.co_firstlineno:
            if [a.arg for a in node.args.args] == arguments:
                return node, source
        elif isinstance(node, ast.FunctionDef) and node.name == function.__name__:
            first_line = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            if first_line == code.co_firstlineno:
                return node, source
    return None


def _return_expression(function) -> str | None:
    """The expression a function returns, as written (None if the source is not available).

    For a lambda this is its body, for a def the last `return`.
    """
    found = _definition(function)
    if found is None:
        return None
    node, source = found
    if isinstance(node, ast.Lambda):
        value = node.body
    else:
        returns = [n for n in node.body if isinstance(n, ast.Return) and n.value is not None]
        if not returns:
            return None
        value = returns[-1].value
    text = ast.get_source_segment(source, value)
    return None if text is None else " ".join(text.split())


def _rename_argument(expression: str, argument: str, new_name: str) -> str:
    return re.sub(rf"\b{re.escape(argument)}\b", lambda _: new_name, expression)


def fit_expression_text(function, x_name: str) -> str:
    """Expression of a fit function with its x argument replaced by x_name."""
    expression = _return_expression(function)
    if expression is None:
        return function.__name__
    return _rename_argument(expression, _first_argument(function), x_name)


def function_expression(function) -> sympy.Expr | None:
    """A function or lambda as a sympy expression, None if it cannot be parsed.

    Only works for a single expression (`lambda U, I: U * I`, or a def whose last line is the
    return); numpy names like `np.sin` or `np.degrees` are understood.
    """
    expression = _return_expression(function)
    if expression is None:
        return None
    text = re.sub(
        r"\b(arcsin|arccos|arctan)\b", lambda m: _NUMPY_NAMES[m.group()],
        re.sub(r"\b(np|numpy|math)\.", "", expression),
    )
    try:
        return parse_formula(text)
    except Exception:  # arbitrary user code: any parse problem means "show it as text instead"
        return None


def fit_expression_latex(function, x_latex: str) -> str | None:
    """Expression of a fit function as LaTeX, None if it cannot be parsed.

    `x_latex` is shown for the x argument, e.g. the symbol of the x column of the plot.
    """
    expression = function_expression(function)
    if expression is None:
        return None
    return to_latex(expression, {_first_argument(function): x_latex})
