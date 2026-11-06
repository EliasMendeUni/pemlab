# API reference: pemlab-instruments

## Finding and opening

```{eval-rst}
.. autofunction:: pemlab_instruments.find_instruments
```

## Multimeter

```{eval-rst}
.. autofunction:: pemlab_instruments.measure_voltage

.. autofunction:: pemlab_instruments.measure_current

.. autofunction:: pemlab_instruments.measure_resistance

.. autofunction:: pemlab_instruments.measure_temperature_pt100

.. autofunction:: pemlab_instruments.pt100_temperature
```

## Instruments

```{eval-rst}
.. autoclass:: pemlab_instruments.AFG1022
   :members:

.. autoclass:: pemlab_instruments.FunctionGenerator
   :members:

.. autoclass:: pemlab_instruments.PowerSupply
   :members:

.. autoclass:: pemlab_instruments.Oscilloscope
   :members:
```

## Sweeps and live plots

```{eval-rst}
.. autoclass:: pemlab_instruments.Sweep
   :members:

.. autoclass:: pemlab_instruments.LinSweep

.. autoclass:: pemlab_instruments.LogSweep

.. autoclass:: pemlab_instruments.Timed

.. autoclass:: pemlab_instruments.LivePlot
   :members:

.. autoclass:: pemlab_instruments.LiveStyle
```

## Series and tables

```{eval-rst}
.. autoclass:: pemlab_instruments.MeasurementLog
   :members:

.. autofunction:: pemlab_instruments.measure_series

.. autofunction:: pemlab_instruments.measure_repeated

.. autofunction:: pemlab_instruments.measure_timeseries
```

## Signals

```{eval-rst}
.. autofunction:: pemlab_instruments.edge_times

.. autofunction:: pemlab_instruments.edge_duration

.. autofunction:: pemlab_instruments.find_peak
```
