r"""Example experiment script: builds tables and plots for the report.

Run in the conda env with pemlab installed: ``python analyse.py``.
Output goes to ./build; include it in LaTeX with ``\input{build/plots/<name>/plot}``.
"""

import matplotlib.pyplot as plt

from pemlab import Project

lab = Project("examples/versuch_beispiel/build")

# 1. edit: raw data -> new columns (the calculations are documented automatically)
iv = lab.edit_csv("examples/versuch_beispiel/data/iv_messdaten.csv", name="iv")
iv.add_uncertainty("sigma_U [V]", "U", sigmas={"U": 0.01})  # device accuracy of the voltmeter

# 2. analysis: plot and regression
analysis = lab.analysis(iv)
data = analysis.make_PlotData(x="I [A]", y="U [V]", y_sigma="sigma_U [V]")


def ohm(x, R):
    return R * x


analysis.regression("iv_regression", ohm, data)

# 3. tables of the raw data
lab.tables_from_folder("examples/versuch_beispiel/data")

# 4. write everything into the build folder
lab.build()
plt.show()
