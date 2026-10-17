"""Project: collects csv edits, plots and tables and writes them to one build folder."""

import shutil
from pathlib import Path

from pemlab.analysis import Analysis
from pemlab.artifacts import Artifact, TableArtifact
from pemlab.data import EditCsv


class Project:
    """Set the build folder once, create things, call build() at the end.

    `tex_prefix` is the path LaTeX uses to find the build folder (for \\includegraphics),
    relative to the folder where the report is compiled. Default: the build folder as given.
    """

    def __init__(self, build_folder: str | Path, tex_prefix: str | None = None):
        self.build_folder = Path(build_folder)
        self.tex_prefix = tex_prefix if tex_prefix is not None else self.build_folder.as_posix()
        self._artifacts: dict[tuple[str, str], Artifact] = {}

    def add(self, artifact: Artifact) -> None:
        """Register an artifact; one with the same kind and name is replaced."""
        if Path(artifact.name).name != artifact.name or artifact.name in ("", ".", ".."):
            raise ValueError(f"Ungültiger Name: {artifact.name!r}")
        self._artifacts[(artifact.kind, artifact.name)] = artifact

    def edit_csv(self, file: str | Path, name: str | None = None) -> EditCsv:
        table = EditCsv(file, name)
        self.add(table)
        return table

    def analysis(self, source: str | Path | EditCsv) -> Analysis:
        return Analysis(source, register=self.add)

    def table(self, csv_file: str | Path, name: str | None = None) -> None:
        csv_file = Path(csv_file)
        self.add(TableArtifact(name or csv_file.stem, csv_file))

    def tables_from_folder(self, folder: str | Path) -> None:
        for csv_file in sorted(Path(folder).glob("*.csv")):
            self.table(csv_file)

    def build(self) -> None:
        """Write every artifact into build/<kind>/<name>/, replacing what was there."""
        for artifact in self._artifacts.values():
            folder = self.build_folder / artifact.kind / artifact.name
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True)
            tex_folder = f"{self.tex_prefix}/{artifact.kind}/{artifact.name}"
            artifact.write(folder, tex_folder)
