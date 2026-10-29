# API reference

## Project

```{eval-rst}
.. autoclass:: pemlab.Project
   :members:
```

## Editing CSV files

```{eval-rst}
.. autoclass:: pemlab.EditCsv
   :members: add_column, replace_column, add_uncertainty, column, save
```

## Analysis

```{eval-rst}
.. autoclass:: pemlab.Analysis
   :members: make_PlotData, plot_data, regression, mean

.. autoclass:: pemlab.data.PlotData
   :members:

.. autoclass:: pemlab.PointStyle

.. autoclass:: pemlab.FitStyle

.. autoclass:: pemlab.LayoutStyle

.. autoclass:: pemlab.fit.FitResult
   :members:

.. autoclass:: pemlab.stats.MeanResult
   :members:
```

## Instruments

```{eval-rst}
.. autofunction:: pemlab.instruments.find_instruments

.. autofunction:: pemlab.instruments.measure_voltage

.. autofunction:: pemlab.instruments.measure_current

.. autofunction:: pemlab.instruments.measure_resistance

.. autofunction:: pemlab.instruments.measure_temperature_pt100

.. autofunction:: pemlab.instruments.pt100_temperature

.. autoclass:: pemlab.instruments.PowerSupply
   :members:

.. autoclass:: pemlab.instruments.FunctionGenerator
   :members:

.. autoclass:: pemlab.instruments.Oscilloscope
   :members:

.. autoclass:: pemlab.instruments.MeasurementLog
   :members:

.. autofunction:: pemlab.instruments.measure_series

.. autofunction:: pemlab.instruments.measure_repeated

.. autofunction:: pemlab.instruments.measure_timeseries

.. autofunction:: pemlab.instruments.edge_times

.. autofunction:: pemlab.instruments.edge_duration

.. autofunction:: pemlab.instruments.find_peak

.. autofunction:: pemlab.instruments.fit_exponential
```
