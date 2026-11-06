# pemlab

Tools for lab courses in physical and electronic measurement technology, in two independent
packages:

| | `pemlab` | `pemlab-instruments` |
| --- | --- | --- |
| for | the **evaluation**: tables, plots, fits, uncertainties, LaTeX | the **measurement**: instruments, sweeps, live plots |
| Python | 3.10 or newer | 3.8 or newer (also old lab computers) |
| depends on | numpy, pandas, matplotlib, scipy, sympy, csvtex | numpy, matplotlib, pyvisa |
| connection | reads CSV files | writes CSV files |

The CSV files are the only connection: measure on the lab computer with `pemlab-instruments`,
evaluate at home with `pemlab`. {doc}`installation` explains how to install both.

```{toctree}
:hidden:

installation
```

```{toctree}
:caption: pemlab (evaluation)
:maxdepth: 1

pemlab/guide
pemlab/examples/01_data_and_calculations
pemlab/examples/02_plots_and_fits
pemlab/api
```

```{toctree}
:caption: pemlab-instruments (measuring)
:maxdepth: 1

instruments/guide
instruments/examples/01_measuring
instruments/api
```
