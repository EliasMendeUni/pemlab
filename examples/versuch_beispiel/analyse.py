r"""Example experiment script: builds the tables for the report.

Run in the conda env with pemlab installed: ``python analyse.py``.
Output goes to ./build; include it in LaTeX with ``\input{build/...}``.
"""

from pemlab import Analysis

resistor = Analysis("data/iv_messdaten.csv")
resistor.make_data(0,1,2)
resistor.plot_data()



