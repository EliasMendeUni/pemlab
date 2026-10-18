"""Sphinx configuration for the pemlab documentation."""

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

# The tutorial notebook is executed locally; its stored outputs are shown as they are.
nb_execution_mode = "off"
myst_enable_extensions = ["colon_fence", "dollarmath"]

autodoc_member_order = "bysource"

exclude_patterns = ["_build", "pemlab_build", "**/.ipynb_checkpoints"]
