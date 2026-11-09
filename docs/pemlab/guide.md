# User guide

This page explains the ideas behind pemlab (the evaluation). The notebooks {doc}`examples/01_data_and_calculations` and {doc}`examples/02_plots_and_fits` show them in action. The measuring is a separate package, see {doc}`../instruments/guide`.

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
- Everything gets its own folder, `build/<kind>/<name>/`, and its files carry the same name.
  The exception are the raw tables of `lab.create_latex_tables_from_raw_data()`: they have the folder
  structure of the csv files, so `data/circuits/rc.csv` becomes `build/tables/circuits/rc.tex`.

  ```text
  build/
    data/resistor/        resistor.csv, resistor.calc.json, resistor.tex
    plots/ohms_law/       ohms_law.pdf, ohms_law.png, ohms_law.tex
    means/R_mean/         R_mean.tex
    tables/               resistor.tex, circuits/rc.tex
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

  To save typing, `lab.find_columns()` prints one such variable for every column of every CSV
  file in the raw data folder of the project (`Project(..., raw_data_folder="data/measurements")`,
  subfolders included), with a header per file. Run it once at the start, copy the output into
  your script and delete the call again, like `find_instruments()` for the measurement.

  ```text
  # resistor.csv
  U = "U [V]"
  I = "I [mA]"

  # circuits/rc.csv
  f = "f [Hz]"
  U_a = "$U_a$ [V]"
  ```

  The variable name is the column name without unit and math markup. If it is already taken by
  another column, the unit or the file name is appended (`I_A`).

## Calculations

All of these methods record what they did. The records are written next to the CSV file and
end up in the LaTeX output.

| Method | Purpose |
| --- | --- |
| `add_column(name, function)` | new column from a function or formula |
| `replace_column(old, new, function)` | change a column in place |
| `add_uncertainty(name, function, sigmas)` | uncertainty of a function |
| `set_column(name, values)` | column from values you computed yourself (e.g. fit results) |

Each takes the keyword-only options `numbers=None` and `show=False`.

The calculation is a **function** (a `lambda` or a `def`). Its **arguments** are the columns,
named without unit and math markup: `U` is the column `U [V]`, `R_x` is `$R_x$ [$k\Omega$]`.
Inside you can use numpy:

```python
table.add_column(R, lambda U, I: U / I)                                  # "U [V]" and "I [A]"
table.add_column(PHI, lambda dt, f: np.degrees(2 * np.pi * f * dt),      # other names:
                 dt="$\\Delta t$ [s]", f="f [Hz]")                        # argument="column"
```

A formula as **text** works as well (`"U * I"`, `"sqrt(U**2 + I**2)"`, `"2 * pi * f"`) and means
the same.

An argument that is not the name of a column gets its column with a keyword argument, as `dt`
and `f` above. pemlab checks the assignment: an argument without a column, a name that fits
several columns, a column that does not exist and an unused assignment all raise an error that
names the problem.

For the report pemlab writes the function as an equation (`np.degrees(...)` becomes $\varphi =
360\,\Delta t\,f$). That works for a single expression (a lambda, or a `def` whose last line is
the `return`). Any other function is computed all the same, and the report shows its source text
instead. `add_uncertainty` needs a single expression because it differentiates it.

`show=True` lists a calculation under "Calculations" in the report. By default it is left out,
because most columns are trivial steps like a unit conversion. The column is computed and
stored either way.

```python
table.replace_column(I_mA, I, lambda I: I * 1e-3)   # "I" is the old column "I [mA]"
```

`numbers` is how the column is shown in the table, see {ref}`number-style`. The stored values are
never rounded.

```{note}
The names `name`, `formula`, `sigmas`, `numbers`, `show`, `old_name` and `new_name` belong to the
methods and cannot be used as argument names of the function.
```

### Uncertainties

`add_uncertainty` applies Gaussian error propagation,

$$\sigma_f = \sqrt{\sum_i \left(\frac{\partial f}{\partial x_i}\,\sigma_{x_i}\right)^2}$$

The derivatives are computed **analytically** (with sympy), and the resulting formula is part of
the report.

`sigmas` gives the uncertainty of **every** argument of the function. A number is a constant (for
example the accuracy of a device), a string is the name of a column with the uncertainties. Use
`0` for quantities that are exact:

```python
table.add_uncertainty(SIGMA_P, lambda U, I: U * I, {"U": 0.01, "I": SIGMA_I})
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

The uncertainties are optional. Without any the fit is unweighted and there is no chi-squared.

`x_sigma` is the same for the uncertainty of x (`make_PlotData(f, U, "sigma_U [V]", "sigma_f [Hz]")`).
Both become error bars, and a regression uses them:

