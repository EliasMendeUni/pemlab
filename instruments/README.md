# pemlab-instruments

Measure with pyvisa instruments in lab courses: function generators, multimeters, power supplies
and oscilloscopes, sweeps with live plots, and CSV files for the evaluation with
[pemlab](https://github.com/EliasMendeUni/pemlab). It runs on **Python 3.8 or newer**, also on old
lab computers, and does not need pemlab.

```python
import pyvisa

from pemlab_instruments import AFG1022, LivePlot, LiveStyle, LogSweep, measure_voltage

rm = pyvisa.ResourceManager()
awg = AFG1022(rm.open_resource("USB0::0x0699::0x0353::1511374::INSTR"))
dmm_e = rm.open_resource("TCPIP::141.48.16.191::INSTR")
dmm_a = rm.open_resource("TCPIP::141.48.16.192::INSTR")

with LogSweep(70, 3000, 60, columns=["f [Hz]", "U_e [V]", "U_a [V]"],
              save="data/hp.csv") as sweep:          # csv row by row, Ctrl+C ends cleanly
    plot = LivePlot(sweep, x="f [Hz]", y=lambda r: r["U_a [V]"] / r["U_e [V]"],
                    style=LiveStyle(xscale="log"))
    for f in sweep:
        awg.set_frequency(f)
        sweep.wait(0.5)
        sweep.add(measure_voltage(dmm_e, ac=True), measure_voltage(dmm_a, ac=True))
```

## Installation

```bash
python -m pip install .
```

in this folder (after downloading the repository as ZIP), or
`pip install "git+https://github.com/EliasMendeUni/pemlab.git#subdirectory=instruments"`. With
`--no-deps` pip leaves the installed packages alone. The documentation with a notebook is at
<https://eliasmendeuni.github.io/pemlab/>.

## License

MIT
