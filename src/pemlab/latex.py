"""LaTeX snippets as plain strings (no file access).

Needs in the report: graphicx, booktabs, siunitx, float (the floats use [H], so they stay
exactly where they are \\input).
"""

import re

from pemlab.calculation import Calculation
from pemlab.fit import FitResult
from pemlab.formulas import column_symbol, normalize_unit, split_unit, symbol_latex, to_latex
from pemlab.numberstyle import NumberStyle
from pemlab.propagation import PropagationResult
from pemlab.stats import MeanResult

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
    """Column as a math symbol, e.g. for the left side of a calculation.

    Math that the user wrote in the name ('$\\frac{U}{I}$ [V/A]') is used as it is.
    """
    base, _ = split_unit(column)
    if "$" in base:
        return base.replace("$", "").strip()
    symbol = column_symbol(column)
    if symbol.isidentifier():
        return symbol_latex(symbol)
    return rf"\mathrm{{{escape_latex(symbol)}}}"


def _siunitx_unit(unit: str) -> str:
    unit = normalize_unit(unit).replace("$", "").replace(" ", "")
    return _SIUNITX_UNITS.get(unit, unit)


def number_with_unit_to_tex(number: str, unit: str | None) -> str:
    """'4e-05' with unit 'V' -> '\\SI{4e-05}{V}' (siunitx)."""
    if unit is None:
        return rf"\num{{{number}}}"
    return rf"\SI{{{number}}}{{{_siunitx_unit(unit)}}}"


def quantity_to_tex(value: float, unit: str | None) -> str:
    return number_with_unit_to_tex(f"{value:g}", unit)


def number_cell_to_tex(cell: str, numbers: NumberStyle, computed: bool = False) -> str:
    """A table cell: numbers rounded and written as \\num{1.5e-3} if needed, text escaped."""
    text = numbers.cell(cell, computed)
    if re.fullmatch(r"[+-]?\d+(\.\d+)?[eE][+-]?\d+", text.strip()):
        return rf"\num{{{text.strip()}}}"
    return escape_latex(text)


def _constant_sigmas_to_tex(calculation: Calculation) -> str:
    items = []
    for symbol, value in calculation.sigmas.items():
        if isinstance(value, str):
            continue
        if isinstance(value, dict):  # an uncertainty given as a function
            items.append(f"${symbol_latex(f'sigma_{symbol}')} = {value['latex']}$")
            continue
        unit = split_unit(calculation.inputs[symbol])[1]
        items.append(f"${symbol_latex(f'sigma_{symbol}')} = {quantity_to_tex(value, unit)}$")
    return f"(with {', '.join(items)})" if items else ""


def calculation_to_tex(calculation: Calculation) -> str:
    """One calculation as inline math, so several of them can follow each other in a line."""
    left = column_latex(calculation.column)
    parts = [f"${left} = {calculation.latex}$", _constant_sigmas_to_tex(calculation)]
    return " ".join(part for part in parts if part)


def calculations_to_tex(calculations: list[Calculation]) -> str:
    """All shown calculations in one paragraph; LaTeX breaks the line when it is full."""
    return "\n\\qquad\n".join(calculation_to_tex(c) for c in calculations if c.show)


def calculations_section_to_tex(calculations: list[Calculation]) -> str:
    """Label plus calculations, empty string if none of them is to be shown."""
    if not any(c.show for c in calculations):
        return ""
    return "Calculations:\n" + calculations_to_tex(calculations)


def fit_formula_to_tex(y_column: str, expression_latex: str | None, expression_text: str) -> str:
    if expression_latex is None:
        symbol = column_symbol(y_column)
        return rf"\texttt{{{escape_latex(f'{symbol} = {expression_text}')}}}"
    return f"${column_latex(y_column)} = {expression_latex}$"


