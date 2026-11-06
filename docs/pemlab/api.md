# API reference

## Project

```{eval-rst}
.. autoclass:: pemlab.Project
   :members: edit_csv, analysis, Visualize, table, tables_from_folder, column_names_from_folder, build
```

## Editing CSV files

```{eval-rst}
.. autoclass:: pemlab.EditCsv
   :members: add_column, replace_column, add_uncertainty, set_column, column, save
```

## Analysis

```{eval-rst}
.. autoclass:: pemlab.Analysis
   :members: make_PlotData, make_regression, visualize, plot_data, regression, mean

.. autoclass:: pemlab.Visualize
   :members: add, figure, show

.. autoclass:: pemlab.Regression

.. autoclass:: pemlab.data.PlotData
   :members:

.. autoclass:: pemlab.NumberStyle

.. autoclass:: pemlab.PointStyle

.. autoclass:: pemlab.FitStyle

.. autoclass:: pemlab.LayoutStyle

.. autoclass:: pemlab.fit.FitResult
   :members:

.. autoclass:: pemlab.stats.MeanResult
   :members:
```
