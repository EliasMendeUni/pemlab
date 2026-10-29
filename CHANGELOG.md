# Changelog

## [Unreleased]

### Added
- Project skeleton (src layout, pyproject.toml, MIT license)
- `Project`: one build folder for everything, `build()` rebuilds it from scratch
- `EditCsv`: add, replace and round columns from formulas; every calculation is recorded
- Analytic Gaussian error propagation (`add_uncertainty`) with LaTeX output of the formulas
- `Analysis`: `plot_data` and `regression` (least squares with uncertainties and chi-squared)
- Tables and plots as LaTeX floats that include their calculations
- `show=False` for `add_column`, `replace_column` and `add_uncertainty`: leave a calculation out
  of the "Calculations" list in the report
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
