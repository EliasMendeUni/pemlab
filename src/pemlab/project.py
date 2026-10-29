"""Project: collects csv edits, plots and tables and writes them to one build folder."""

import os
import shutil
import stat
import sys
from pathlib import Path

from pemlab.analysis import Analysis
from pemlab.artifacts import Artifact, TableArtifact
from pemlab.data import EditCsv, column_variables_to_text
from pemlab.numberstyle import NumberStyle
from pemlab.plotstyle import FitStyle, LayoutStyle, PointStyle

_BUILD_MARKER = ".pemlab-build"
_RMTREE_ERROR_ARGUMENT = "onexc" if sys.version_info >= (3, 12) else "onerror"


def _clear_read_only_and_retry(function, path, _error) -> None:
    """rmtree error handler: Windows refuses to delete read-only files and folders (OneDrive)."""
    os.chmod(path, stat.S_IWRITE)
    function(path)


class Project:
    """Set the build folder once, create things, call build() at the end.

    `tex_prefix` is the path LaTeX uses to find the build folder (for \\includegraphics),
    relative to the folder where the report is compiled. Default: the build folder as given.

    `points`, `fit` and `layout` are the looks of all plots of the project (see `PointStyle`,
    `FitStyle` and `LayoutStyle`); the same arguments of a single plot override them one by one.
    `numbers` (a `NumberStyle`) is how tables, fit results and means show their numbers; the
    same argument of a single call overrides it.
    """

    def __init__(
        self,
        build_folder: str | Path,
        tex_prefix: str | None = None,
        points: PointStyle | None = None,
        fit: FitStyle | None = None,
        layout: LayoutStyle | None = None,
        numbers: NumberStyle | None = None,
    ):
        self.build_folder = Path(build_folder)
        self.tex_prefix = tex_prefix if tex_prefix is not None else self.build_folder.as_posix()
        self.points = points
        self.fit = fit
        self.layout = layout
        self.numbers = numbers
        self._artifacts: dict[tuple[str, str], Artifact] = {}

    def add(self, artifact: Artifact) -> None:
        """Register an artifact; one with the same kind and name is replaced."""
        if Path(artifact.name).name != artifact.name or artifact.name in ("", ".", ".."):
            raise ValueError(f"Ungültiger Name: {artifact.name!r}")
        self._artifacts[(artifact.kind, artifact.name)] = artifact

    def edit_csv(
        self, file: str | Path, name: str | None = None, numbers: NumberStyle | None = None
    ) -> EditCsv:
        table = EditCsv(file, name, numbers or self.numbers)
        self.add(table)
        return table

    def analysis(self, source: str | Path | EditCsv) -> Analysis:
        return Analysis(
            source,
            register=self.add,
            points=self.points,
            fit=self.fit,
            layout=self.layout,
            numbers=self.numbers,
        )

    def table(
        self, csv_file: str | Path, name: str | None = None, numbers: NumberStyle | None = None
    ) -> None:
        csv_file = Path(csv_file)
        self.add(TableArtifact(name or csv_file.stem, csv_file, numbers or self.numbers))

    def tables_from_folder(self, folder: str | Path, numbers: NumberStyle | None = None) -> None:
        for csv_file in sorted(Path(folder).glob("*.csv")):
            self.table(csv_file, numbers=numbers)

    def column_names_from_folder(self, folder: str | Path) -> None:
        """Print one Python variable per CSV column, ready to copy into your script.

        A helper for the start of an analysis: call it once, paste the output into the script
        and delete the call again.
        """
        csv_files = sorted(Path(folder).glob("*.csv"))
        print(column_variables_to_text(csv_files) if csv_files else f"No csv files in {folder}")

    def _reset_build_folder(self) -> None:
        """Delete the whole build folder and create it empty again.

        Only folders that pemlab created (they hold a marker file) or empty ones are deleted,
        so a wrong path like Project("data") cannot wipe other files.
        """
        folder = self.build_folder
        if folder.exists():
            if any(folder.iterdir()) and not (folder / _BUILD_MARKER).exists():
                raise FileExistsError(
                    f"'{folder}' ist nicht leer und wurde nicht von pemlab angelegt. "
                    "Lösche den Ordner einmal selbst oder wähle einen anderen Build-Ordner."
                )
            shutil.rmtree(folder, **{_RMTREE_ERROR_ARGUMENT: _clear_read_only_and_retry})
        folder.mkdir(parents=True)
        (folder / _BUILD_MARKER).touch()

    def build(self) -> None:
        """Empty the build folder, then write every artifact into build/<kind>/<name>/."""
        self._reset_build_folder()
        for artifact in self._artifacts.values():
            folder = self.build_folder / artifact.kind / artifact.name
            folder.mkdir(parents=True, exist_ok=True)  # a LaTeX auto-build may have made it
            tex_folder = f"{self.tex_prefix}/{artifact.kind}/{artifact.name}"
            artifact.write(folder, tex_folder)
