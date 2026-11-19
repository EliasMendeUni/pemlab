"""pemlab-instruments: measure with pyvisa instruments, live plots and csv files for pemlab."""

from __future__ import annotations

__version__ = "0.1.0"

from .discovery import find_instruments
from .files import timestamped_path
from .dmm import (
    measure_current,
    measure_resistance,
    measure_temperature_pt100,
    measure_voltage,
    pt100_temperature,
)
from .generator import AFG1022, FunctionGenerator
from .live import LivePlot, LiveStyle
from .log import MeasurementLog
from .scope import Oscilloscope
from .series import measure_repeated, measure_series, measure_timeseries
from .signals import edge_duration, edge_times, find_peak
from .source import PowerSupply
from .sweep import LinSweep, LogSweep, Sweep, Timed

__all__ = [
    "AFG1022",
    "LinSweep",
    "LivePlot",
    "LiveStyle",
    "LiveStyle",
    "LogSweep",
    "Sweep",
    "Timed",
    "FunctionGenerator",
    "MeasurementLog",
    "Oscilloscope",
    "PowerSupply",
    "edge_duration",
    "edge_times",
    "find_instruments",
    "find_peak",
    "measure_current",
    "measure_repeated",
    "measure_resistance",
    "measure_series",
    "measure_timeseries",
    "measure_temperature_pt100",
    "measure_voltage",
    "pt100_temperature",
    "timestamped_path",
]
