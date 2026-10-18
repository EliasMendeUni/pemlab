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
    means/R_mean/         R_mean.tex
    tables/resistor/      resistor.tex
  ```

- Creating something with the same kind and name twice replaces the earlier one. Re-running a
  notebook cell therefore does not create duplicates.

## Column names and units

A column name is just a label. By convention it consists of a name and, in square brackets, the
unit: `U [V]`, `I [mA]`, `$R_i$ [\Omega]`. The same text appears in the tables, on the plot axes
and in the calculations.

- Math is allowed: `$R_i$` is typeset as math, and `\Omega` is turned into math automatically
  (so is the unit `Ohm`).
- A name without brackets means "no unit", for example the dimensionless gain `H`.
- pemlab does **not** derive anything from the names. Everywhere a column is needed, you pass
  its full name. Write each name once in your script and reuse the variable:

  ```python
  U = "U [V]"
  I_mA = "I [mA]"
  R = r"$R$ [\Omega]"
  ```

  To save typing, `lab.column_names_from_folder("data")` prints one such variable for every
  column of every CSV file in a folder, grouped by file. Copy the output into your script and
  delete the call again.

  ```text
  # resistor.csv
  U = "U [V]"
  I = "I [mA]"
  ```

  The variable name is the column name without unit and math markup. If it is already taken by
  another column, the unit or the file name is appended (`I_A`).

## Calculations

All of these methods record what they did. The records are written next to the CSV file and
end up in the LaTeX output.

| Method | Purpose |
| --- | --- |
| `add_column(name, formula, **columns)` | new column from a formula |
| `replace_column(old, new, formula, **columns)` | change a column in place |
| `add_uncertainty(name, formula, sigmas, **columns)` | uncertainty of a formula |

Each takes the keyword-only options `decimals=None` and `show=True`.

A formula is written like Python: `"U * I"`, `"sqrt(U**2 + I**2)"`, `"2 * pi * f"`. Available
functions are `sqrt`, `exp`, `log`, `sin`, `cos`, `tan` and so on. The **variables** of the
formula are local names. You assign each of them a column with a keyword argument:

```python
table.add_column(R, "U / I", U=U, I=I)   # variable U is the column "U [V]", ...
```

pemlab checks the assignment. A variable without a column, a column that does not exist and an
unused assignment all raise an error that names the problem.

`decimals` rounds the stored values. Later calculations use the rounded values.

`show=False` keeps a calculation out of the "Calculations" list in the report, for example a
trivial unit conversion. The column is still computed and stored.

```python
table.replace_column(I_mA, I, "I_mA * 1e-3", I_mA=I_mA, show=False)
```

`replace_column` uses the old column like any other, so assign it to a variable as well.

```{note}
The names `name`, `formula`, `sigmas`, `decimals`, `show`, `old_name` and `new_name` belong to the
methods and cannot be used as variable names in a formula.
```

### Uncertainties

`add_uncertainty` applies Gaussian error propagation,

$$\sigma_f = \sqrt{\sum_i \left(\frac{\partial f}{\partial x_i}\,\sigma_{x_i}\right)^2}$$

The derivatives are computed **analytically** (with sympy), and the resulting formula is part of
the report.

`sigmas` gives the uncertainty of **every** variable of the formula. A number is a constant (for
example the accuracy of a device), a string is the name of a column with the uncertainties. Use
`0` for quantities that are exact:

```python
table.add_uncertainty(SIGMA_P, "U * I", {"U": 0.01, "I": SIGMA_I}, U=U, I=I)
```

A missing or superfluous entry raises an error, so a typo cannot silently make a value exact.

```{note}
The propagation assumes **independent** uncertainties. A quantity that appears several times in
a formula is treated as one quantity.
```

## Plots and regression

{meth}`~pemlab.Analysis.make_PlotData` selects columns by their full name:

```python
data = analysis.make_PlotData(I, U, SIGMA_U)  # x, y, y-uncertainty
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

## Mean of a series

{meth}`~pemlab.Analysis.mean` gives the mean of a column with its spread and uncertainty:

```python
analysis.mean("R_mean", R, reference=470)
```

```text
n = 10
mean = 469.78 ± 0.43
standard deviation = 1.35
deviation from 470 = -0.22, -0.047 %, 0.52 sigma
```

- Without `sigma`, the result is the arithmetic mean, the sample standard deviation $s$ and the
  standard error $s/\sqrt{n}$ as uncertainty of the mean.
- With `sigma="<uncertainty column>"` it is the **weighted mean** with the uncertainty
  $1/\sqrt{\sum 1/\sigma_i^2}$ and the reduced chi-squared. A value near 1 means that the
  values agree within their uncertainties.
- `reference` (for example a literature value) adds the deviation from it, also in percent and in
  units of the uncertainty of the mean.

The result is also written to `build/means/<name>/<name>.tex` as a table, together with the
calculations that were used for the column.

## Using the result in LaTeX

Every table and every plot is **one LaTeX float**: the figure or table, its caption, and below
it in small type the fit results and the calculations that were used. Because they are in the
same float, nothing moves away from its table or plot. The floats use the placement `[H]`
(package `float`), so they stay exactly where you write the `\input`.

```latex
\input{build/data/resistor/resistor}        % edited table with its calculations
\input{build/plots/ohms_law/ohms_law}       % plot, fit result and calculations
\input{build/means/R_mean/R_mean}           % mean of a column
\input{build/tables/resistor/resistor}      % table of the raw data
```

Paths are relative to the folder in which you compile the report. If your report lies in
another folder than the one in which you run Python, tell pemlab the path from the report to
the build folder:

```python
lab = Project("build", tex_prefix="../build")
```

Your own caption for a plot is passed as LaTeX: `caption=r"Voltage over current of $R_1$"`.
