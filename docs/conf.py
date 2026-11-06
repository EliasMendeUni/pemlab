"""Sphinx configuration for the documentation of pemlab and pemlab-instruments."""

import shutil
import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "instruments" / "src"))

import pemlab  # noqa: E402

project = "pemlab"
author = "Elias Mende"
copyright = "2026, Elias Mende"
release = pemlab.__version__

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

html_theme = "furo"
html_title = "pemlab"

# The example notebooks are executed locally; their stored outputs are shown as they are.
nb_execution_mode = "off"
myst_enable_extensions = ["colon_fence", "dollarmath"]

autodoc_member_order = "bysource"

# The notebooks live next to their package (so they can be run from there). They are copied into
# the docs on every build, a symlink would not survive a checkout on Windows.
for source, target in (
    (root / "examples", Path(__file__).parent / "pemlab" / "examples"),
    (root / "instruments" / "examples", Path(__file__).parent / "instruments" / "examples"),
):
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(
        source, target, ignore=shutil.ignore_patterns("pemlab_build", ".ipynb_checkpoints")
    )

exclude_patterns = [
    "_build",
    "pemlab_build",
    "**/.ipynb_checkpoints",
    "pemlab/examples/data",
    "instruments/examples/data",
]
