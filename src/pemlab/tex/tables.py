"""Tables: write data as LaTeX (booktabs) tables."""

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


class Table:
    """A data table that can be exported as LaTeX.

    ``df`` is a pandas DataFrame; use ``Table.from_csv`` to load a CSV file.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    @classmethod
    def from_csv(cls, csv_path: str | Path, sep: str = ",") -> Table:
        """Load a CSV file (first row = column names; ``sep="\\t"`` for tabs)."""
        return cls(pd.read_csv(csv_path, sep=sep))

    def to_tex(
        self,
        tex_path: str | Path,
        *,
        caption: str | None = None,
        label: str | None = None,
        header: list[str] | None = None,
        decimals: int | dict[str, int] | None = None,
        placement: str = "htbp",
    ) -> Path:
        r"""Write a booktabs table to ``tex_path`` and return the path.

        Include it with ``\input{...}``; needs ``\usepackage{booktabs}``.

        Parameters
        ----------
        tex_path : Output file (missing folders are created).
        caption, label : Table caption and label (e.g. ``"tab:iv"``).
        header : LaTeX column headers, e.g. ``["$U$ (V)", "$I$ (A)"]``.
            Default: the column names.
        decimals : Decimal places for floats, for all columns (int) or per
            column name (dict). Default: values are written unchanged.
        placement : LaTeX float placement.
        """
        df = self.df
        if header is None:
            header = [_escape(str(c)) for c in df.columns]
        elif len(header) != len(df.columns):
            raise ValueError(f"header has {len(header)} entries, table has {len(df.columns)}.")

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
