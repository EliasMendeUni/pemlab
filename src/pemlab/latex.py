"""LaTeX snippets as plain strings (no file access)."""

import sympy

from pemlab.calculation import Calculation
from pemlab.fit import FitResult
from pemlab.formulas import column_symbol

_ESCAPES = {
    "\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#",
    "$": r"\$", "{": r"\{", "}": r"\}",
}


def escape_latex(text: str) -> str:
    return "".join(_ESCAPES.get(char, char) for char in text)


def symbol_latex(name: str) -> str:
    """'sigma_P' -> '\\sigma_{P}'"""
    return sympy.latex(sympy.Symbol(name))


def display_equation(left: str, right: str) -> str:
    return "\n".join([r"\[", f"  {left} = {right}", r"\]"])


def _constant_sigmas_to_tex(calculation: Calculation) -> str:
    items = [
        f"${symbol_latex(f'sigma_{symbol}')} = {value:g}$"
        for symbol, value in calculation.sigmas.items()
        if not isinstance(value, str)
    ]
    return f"mit {', '.join(items)}." if items else ""


def calculation_to_tex(calculation: Calculation) -> str:
    left = symbol_latex(column_symbol(calculation.column))
    parts = [display_equation(left, calculation.latex), _constant_sigmas_to_tex(calculation)]
    return "\n".join(part for part in parts if part)


def calculations_to_tex(calculations: list[Calculation]) -> str:
    return "\n\n".join(calculation_to_tex(c) for c in calculations)


def calculations_section_to_tex(calculations: list[Calculation]) -> str:
    """Heading plus calculations, empty string if there are none."""
    if not calculations:
        return ""
    return "\n\n".join([r"\noindent\textbf{Berechnungen}", calculations_to_tex(calculations)])


def fit_formula_to_tex(y_symbol: str, expression_latex: str | None, expression_text: str) -> str:
    if expression_latex is None:
        return rf"\texttt{{{escape_latex(f'{y_symbol} = {expression_text}')}}}"
    return display_equation(symbol_latex(y_symbol), expression_latex)


def fit_result_to_tex(result: FitResult, formula_tex: str) -> str:
    rows = [
        rf"  ${symbol_latex(name)}$ & ${value}$ & $\pm {error}$ \\"
        for name, value, error in result.formatted()
    ]
    parts = [
        r"\noindent\textbf{Regression}",
        formula_tex,
        "\n".join([r"\begin{tabular}{lrr}", r"  parameter & value & error \\", r"  \hline", *rows,
                   r"\end{tabular}"]),
    ]
    if result.chi2 is not None and result.dof > 0:
        parts.append(
            rf"$\chi^2/\mathrm{{ndf}} = {result.chi2:.3g}/{result.dof}"
            rf" = {result.chi2 / result.dof:.3g}$"
        )
    return "\n\n".join(parts)


def plot_page_to_tex(image_file: str, caption: str, label: str, sections: list[str]) -> str:
    """Figure followed by further sections (fit, calculations); empty sections are skipped."""
    figure = "\n".join([
        r"\begin{figure}[htbp]",
        r"  \centering",
        rf"  \includegraphics[width=0.8\textwidth]{{{image_file}}}",
        rf"  \caption{{{escape_latex(caption)}}}",
        rf"  \label{{{label}}}",
        r"\end{figure}",
    ])
    return "\n\n".join([figure, *(s for s in sections if s)]) + "\n"
