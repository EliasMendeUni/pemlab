"""Sphinx configuration for the pemlab documentation."""

import shutil
from pathlib import Path

import pemlab

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

# The example notebooks are executed locally; its stored outputs are shown as they are.
nb_execution_mode = "off"
myst_enable_extensions = ["colon_fence", "dollarmath"]

autodoc_member_order = "bysource"

# The notebooks live in ../examples (so they can be run from there). They are copied next to the
# docs on every build, a symlink would not survive a checkout on Windows.
_examples = Path(__file__).parent.parent / "examples"
_target = Path(__file__).parent / "examples"
shutil.rmtree(_target, ignore_errors=True)
shutil.copytree(_examples, _target, ignore=shutil.ignore_patterns("pemlab_build", ".ipynb_checkpoints"))

exclude_patterns = ["_build", "pemlab_build", "**/.ipynb_checkpoints", "examples/data"]
