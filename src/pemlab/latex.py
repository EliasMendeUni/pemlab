"""LaTeX snippets as plain strings (no file access).

Needs in the report: graphicx, booktabs, siunitx, float (the floats use [H], so they stay
exactly where they are \\input).
"""

from pemlab.calculation import Calculation
from pemlab.fit import FitResult
from pemlab.formulas import column_symbol, normalize_unit, split_unit, symbol_latex

_ESCAPES = {
    "\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#",
    "$": r"\$", "{": r"\{", "}": r"\}",
}
_SIUNITX_UNITS = {r"\Omega": r"\ohm"}


def escape_latex(text: str) -> str:
    return "".join(_ESCAPES.get(char, char) for char in text)


def text_with_math(text: str) -> str:
    """Text for LaTeX: '$R_i$' stays math, '\\Omega' becomes math, anything else is escaped."""
    if "$" in text:
        return text
    if "\\" in text:
        return f"${text}$"
    return escape_latex(text)


def name_to_tex(name: str) -> str:
    """Column name as LaTeX text: '$R_i$ [\\Omega]' -> '$R_i$ [$\\Omega$]'."""
    base, unit = split_unit(name)
    if unit is None:
        return text_with_math(base)
    return f"{text_with_math(base)} [{text_with_math(normalize_unit(unit))}]"


def column_latex(column: str) -> str:
    """Column as a math symbol, e.g. for the left side of a calculation."""
    symbol = column_symbol(column)
    if symbol.isidentifier():
        return symbol_latex(symbol)
    return rf"\mathrm{{{escape_latex(symbol)}}}"


def quantity_to_tex(value: float, unit: str | None) -> str:
    """4e-05 with unit 'V' -> '\\SI{4e-05}{V}' (siunitx)."""
    if unit is None:
        return rf"\num{{{value:g}}}"
    siunitx_unit = normalize_unit(unit).replace("$", "").replace(" ", "")
    siunitx_unit = _SIUNITX_UNITS.get(siunitx_unit, siunitx_unit)
    return rf"\SI{{{value:g}}}{{{siunitx_unit}}}"


def _constant_sigmas_to_tex(calculation: Calculation) -> str:
    items = []
    for symbol, value in calculation.sigmas.items():
        if isinstance(value, str):
            continue
        unit = split_unit(calculation.inputs[symbol])[1]
        items.append(f"${symbol_latex(f'sigma_{symbol}')} = {quantity_to_tex(value, unit)}$")
    return f"(mit {', '.join(items)})" if items else ""


def calculation_to_tex(calculation: Calculation) -> str:
    """One calculation as inline math, so several of them can follow each other in a line."""
    left = column_latex(calculation.column)
    parts = [f"${left} = {calculation.latex}$", _constant_sigmas_to_tex(calculation)]
    return " ".join(part for part in parts if part)


def calculations_to_tex(calculations: list[Calculation]) -> str:
    """All calculations in one paragraph; LaTeX breaks the line when it is full."""
    return "\n\\qquad\n".join(calculation_to_tex(c) for c in calculations)


def calculations_section_to_tex(calculations: list[Calculation]) -> str:
    """Label plus calculations, empty string if there are none."""
    if not calculations:
        return ""
    return "Calculations:\n" + calculations_to_tex(calculations)


def fit_formula_to_tex(y_column: str, expression_latex: str | None, expression_text: str) -> str:
    if expression_latex is None:
        symbol = column_symbol(y_column)
        return rf"\texttt{{{escape_latex(f'{symbol} = {expression_text}')}}}"
    return f"${column_latex(y_column)} = {expression_latex}$"


def fit_result_to_tex(result: FitResult, formula_tex: str) -> str:
    rows = [
        rf"  ${symbol_latex(name)}$ & ${value}$ & $\pm {error}$ \\"
        for name, value, error in result.formatted()
    ]
    parts = [
        f"Regression: {formula_tex}",
        "\n".join([r"\begin{tabular}{lrr}", r"  parameter & value & error \\", r"  \hline", *rows,
                   r"\end{tabular}"]),
    ]
    if result.chi2 is not None and result.dof > 0:
        parts.append(
            rf"$\chi^2/\mathrm{{ndf}} = {result.chi2:.3g}/{result.dof}"
            rf" = {result.chi2 / result.dof:.3g}$"
        )
    return "\n\\par\\smallskip\n".join(parts)


def notes_to_tex(sections: list[str]) -> str:
    """Small text below a table or figure, inside the same float. Empty if there is nothing."""
    sections = [section for section in sections if section]
    if not sections:
        return ""
    body = "\n  \\par\\smallskip\n".join(sections)
    return "\n".join([r"  \par\medskip", r"  {\footnotesize", body, r"  }"])


def table_float_to_tex(
    headers: list[str], rows: list[list[str]], caption: str, label: str, notes: list[str]
) -> str:
    """Table with caption and notes as ONE float, so the notes cannot move away from it.

    `caption` is LaTeX; headers are column names (see name_to_tex); cells are plain text.
    """
    header_line = " & ".join(name_to_tex(header) for header in headers)
    body = [" & ".join(escape_latex(cell) for cell in row) + r" \\" for row in rows]
    lines = [
        r"\begin{table}[H]",
        r"  \centering",
        rf"  \begin{{tabular}}{{@{{}}{'c' * len(headers)}@{{}}}}",
        r"    \toprule",
        f"    {header_line} \\\\",
        r"    \midrule",
        *(f"    {line}" for line in body),
        r"    \bottomrule",
        r"  \end{tabular}",
        rf"  \caption{{{caption}}}",
        rf"  \label{{{label}}}",
        notes_to_tex(notes),
        r"\end{table}",
    ]
    return "\n".join(line for line in lines if line) + "\n"


def figure_float_to_tex(image_file: str, caption: str, label: str, notes: list[str]) -> str:
    """Figure with caption and notes (fit, calculations) as ONE float. `caption` is LaTeX."""
    lines = [
        r"\begin{figure}[H]",
        r"  \centering",
        rf"  \includegraphics[width=0.8\textwidth]{{{image_file}}}",
        rf"  \caption{{{caption}}}",
        rf"  \label{{{label}}}",
        notes_to_tex(notes),
        r"\end{figure}",
    ]
    return "\n".join(line for line in lines if line) + "\n"
