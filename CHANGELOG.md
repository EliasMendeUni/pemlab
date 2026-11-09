# Changelog

## [Unreleased]

### Changed
- The measurement code is its own package, `pemlab-instruments` (folder `instruments/`, import
  `pemlab_instruments`, Python 3.8 or newer, no dependency on pemlab). `pemlab.instruments` and the
  `instruments` extra are gone; `LivePlot` takes a `LiveStyle` instead of `PointStyle`/`LayoutStyle`;
  `fit_exponential` is `pemlab.fit.fit_exponential`
- `add_column`, `replace_column` and `add_uncertainty` take a function (lambda or def, numpy allowed)
  as well as a formula text; the report shows the expression of a single-expression function
- `Project(..., raw_data_folder=...)`: `tables_from_folder` is now `create_latex_tables_from_raw_data()`,
  it includes subfolders and the .tex files get the folder structure of the csv files
  (`build/tables/<subfolder>/<name>.tex`); `column_names_from_folder` is now `find_columns()`
- Plots are drawn when they are written; figures are closed afterwards
- Documentation in two parts, examples are workflow notebooks

### Added
- `add_uncertainty`: an uncertainty in `sigmas` can be a function of the columns (e.g. the accuracy
  of a multimeter from the reading)
- Fits can include the uncertainty of x: `make_PlotData(x, y, y_sigma, x_sigma)`, effective variance method
  (optional, x error bars are drawn too)
- `Analysis.make_PlotData(..., x_range=(low, high), y_range=(low, high))` selects the points of a plot or
  fit by intervals (`None` = open side)
- `Project.Visualize(name)`: any number of data sets, fits (`Analysis.make_regression`) and functions
  in one plot

### Added
- `pemlab.instruments`: `Sweep`, `LinSweep`, `LogSweep`, `Timed` (measure inside a `with` block,
  Ctrl+C ends cleanly, csv written row by row), `LivePlot` (updated during the measurement, same
  `PointStyle`/`LayoutStyle`) and `AFG1022` (Tektronix function generator)
- Project skeleton (src layout, pyproject.toml, MIT license)
- `Project`: one build folder for everything, `build()` rebuilds it from scratch
- `EditCsv`: add, replace and round columns from formulas; every calculation is recorded
- Analytic Gaussian error propagation (`add_uncertainty`) with LaTeX output of the formulas
- `Analysis`: `plot_data` and `regression` (least squares with uncertainties and chi-squared)
- Tables and plots as LaTeX floats that include their calculations
- `show=True` for `add_column`, `replace_column` and `add_uncertainty`: list a calculation under
  "Calculations" in the report (default: not listed)
- `NumberStyle`: how numbers are shown (decimals of table cells, digits of uncertainties, switch
  to `1e-3` notation below `sci_below` and from `sci_above`). Only the display is rounded, the
  csv keeps all digits. `numbers=` of `Project`, `edit_csv`, `table`, `tables_from_folder`,
  `add_column`, `replace_column`, `add_uncertainty`, `regression` and `mean`
- Formulas of `add_column` etc. use the column names as variables (`"U * I"` for the columns
  `U [V]` and `I [A]`); `U="..."` is only needed for another name
- `EditCsv.set_column`: a column from your own values (e.g. fit results) that the table shows
  with `numbers` like a computed column
- Regression formulas with a math column on the x axis (`\frac{1}{R_x}`) are shown correctly
- `Analysis.mean`: mean (optionally weighted) with standard deviation, uncertainty of the mean
  and deviation from a reference value, also as a LaTeX table
- `Project.column_names_from_folder`: prints a Python variable for every CSV column
- `pemlab.instruments` (extra `pemlab[instruments]`): `find_instruments` prints the code to open every
  connected VISA instrument, DMM measurements (`measure_voltage`, `measure_current`,
  `measure_resistance`, Pt100 temperature), `PowerSupply`, `FunctionGenerator`, `Oscilloscope`,
  `MeasurementLog` (csv for `lab.edit_csv`) and `measure_series`
- `measure_timeseries` (time column with the real times), `Oscilloscope.stop/run/single/stopped`,
  `FunctionGenerator.output()`, signal helpers `edge_times`, `edge_duration` and `find_peak`,
  and `fit_exponential` for charging and discharging curves
- `PointStyle`, `FitStyle` and `LayoutStyle`: look of the plots (points and error bars, fit
  curve, axes and layout) for one plot (`points=`, `fit=`, `layout=` of `plot_data` and
  `regression`) or for a whole project (`Project(..., points=..., layout=...)`); the default
  markers are smaller than before
- Sphinx documentation (Furo theme) with a tutorial notebook, deployed to GitHub Pages

### Removed
- `Table`, `LinearFit` and `FitPlot` of the first skeleton (replaced by the classes above)
