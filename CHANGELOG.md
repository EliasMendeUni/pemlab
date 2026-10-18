# Changelog

## [Unreleased]

### Added
- Project skeleton (src layout, pyproject.toml, MIT license)
- `Project`: one build folder for everything, `build()` rebuilds it from scratch
- `EditCsv`: add, replace and round columns from formulas; every calculation is recorded
- Analytic Gaussian error propagation (`add_uncertainty`) with LaTeX output of the formulas
- `Analysis`: `plot_data` and `regression` (least squares with uncertainties and chi-squared)
- Tables and plots as LaTeX floats that include their calculations
- Sphinx documentation (Furo theme) with a tutorial notebook, deployed to GitHub Pages

### Removed
- `Table`, `LinearFit` and `FitPlot` of the first skeleton (replaced by the classes above)
