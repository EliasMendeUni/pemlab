r"""Example experiment script: builds the tables for the report.

Run in the conda env with pemlab installed: ``python analyse.py``.
Output goes to ./build; include it in LaTeX with ``\input{build/...}``.
"""

from pemlab import Analysis

resistor = Analysis("examples/versuch_beispiel/data/iv_messdaten.csv")
plot_data = resistor.make_data(0,1,2)
resistor.plot_data(plot_data)



