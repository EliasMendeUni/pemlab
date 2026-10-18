"""Things Project.build() writes into the build folder (one folder per artifact)."""

from pathlib import Path
from typing import Protocol

from matplotlib.figure import Figure

from pemlab.data import table_tex
from pemlab.latex import plot_page_to_tex


class Artifact(Protocol):
    kind: str  # subfolder of the build folder: "data", "plots", "tables"
    name: str

    def write(self, folder: Path, tex_folder: str) -> None:
        """Write into the empty `folder`. `tex_folder` is how LaTeX refers to that folder."""
        ...


class PlotArtifact:
    kind = "plots"

    def __init__(self, name: str, figure: Figure, caption: str, sections: list[str]):
        self.name = name
        self.figure = figure
        self.caption = caption
        self.sections = sections

    def write(self, folder: Path, tex_folder: str) -> None:
        self.figure.savefig(folder / "plot.pdf")
        self.figure.savefig(folder / "plot.png", dpi=200)
        tex = plot_page_to_tex(
            f"{tex_folder}/plot.pdf", self.caption, f"fig:{self.name}", self.sections
        )
        (folder / "plot.tex").write_text(tex, encoding="utf-8")


class TableArtifact:
    kind = "tables"

    def __init__(self, name: str, csv_file: str | Path):
        self.name = name
        self.csv_file = Path(csv_file)

    def write(self, folder: Path, tex_folder: str) -> None:
        table = table_tex(self.csv_file, self.name)
        (folder / f"{self.name}.tex").write_text(table + "\n", encoding="utf-8")
