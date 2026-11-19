# Measuring with pyvisa

`pemlab-instruments` takes the measurements: it controls the instruments with pyvisa and writes
CSV files. It is independent of the evaluation package `pemlab`, runs on **Python 3.8 or newer**
and needs only numpy, matplotlib and pyvisa. The CSV files are what `lab.edit_csv(...)` of
{doc}`pemlab <../pemlab/guide>` reads. The notebook {doc}`examples/01_measuring` runs all of this
without hardware.

```bash
pip install pemlab-instruments
```

See {doc}`../installation` for the installation on computers without git or with other packages
that must not change.

The commands follow the instruments of the lab (Tektronix AFG1022 function generator, Rigol DM3000
multimeters, DP800 supplies, DG function generators, DS1000Z oscilloscopes). Other instruments
need other commands, the idea stays the same.

## Find the instruments

`find_instruments()` lists all connected instruments with their address, asks each one for
`*IDN?` and prints the code that opens them. The variable names follow the kind of instrument
(`dmm_1`, `source_1`, `awg_1`, `scope_1`). Copy the block into your script and delete the call.

```python
from pemlab_instruments import find_instruments

find_instruments()
```

```text
TCPIP::141.48.16.191::INSTR  RIGOL TECHNOLOGIES,DM3068,DM3O1,00.01
TCPIP::141.48.16.192::INSTR  RIGOL TECHNOLOGIES,DP832,DP8C1,00.01

# --- copy into your script ---
import pyvisa
from pemlab_instruments import PowerSupply

rm = pyvisa.ResourceManager()

# RIGOL TECHNOLOGIES,DM3068,DM3O1,00.01
dmm_1_add = 'TCPIP::141.48.16.191::INSTR'
dmm_1 = rm.open_resource(dmm_1_add)

# RIGOL TECHNOLOGIES,DP832,DP8C1,00.01
source_1_add = 'TCPIP::141.48.16.192::INSTR'
source_1 = PowerSupply(rm.open_resource(source_1_add))
```

## Multimeter

The functions take the opened resource and **return** the value (in V, A or Ohm):

```python
from pemlab_instruments import measure_current, measure_resistance, measure_voltage

voltage = measure_voltage(dmm_1, range=1)      # DC, range 1 V
current = measure_current(dmm_1, ac=True)      # AC
resistance = measure_resistance(dmm_1, four_wire=True)
```

For temperatures with a **Pt100** (or Pt1000, `r0=1000`) the resistance is measured and
converted with the standard curve (IEC 60751):

```python
from pemlab_instruments import measure_temperature_pt100

temperature = measure_temperature_pt100(dmm_1)   # in degrees Celsius
```

## Power supply, function generators, oscilloscope

```python
source_1.settings(voltage=1.1, current=0.1, channel=1)
with source_1.output(channel=1):     # on inside the block, off again afterwards (also after errors)
    ...

awg_1.settings("sine", frequency=1000, amplitude=2, offset=0)   # amplitude in Vpp
awg_1.set_frequency(1500)
awg_1.on()

scope_1.measure("vpp", channel=1)    # also "vrms", "freq", "period", ...
time, voltage = scope_1.read_waveform(channel=1)
scope_1.screenshot("data/scope.png")
```

The Tektronix AFG1022 has its own class, `AFG1022(resource, load=50)`, with the same methods;
`FunctionGenerator` is the Rigol DG series.

`source_1.on()` and `source_1.off()` switch the output without a `with` block. The generators
have the same `output()` block:

```python
with awg_1.output():
    ...
```

The scope can be stopped, restarted or armed for a single shot (`scope_1.stop()`,
`scope_1.run()`, `scope_1.single()`). Read a trace inside `stopped()` so that it does not change
while it is transferred:

```python
with scope_1.stopped():
    time, voltage = scope_1.read_waveform(channel=1)
```

## Sweeps with live plot

`LogSweep`, `LinSweep` and `Timed` are context managers. **You write the loop yourself**:
set the instruments, wait, measure, and `sweep.add(...)` stores a row (first the loop value, then
your measured values). Plotting, saving and the kind of sweep are independent of each other.

