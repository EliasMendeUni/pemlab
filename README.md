# pemlab

Python package for measurement data analysis and (LaTeX) lab reports in
physical and electronic measurement technology.

> Status: early development (v0.1.0). The API is not stable yet.

## Installation

```bash
pip install git+https://github.com/EliasMendeUni/pemlab.git
```

For development:

```bash
git clone https://github.com/EliasMendeUni/pemlab.git
cd pemlab
pip install -e ".[dev]"
```

## Usage

```python
from pemlab import FitPlot, LinearFit, Table

Table.from_csv("data/measurement.csv").to_tex(
    "build/tab.tex", caption="My measurement.", label="tab:m",
    header=["$U$ (V)", "$I$ (A)"], decimals=3,
)

fit = LinearFit.from_csv("data/measurement.csv", x="U [V]", y="I [A]")
print(fit)
FitPlot(fit, xlabel="$U$ (V)", ylabel="$I$ (A)").save("build/fit.pdf")
```

Include the table with `\input{build/tab.tex}` (requires
`\usepackage{booktabs}`) and the plot with `\includegraphics`.
A full example is in [examples/versuch_beispiel](examples/versuch_beispiel).

## License

MIT, see [LICENSE](LICENSE).
