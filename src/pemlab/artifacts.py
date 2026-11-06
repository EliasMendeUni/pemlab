"""Things Project.build() writes into the build folder (one folder per artifact)."""

from pathlib import Path
from typing import Protocol

from matplotlib.figure import Figure

from pemlab.data import table_tex
from pemlab.latex import escape_latex, figure_float_to_tex
from pemlab.numberstyle import NumberStyle


class Artifact(Protocol):
    kind: str  # subfolder of the build folder: "data", "plots", "means", "tables"
    name: str
    folder: str | None  # None: build/<kind>/<name>/; else build/<kind>/<folder>/ ("": none)

    def write(self, folder: Path, tex_folder: str) -> None:
        """Write into the empty `folder`. `tex_folder` is how LaTeX refers to that folder."""
        ...


class PlotArtifact:
    kind = "plots"
    folder = None

    def __init__(
        self, name: str, figure: Figure, caption: str, notes: list[str], png_dpi: int = 200
    ):
        self.name = name
        self.figure = figure
        self.caption = caption  # LaTeX
        self.notes = notes
        self.png_dpi = png_dpi

    def write(self, folder: Path, tex_folder: str) -> None:
        self.figure.savefig(folder / f"{self.name}.pdf")
        self.figure.savefig(folder / f"{self.name}.png", dpi=self.png_dpi)
        tex = figure_float_to_tex(
            f"{tex_folder}/{self.name}.pdf", self.caption, f"fig:{self.name}", self.notes
        )
        (folder / f"{self.name}.tex").write_text(tex, encoding="utf-8")


class MeanArtifact:
    kind = "means"
    folder = None

    def __init__(self, name: str, tex: str):
        self.name = name
        self.tex = tex

    def write(self, folder: Path, tex_folder: str) -> None:
        (folder / f"{self.name}.tex").write_text(self.tex, encoding="utf-8")


class TableArtifact:
    kind = "tables"

    def __init__(
        self,
        name: str,
        csv_file: str | Path,
        numbers: NumberStyle | None = None,
        folder: str | None = None,
    ):
        """`folder`: where below build/tables the .tex goes, e.g. "circuits/rc" (None: its own
        folder named like the table, "": directly in build/tables)."""
        self.name = name
        self.csv_file = Path(csv_file)
        self.numbers = numbers
        self.folder = folder

    def write(self, folder: Path, tex_folder: str) -> None:
        path = f"{self.folder}/{self.name}" if self.folder else self.name
        caption = escape_latex(f"{path} (raw data)")
        label = "tab:" + path.replace("/", "_") + "_raw"
        table = table_tex(self.csv_file, caption, label, numbers=self.numbers)
        (folder / f"{self.name}.tex").write_text(table, encoding="utf-8")