- with `y_sigma` the points are weighted, and the errors and chi-squared are absolute;
- with `x_sigma` the uncertainty of x is **included in the errors of the fit** by the *effective
  variance* method: every point gets $\sigma^2 = \sigma_y^2 + \bigl(f'(x)\,\sigma_x\bigr)^2$,
  with the slope $f'$ of the fitted curve. The weights depend on the parameters, so the fit is
  repeated until they no longer change. The report says that the x uncertainties were included.

Either one is optional. Leave `x_sigma` out and the x values count as exact.

`x_range` and `y_range` keep only the points inside an interval `(low, high)` (both ends
included, `None` leaves a side open). Use them to fit a part of the measurement, for example the
slope of a filter in the stop band:

```python
flank = analysis.make_PlotData(F, A_DB, x_range=(100, 400))    # 100 Hz <= f <= 400 Hz
top = analysis.make_PlotData(F, A_DB, y_range=(-3, None))      # only points above -3 dB
```

An error bar column (`y_sigma`) is cut along with the points. If no point is left, you get an
error.

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

(visualize)=
### Several data sets in one plot

`plot_data` and `regression` make one plot from one data set. For more, create a
{class}`~pemlab.Visualize` and `add` what should be in it, as often as you like:

```python
plot = lab.Visualize("amplitude", layout=LayoutStyle(xscale="log"))   # build/plots/amplitude

plot.add(data_low, points=PointStyle(label="low-pass"))               # measured points
plot.add(analysis.make_regression(highpass, data_high, p0=[500]),     # points and fit curve
         points=PointStyle(label="high-pass"), fit=FitStyle(color="C1"))
plot.add(lambda f: 1 / np.sqrt(2), fit=FitStyle(label="-3 dB", linestyle=":"))   # a function
plot                                                                  # a notebook shows it
```

What you can `add`:

| `plot.add(...)` | draws | looks |
| --- | --- | --- |
| `analysis.make_PlotData(x, y)` | measured points (error bars with `y_sigma`) | `points` |
| `analysis.make_regression(function, data)` | the points of the data and the fit curve | `points`, `fit` |
| a function `f(x)` (a lambda with numpy) | the curve; `x=(low, high)` sets the range | `fit` |

The layers are drawn in the order they are added. Data from different tables can be mixed. The
`layout` of the `Visualize` is the look of the whole plot. `points` and `fit` of an `add`
replace the defaults of the project for this layer (`FitStyle(label=...)` is the legend text). Set
a `PointStyle(label=...)` for every set of points, otherwise they are all "Messdaten" in the
legend. The legend appears by default as soon as there is more than one layer.

The fit results of all regressions and the calculations behind all columns that are used end up
in the one LaTeX float of the plot. `regression.result` holds the parameters and uncertainties
of a fit (`make_regression` prints them too). `analysis.plot_data(...)` and
`analysis.regression(...)` are shortcuts for a `Visualize` with a single layer.

(number-style)=
## Numbers in tables and results

Only the **display** is rounded. The csv files and all calculations keep every digit. A
{class}`~pemlab.NumberStyle` sets how numbers are shown. Every field has a default:

```python
from pemlab import NumberStyle, Project

lab = Project("data/_build", numbers=NumberStyle(error_digits=1))   # all numbers of the project
table.add_column(R, "U / I", numbers=NumberStyle(decimals=1))        # one column of a table
analysis.regression("fit", line, data, numbers=NumberStyle(sci_below=1e-3))  # one result
```

| Field | Meaning | Default |
| --- | --- | --- |
| `decimals` | decimals of table cells (`None`: the digits of the csv) | `None` |
| `error_digits` | significant digits of an uncertainty; the value gets the same place | 2 |
| `significant_digits` | digits of a number without uncertainty (and of computed columns) | 4 |
| `sci_below` | numbers with a smaller absolute value are written as `1.5e-3` | 0.01 |
| `sci_above` | numbers from this value on are written as `1.5e5` | 100000 |

Fit results and means get the same exponent for value and uncertainty: `(2.848 ± 0.004)e-9`. A
column computed by `add_column` or `add_uncertainty` has no precision of its own, so a table shows
it with `significant_digits` unless you give it a `decimals`. Raw columns and unit conversions
(`replace_column`) keep the digits of the csv. A style of a single call replaces the style of the
project completely. `res.values` and `res.errors` of a fit are always exact.

## Look of the plots

Three small classes set how a plot looks. Every field has a default, so you only name what you
want to change:

- {class}`~pemlab.PointStyle`: measured points and error bars (marker, size, color, alpha, ...)
- {class}`~pemlab.FitStyle`: the fit curve (color, line width, line style, label); only plots with
  a fit use it
- {class}`~pemlab.LayoutStyle`: figure and axes (size, labels, title, log scales, limits, grid,
  legend, font size, png resolution)

```python
from pemlab import FitStyle, LayoutStyle, PointStyle

points = PointStyle(marker_size=2, marker_alpha=0.5)
log_x = LayoutStyle(xscale="log", figsize=(6, 3.5))

analysis.regression("ohms_law", ohm, data, points=points, layout=log_x)  # one plot
lab = Project("data/_build", points=points)  # all plots of the project
```

`Project` and `Analysis` take the same three arguments as a default for all their plots. An
argument of a single plot replaces that one part and leaves the others as they are. So you can
keep the points of the project and change only the layout of one plot. `plot_data` takes
`points` and `layout` (it has no fit curve).

`None` means automatic: axis labels come from the column names, colors from matplotlib's color
cycle. Make a changed copy of a style with `dataclasses.replace(log_x, grid=False)`.

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
\input{build/tables/resistor}               % table of the raw data
```

Paths are relative to the folder in which you compile the report. If your report lies in
another folder than the one in which you run Python, tell pemlab the path from the report to
the build folder:

```python
lab = Project("build", tex_prefix="../build")
```

Your own caption for a plot is passed as LaTeX: `caption=r"Voltage over current of $R_1$"`.
