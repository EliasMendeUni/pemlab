"""Things Project.build() writes into the build folder (one folder per artifact)."""

from pathlib import Path
from typing import Protocol

from matplotlib.figure import Figure

from pemlab.data import table_tex
from pemlab.latex import escape_latex, figure_float_to_tex


class Artifact(Protocol):
    kind: str  # subfolder of the build folder: "data", "plots", "tables"
    name: str

    def write(self, folder: Path, tex_folder: str) -> None:
        """Write into the empty `folder`. `tex_folder` is how LaTeX refers to that folder."""
        ...


class PlotArtifact:
    kind = "plots"

    def __init__(self, name: str, figure: Figure, caption: str, notes: list[str]):
        self.name = name
        self.figure = figure
        self.caption = caption  # LaTeX
        self.notes = notes

    def write(self, folder: Path, tex_folder: str) -> None:
        self.figure.savefig(folder / f"{self.name}.pdf")
        self.figure.savefig(folder / f"{self.name}.png", dpi=200)
        tex = figure_float_to_tex(
            f"{tex_folder}/{self.name}.pdf", self.caption, f"fig:{self.name}", self.notes
        )
        (folder / f"{self.name}.tex").write_text(tex, encoding="utf-8")


class TableArtifact:
    kind = "tables"

    def __init__(self, name: str, csv_file: str | Path):
        self.name = name
        self.csv_file = Path(csv_file)

    def write(self, folder: Path, tex_folder: str) -> None:
        caption = escape_latex(f"{self.name} (raw data)")
        table = table_tex(self.csv_file, caption, f"tab:{self.name}_raw")
        (folder / f"{self.name}.tex").write_text(table, encoding="utf-8")
