"""pemlab: tools for measurement data analysis and lab reports."""

from pemlab.analysis.fit import LinearFit
from pemlab.graphics.plot import FitPlot
from pemlab.tex.tables import Table

__version__ = "0.1.0"

__all__ = ["FitPlot", "LinearFit", "Table"]
