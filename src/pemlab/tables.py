"""Tabellen: CSV-Dateien als LaTeX-Tabelle (booktabs) ausgeben."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_SPECIAL = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_"}


def _escape(text: str) -> str:
    return "".join(_SPECIAL.get(c, c) for c in text)


def _format_cell(value, decimals: int | None) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        if decimals is not None:
            return f"{value:.{decimals}f}"
        return np.format_float_positional(value, trim="-")
    return _escape(str(value))


def csv_to_tex(
    csv_path: str | Path,
    tex_path: str | Path,
    *,
    caption: str | None = None,
    label: str | None = None,
    header: list[str] | None = None,
    decimals: int | dict[str, int] | None = None,
    sep: str = ",",
    placement: str = "htbp",
) -> Path:
    """Liest eine CSV-Datei und schreibt sie als LaTeX-Tabelle in eine .tex-Datei.

    Die Tabelle nutzt booktabs (``\\toprule``/``\\midrule``/``\\bottomrule``) und
    ``\\centering``. Die erzeugte Datei kann mit ``\\input{...}`` eingebunden werden;
    im Preamble wird ``\\usepackage{booktabs}`` benötigt.

    Parameter
    ---------
    csv_path : Pfad zur CSV-Datei (erste Zeile = Spaltennamen).
    tex_path : Zieldatei; fehlende Ordner werden angelegt.
    caption, label : Beschriftung und Label (``tab:...``) der Tabelle.
    header : Spaltenüberschriften als LaTeX, z. B. ``["$U$ (V)", "$I$ (A)"]``.
        Ohne Angabe werden die Spaltennamen aus der CSV verwendet.
    decimals : Nachkommastellen für Kommazahlen, entweder für alle Spalten (int)
        oder pro Spaltenname (dict). Ohne Angabe bleibt die Zahl unverändert.
    sep : Trennzeichen der CSV (Standard ``","``, bei Tabs ``"\\t"``).
    placement : Platzierung der Tabelle (Standard ``htbp``).

    Rückgabe
    --------
    Pfad der geschriebenen .tex-Datei.
    """
    df = pd.read_csv(csv_path, sep=sep)

    if header is None:
        header = [_escape(str(c)) for c in df.columns]
    elif len(header) != len(df.columns):
        raise ValueError(
            f"header hat {len(header)} Einträge, die CSV aber {len(df.columns)} Spalten."
        )

    def dec(column: str) -> int | None:
        return decimals.get(column) if isinstance(decimals, dict) else decimals

    lines = [rf"\begin{{table}}[{placement}]"]
    if caption is not None:
        lines.append(rf"  \caption{{{caption}}}")
    if label is not None:
        lines.append(rf"  \label{{{label}}}")
    lines += [
        r"  \centering",
        rf"  \begin{{tabular}}{{@{{}}{'c' * len(df.columns)}@{{}}}}",
        r"    \toprule",
        "    " + " & ".join(header) + r" \\",
        r"    \midrule",
    ]
    for _, row in df.iterrows():
        cells = [_format_cell(row[c], dec(c)) for c in df.columns]
        lines.append("    " + " & ".join(cells) + r" \\")
    lines += [r"    \bottomrule", r"  \end{tabular}", r"\end{table}", ""]

    tex_path = Path(tex_path)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(lines), encoding="utf-8")
    return tex_path
