r"""Example experiment script: builds the table and fit plot for the report.

Run in the conda env with pemlab installed: ``python analyse.py``.
Output goes to ./build; include it in LaTeX with ``\input{build/...}``
and ``\includegraphics{build/...}``.
"""

from pathlib import Path

from pemlab import FitPlot, LinearFit, Table

HERE = Path(__file__).parent
DATA = HERE / "data" / "iv_messdaten.csv"
BUILD = HERE / "build"

# Table
Table.from_csv(DATA).to_tex(
    BUILD / "tab_iv.tex",
    caption=r"Measured $I$--$U$ characteristic.",
    label="tab:iv",
    header=[r"$U$ (V)", r"$I$ (A)", r"$\sigma_I$ (A)"],
    decimals={"U [V]": 3, "I [A]": 5, "sigma_I [A]": 5},
)

# Linear fit (columns by name or position, e.g. x=0, y=1, sigma_y=2)
fit = LinearFit.from_csv(DATA, x="U [V]", y="I [A]", sigma_y="sigma_I [A]")
print(fit)
R, R_err = fit.inverse_slope()
print(f"R = {R:.1f} +- {R_err:.1f} Ohm")

# Plot
FitPlot(
    fit,
    xlabel="$U$ (V)",
    ylabel="$I$ (A)",
    fit_label=rf"Fit: $R$ = {R:.1f} $\Omega$",
).save(BUILD / "iv_fit.pdf")

print(f"Output written to {BUILD}")