def fit_result_to_tex(
    result: FitResult, formula_tex: str, numbers: NumberStyle | None = None
) -> str:
    rows = [
        rf"  ${symbol_latex(name)}$ & \num{{{value}}} & $\pm$ \num{{{error}}} \\"
        for name, value, error in result.formatted(numbers)
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
    if result.x_errors_used:
        parts.append(
            r"Uncertainties of $x$ included (effective variance: "
            r"$\sigma^2 = \sigma_y^2 + (f'(x)\,\sigma_x)^2$)."
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
    headers: list[str],
    rows: list[list[str]],
    caption: str,
    label: str,
    notes: list[str],
    numbers: NumberStyle | None = None,
    column_numbers: dict[str, NumberStyle] | None = None,
    computed: frozenset[str] = frozenset(),
) -> str:
    """Table with caption and notes as ONE float, so the notes cannot move away from it.

    `caption` is LaTeX; headers are column names (see name_to_tex); cells are plain text that
    is shown with `numbers`, or with the style of its column in `column_numbers`. The columns
    in `computed` are shown with significant digits, because they have no precision of their own.
    """
    default = numbers or NumberStyle()
    styles = [(column_numbers or {}).get(header, default) for header in headers]
    header_line = " & ".join(name_to_tex(header) for header in headers)
    is_computed = [header in computed for header in headers]
    body = [
        " & ".join(
            number_cell_to_tex(cell, style, flag)
            for cell, style, flag in zip(row, styles, is_computed, strict=True)
        )
        + r" \\"
        for row in rows
    ]
    return _table_float(header_line, body, "c" * len(headers), caption, label, notes)


def _table_float(
    header_line: str, body: list[str], alignment: str, caption: str, label: str, notes: list[str]
) -> str:
    """The [H] table float: tabular, caption, label and notes."""
    lines = [
        r"\begin{table}[H]",
        r"  \centering",
        rf"  \begin{{tabular}}{{@{{}}{alignment}@{{}}}}",
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


def _mean_rows(result: MeanResult, column: str, numbers: NumberStyle) -> list[tuple[str, str]]:
    """(label, value) pairs of the mean table; both are LaTeX."""
    unit = split_unit(column)[1]
    symbol = column_latex(column)
    value, error = result.formatted_mean(numbers)
    kind = "weighted mean" if result.weighted else "mean"

    rows = [
        ("number of values", f"${result.n}$"),
        (rf"{kind} $\bar{{{symbol}}}$", number_with_unit_to_tex(value, unit)),
    ]
    if result.std is not None:
        std = numbers.number(result.std, 3)
        rows.append(("standard deviation", number_with_unit_to_tex(std, unit)))
    if error is not None:
        label = "uncertainty of the weighted mean" if result.weighted else "standard error"
        rows.append((label, number_with_unit_to_tex(error, unit)))
    if result.chi2_ndf is not None:
        rows.append((r"$\chi^2/\mathrm{ndf}$", f"${result.chi2_ndf:.3g}$"))
    if result.reference is not None:
        rows.append(("reference value", number_with_unit_to_tex(f"{result.reference:g}", unit)))
        rows.append(("deviation", number_with_unit_to_tex(f"{result.deviation:+.3g}", unit)))
    if result.relative_deviation is not None:
        rows.append(("relative deviation", rf"${result.relative_deviation:+.2g}\,\%$"))
    if result.deviation_in_sigma is not None:
        rows.append(("deviation in units of the uncertainty", f"${result.deviation_in_sigma:.2g}$"))
    return rows


def mean_result_to_tex(
    result: MeanResult,
    column: str,
    caption: str,
    label: str,
    notes: list[str],
    numbers: NumberStyle | None = None,
) -> str:
    """Table float with the mean of a column, its spread and (optional) the reference."""
    rows = _mean_rows(result, column, numbers or NumberStyle())
    body = [f"{row_label} & {value} \\\\" for row_label, value in rows]
    return _table_float("quantity & value", body, "lr", caption, label, notes)


def _value_error_to_tex(value: str, error: str, unit: str | None) -> str:
    r"""'2.848e-9' and '0.0037e-9' -> \SI[uncertainty-mode=separate]{2.848 +- 0.0037 e-9}{V}.

    siunitx takes the exponent once, behind the uncertainty. The option makes it show a +-
    whatever the document sets.
    """
    mantissa, _, exponent = value.partition("e")
    number = f"{mantissa} +- {error.partition('e')[0]}" + (f" e{exponent}" if exponent else "")
    option = "[uncertainty-mode=separate]"
    if unit is None:
        return rf"\num{option}{{{number}}}"
    return rf"\SI{option}{{{number}}}{{{_siunitx_unit(unit)}}}"


def _parameter_table_to_tex(result: PropagationResult, numbers: NumberStyle) -> str:
    rows = []
    for p in result.parameters:
        value = number_with_unit_to_tex(numbers.number(p.value), p.unit)
        sigma = "--"
        if p.sigma is not None:
            sigma = number_with_unit_to_tex(numbers.number(p.sigma, numbers.error_digits), p.unit)
        rows.append(rf"    ${column_latex(p.name)}$ & {value} & {sigma} \\")
    return "\n".join([
        r"\begin{center}",
        r"  \begin{tabular}{@{}lrr@{}}",
        r"    \toprule",
        r"    parameter & value & uncertainty \\",
        r"    \midrule",
        *rows,
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{center}",
    ])


def _propagation_steps_to_tex(
    result: PropagationResult, names: dict[str, str], left: str, numbers: NumberStyle
) -> list[str]:
    """The formula, the derivatives and the sum of the contributions, as display math."""
    derivatives = [
        rf"\frac{{\partial {left}}}{{\partial {names[p.symbol]}}} &= "
        rf"{to_latex(result.derivatives[p.symbol], names)} = \num{{{numbers.number(p.derivative)}}}"
        for p in result.uncertain_parameters
    ]
    contributions = [
        number_with_unit_to_tex(numbers.number(p.contribution, 3), result.unit)
        for p in result.uncertain_parameters
    ]
    terms = [rf"\left({contribution}\right)^{{2}}" for contribution in contributions]
    break_line = " \\\\\n  "  # LaTeX line break inside aligned
    pairs = [" + ".join(terms[i : i + 2]) for i in range(0, len(terms), 2)]
    variance = (break_line + r"&\quad + ").join(pairs)
    error = number_with_unit_to_tex(numbers.number(result.error, numbers.error_digits), result.unit)
    sigma = rf"\sigma_{{{left}}}"
    return [
        rf"\[ {left} = {to_latex(result.expression, names)} \]",
        rf"\[ {sigma} = \sqrt{{\sum_i \left(\frac{{\partial {left}}}{{\partial x_i}}"
        r"\,\sigma_{x_i}\right)^{2}} \]",
        "\\[\n\\begin{aligned}\n  " + break_line.join(derivatives) + "\n\\end{aligned}\n\\]",
        "\\[\n\\begin{aligned}\n"
        f"  {sigma}^{{2}} &= {variance}{break_line}{sigma} &= {error}\n"
        "\\end{aligned}\n\\]",
    ]


def propagation_to_tex(
    result: PropagationResult, show: bool = False, numbers: NumberStyle | None = None
) -> str:
    r"""Parameters with their uncertainties and the result; `show` adds the calculation.

    Display math and a centered table, no float: \input it where the result belongs.
    """
    numbers = numbers or NumberStyle()
    left = column_latex(result.result)
    names = {p.symbol: column_latex(p.name) for p in result.parameters}
    value, error = result.formatted(numbers)
    final = rf"\[ {left} = {_value_error_to_tex(value, error, result.unit)} \]"
    parts = _propagation_steps_to_tex(result, names, left, numbers) if show else []
    if show:
        parts.insert(1, _parameter_table_to_tex(result, numbers))
    else:
        parts.append(_parameter_table_to_tex(result, numbers))
    return "\n".join([*parts, final]) + "\n"


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
