r"""Example experiment script: builds the tables for the report.

Run in the conda env with pemlab installed: ``python analyse.py``.
Output goes to ./build; include it in LaTeX with ``\input{build/...}``.
"""

from pemlab import Analysis, EditCsv, LatexConverter

resistor = Analysis("examples/versuch_beispiel/data/iv_messdaten.csv")
plot_data = resistor.make_PlotData(1,0,2)

def ohm(x,R):
    return R * x

resistor.plot_regression(ohm, plot_data)

converter = LatexConverter("examples/versuch_beispiel/build/raw_data")
converter.build_tables_from_folder("examples/versuch_beispiel/data")