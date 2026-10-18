# pemlab

**pemlab** turns measurement data from physics and electronics lab courses into finished pieces
for your LaTeX report: tables, plots with regression, and the calculations behind every derived
column, including uncertainties.

You describe the analysis in a short Python script or notebook. pemlab writes everything into
one build folder, which you include in your report with `\input`.

## What it does

- **Edit raw data** without touching the CSV files: add columns from formulas, change units,
  round values.
- **Propagate uncertainties** with Gaussian error propagation. The derivatives are computed
  analytically, and the formulas are written into the report.
- **Fit functions** to your data (least squares, with y-uncertainties and chi-squared) and plot
  data and fit together.
- **Document everything**: every table and plot comes with the calculations that were used, in
  the same LaTeX float, so nothing drifts away from its table or figure.
- **One build**: `lab.build()` rebuilds the whole build folder, and files you no longer need
  disappear.

## Installation

pemlab needs Python 3.10 or newer. A fresh environment is recommended:

```bash
conda create -n praktikum python=3.13
conda activate praktikum
pip install git+https://github.com/EliasMendeUni/pemlab.git
```

For development (changes to the source take effect immediately):

```bash
git clone https://github.com/EliasMendeUni/pemlab.git
cd pemlab
pip install -e ".[dev]"
```

Your LaTeX report needs these packages: `graphicx`, `booktabs`, `siunitx` and `float`.

## A first example

```python
from pemlab import Project

lab = Project("build")

table = lab.edit_csv("data/resistor.csv", name="resistor")   # columns "U [V]", "I [mA]"
table.replace_column("I [mA]", "I [A]", "I * 1e-3")           # change a column in place
table.add_uncertainty("sigma_U [V]", "U", sigmas={"U": 0.01})  # device accuracy

analysis = lab.analysis(table)
data = analysis.make_PlotData("I [A]", "U [V]", "sigma_U [V]")


def ohm(x, R):
    return R * x


analysis.regression("ohms_law", ohm, data)   # fit, plot and results
lab.build()
```

Then include the result in your report:

```latex
\input{build/plots/ohms_law/ohms_law}
```

## Documentation

The documentation with a complete tutorial is at
<https://eliasmendeuni.github.io/pemlab/>.

## Status

Early development (v0.1.0). The API is not stable yet.

## License

MIT, see the [LICENSE](https://github.com/EliasMendeUni/pemlab/blob/main/LICENSE) file.