```python
from pemlab_instruments import AFG1022, LivePlot, LiveStyle, LogSweep, measure_voltage

with LogSweep(10, 20_000, 60, columns=["f [Hz]", "U_e [V]", "U_a [V]"],
              save="data/measurements/hp.csv") as sweep:
    plot = LivePlot(sweep, x="f [Hz]", y=lambda row: row["U_a [V]"] / row["U_e [V]"],
                    style=LiveStyle(xscale="log", xlabel="$f$ [Hz]", ylabel="$|H|$"))
    for f in sweep:
        awg.set_frequency(f)
        sweep.wait(0.3)                                  # waits and keeps the plot responsive
        sweep.add(measure_voltage(dmm_e, ac=True), measure_voltage(dmm_a, ac=True))
plot.show()                                              # keeps the window open
```

- The csv file is written **row by row**, nothing is lost if something goes wrong.
- **Ctrl+C** ends the block cleanly; the rows so far stay in `sweep.log` and in the csv file, and
  the code behind the block runs on. `sweep.interrupted` tells whether it was interrupted.
- `sweep.on_row(callback)` calls your function after every row (printing, checks, more plots).
- `LivePlot` takes a column name or a function of the row (a dict) for `x` and `y`, so the live
  plot can show $|H| = U_a/U_e$ while the file keeps the raw voltages. `LiveStyle` is its look
  (marker, color, scales, labels, limits, ...); `plot.save(path)` saves the current state.
- `Timed(interval, columns, duration)` measures over time: the first column is the **real** time
  since the start. Without `duration` it runs until Ctrl+C. `Sweep(values, columns)` takes any
  iterable, e.g. `itertools.count()` for an endless measurement.

Matplotlib needs an interactive backend for the live window (not `Agg`). In a notebook the plot
appears below the cell.

## Series without a sweep object

`measure_series` sets a value, waits, measures and stores the row:

```python
from pemlab_instruments import measure_series

log = measure_series(
    [1, 2, 3, 4, 5],                                       # set values in V
    lambda voltage: source_1.settings(voltage, 0.1),
    lambda: measure_current(dmm_1),
    columns=["U [V]", "I [A]"],                            # set value first, then the measured ones
    settle=1.0,                                            # seconds to wait after setting
)
log.save("data/measurements/resistor.csv")
```

`measure_timeseries(measure, duration, interval, columns)` does the same over time, and
`MeasurementLog` is the table behind all of it:

```python
from pemlab_instruments import MeasurementLog, measure_repeated

log = MeasurementLog("t [s]", "T [degC]")
log.add(0, measure_temperature_pt100(dmm_1))
log.save("data/measurements/temperature.csv")
arrays = log.to_arrays()                                   # {"t [s]": array, ...}

values = measure_repeated(lambda: measure_voltage(dmm_1), n=10, wait=0.2)  # for a mean
```

The saved CSV is the starting point of the analysis: `lab.edit_csv(...)` with the real file name.

**Date and time are part of every saved file name** (`log.save`, `save=` of a sweep,
`scope.screenshot`, `plot.save`): `data/measurements/resistor.csv` becomes
`data/measurements/resistor_2026-11-10_14-30-05.csv`. A repeated measurement never overwrites an
earlier file; if the name exists already (same second) a counter is added. `save` and `screenshot`
return the real path, a sweep has it as `sweep.save_path`. `timestamp=False` keeps the name as given.

## Evaluate a recorded signal

These functions take the arrays of a trace (for example from `read_waveform`) or of a curve:

```python
from pemlab_instruments import edge_duration, edge_times, find_peak

# pulse and echo: times of the rising edges, choose a level below the smaller echo
t_pulse, t_echo = edge_times(time, voltage, level=0.5)
delay = t_echo - t_pulse

rise = edge_duration(time, voltage)                  # 10 % to 90 % of the amplitude
fall = edge_duration(time, voltage, rising=False)

# resonance curve: position and height of the maximum, refined between the samples
f_res, u_max = find_peak(frequencies, amplitudes)
```

The exponential fit of a charging curve is part of the evaluation package:
`from pemlab.fit import fit_exponential`.
