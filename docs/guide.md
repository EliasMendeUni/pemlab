# User guide

This page explains the ideas behind pemlab. The {doc}`tutorial` shows them in action.

## The workflow

An analysis has three steps, all inside one {class}`~pemlab.Project`:

1. **Edit**: load a raw CSV file and add or change columns. The file itself is never modified.
2. **Analyse**: plot columns and fit functions to them.
3. **Build**: `lab.build()` writes tables, plots and calculations into the build folder.

```python
lab = Project("build")                       # set the build folder once
table = lab.edit_csv("data/measurement.csv")  # 1. edit
analysis = lab.analysis(table)                # 2. analyse
lab.build()                                   # 3. build
```

## The build folder

`lab.build()` first **deletes the whole build folder** and then writes everything again. Files
that your script no longer produces disappear.

- pemlab only deletes folders that it created itself (they contain a marker file
  `.pemlab-build`) or that are empty. `Project("data")` on a folder with your own files stops
  with an error instead of deleting them.
- Everything gets its own folder, `build/<kind>/<name>/`, and its files carry the same name:

  ```text
  build/
    data/resistor/        resistor.csv, resistor.calc.json, resistor.tex
    plots/ohms_law/       ohms_law.pdf, ohms_law.png, ohms_law.tex
    tables/resistor/      resistor.tex
  ```

- Creating something with the same kind and name twice replaces the earlier one. Re-running a
  notebook cell therefore does not create duplicates.

## Column names and units

A column name consists of a name and, in square brackets, the unit: `U [V]`, `I [mA]`,
`$R_i$ [\Omega]`.

- In **formulas** you use the name *without* the unit: `"U / I"`.
- Math is allowed in names: `$R_i$` is typeset as math, and `\Omega` is turned into math
  automatically (so is the unit `Ohm`).
- A name without brackets means "no unit", for example the dimensionless gain `H`.
- The part before the bracket must be unique in a table. `I [mA]` and `I [A]` cannot both
  exist, give one of them another name (or use `replace_column`).

The same names appear in the tables, on the plot axes and in the calculations, so the report stays
consistent.

## Calculations

All of these methods record what they did. The records are written next to the CSV file and
end up in the LaTeX output.

| Method | Purpose |
| --- | --- |
| `add_column(name, formula, decimals=None)` | new column from a formula |
| `replace_column(old, new, formula, decimals=None)` | change a column in place |
| `add_uncertainty(name, formula, sigmas=None, decimals=None)` | uncertainty of a formula |

Formulas are written like Python: `"U * I"`, `"sqrt(U**2 + I**2)"`, `"2 * pi * f"`.
Available functions are `sqrt`, `exp`, `log`, `sin`, `cos`, `tan` and so on.

`decimals` rounds the stored values. Later calculations use the rounded values.

### Uncertainties

`add_uncertainty` applies Gaussian error propagation,

$$\sigma_f = \sqrt{\sum_i \left(\frac{\partial f}{\partial x_i}\,\sigma_{x_i}\right)^2}$$

The derivatives are computed **analytically** (with sympy), and the resulting formula is part of
the report.

The uncertainty of a quantity `X` is taken from the column with the symbol `sigma_X`
(`sigma_X [V]` or `$\sigma_X$ [V]`). If there is no such column, pass it explicitly:

```python
table.add_uncertainty("sigma_P [W]", "U * I", sigmas={"U": 0.01, "I": 2e-5})
```

A value is a constant (for example the accuracy of a device), a string is the name of a column.
Use `0` for quantities that are exact. Leaving a quantity out raises an error, so a typo cannot
silently make a value exact.

```{note}
The propagation assumes **independent** uncertainties. A quantity that appears several times in
a formula is treated as one quantity.
```

## Plots and regression

{meth}`~pemlab.Analysis.make_PlotData` selects columns by their full name, including the unit:

```python
data = analysis.make_PlotData("I [A]", "U [V]", "sigma_U [V]")  # x, y, y-uncertainty
```

The uncertainty is optional. Without it the fit is unweighted and there is no chi-squared.

- {meth}`~pemlab.Analysis.plot_data` plots only the measured points.
- {meth}`~pemlab.Analysis.regression` fits a function and plots data and fit.

A fit function has `x` as first argument, the parameters after it, and one `return` line:

```python
def ohm(x, R):
    return R * x
```

Because the expression is in a single `return` line, pemlab can show it in the report. For
nonlinear functions pass start values with `p0=[...]`.

The result of `regression` is a {class}`~pemlab.fit.FitResult` with the parameters, their
uncertainties and chi-squared per degree of freedom. The same numbers are in the LaTeX output.

## Using the result in LaTeX

Every table and every plot is **one LaTeX float**: the figure or table, its caption, and below
it in small type the fit results and the calculations that were used. Because they are in the
same float, nothing moves away from its table or plot. The floats use the placement `[H]`
(package `float`), so they stay exactly where you write the `\input`.

```latex
\input{build/data/resistor/resistor}        % edited table with its calculations
\input{build/plots/ohms_law/ohms_law}       % plot, fit result and calculations
\input{build/tables/resistor/resistor}      % table of the raw data
```

Paths are relative to the folder in which you compile the report. If your report lies in
another folder than the one in which you run Python, tell pemlab the path from the report to
the build folder:

```python
lab = Project("build", tex_prefix="../build")
```

Your own caption for a plot is passed as LaTeX: `caption=r"Voltage over current of $R_1$"`.
