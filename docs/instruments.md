# Measuring with pyvisa

The module `pemlab.instruments` helps to take the measurements themselves. Its results are CSV
files in the format that `lab.edit_csv(...)` reads. It needs `pyvisa`:

```bash
pip install "pemlab[instruments]"
```

The commands follow the Rigol series of the lab (DM3000 multimeters, DP800 supplies, DG function
generators, DS1000Z oscilloscopes). Other instruments need other commands, the idea stays the same.

## Find the instruments

`find_instruments()` lists all connected instruments with their address, asks each one for
`*IDN?` and prints the code that opens them. The variable names follow the kind of instrument
(`dmm_1`, `source_1`, `awg_1`, `scope_1`). Copy the block into your script and delete the call.

```python
from pemlab.instruments import find_instruments

find_instruments()
```

```text
TCPIP::141.48.16.191::INSTR  RIGOL TECHNOLOGIES,DM3068,DM3O1,00.01
TCPIP::141.48.16.192::INSTR  RIGOL TECHNOLOGIES,DP832,DP8C1,00.01

# --- copy into your script ---
import pyvisa
from pemlab.instruments import PowerSupply

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
from pemlab.instruments import measure_current, measure_resistance, measure_voltage

voltage = measure_voltage(dmm_1, range=1)      # DC, range 1 V
current = measure_current(dmm_1, ac=True)      # AC
resistance = measure_resistance(dmm_1, four_wire=True)
```

For temperatures with a **Pt100** (or Pt1000, `r0=1000`) the resistance is measured and
converted with the standard curve (IEC 60751):

```python
from pemlab.instruments import measure_temperature_pt100

temperature = measure_temperature_pt100(dmm_1)   # in degrees Celsius
```

## Power supply, function generator, oscilloscope

```python
source_1.settings(voltage=1.1, current=0.1, channel=1)
with source_1.output(channel=1):     # on inside the block, off again afterwards (also after errors)
    ...

awg_1.settings("sine", frequency=1000, amplitude=2, offset=0)
awg_1.on()

scope_1.measure("vpp", channel=1)    # also "vrms", "freq", "period", ...
time, voltage = scope_1.read_waveform(channel=1)
scope_1.screenshot("data/scope.png")
```

`source_1.on()` and `source_1.off()` switch the output without a `with` block.

## Take a series and save it as csv

`measure_series` sets a value, waits, measures and stores the row:

```python
from pemlab.instruments import measure_series

log = measure_series(
    [1, 2, 3, 4, 5],                                       # set values in V
    lambda voltage: source_1.settings(voltage, 0.1),
    lambda: measure_current(dmm_1),
    columns=["U [V]", "I [A]"],                            # set value first, then the measured ones
    settle=1.0,                                            # seconds to wait after setting
)
log.save("data/measurements/resistor.csv")
```

Without a series, build the table yourself with `MeasurementLog`:

```python
from pemlab.instruments import MeasurementLog, measure_repeated

log = MeasurementLog("t [s]", "T [degC]")
log.add(0, measure_temperature_pt100(dmm_1))
log.save("data/measurements/temperature.csv")

values = measure_repeated(lambda: measure_voltage(dmm_1), n=10, wait=0.2)  # for a mean
```

The saved CSV is the starting point of the analysis: `lab.edit_csv("data/measurements/resistor.csv")`.
