"""Measure a whole series: set a value, wait, measure, repeat."""

import time
from collections.abc import Callable, Iterable

from pemlab.instruments.log import MeasurementLog


def measure_series(
    values: Iterable[float],
    set_value: Callable[[float], None],
    measure: Callable[[], float | tuple[float, ...]],
    columns: list[str],
    settle: float = 0.5,
    verbose: bool = True,
) -> MeasurementLog:
    """For every value: `set_value(value)`, wait `settle` seconds, `measure()`, store the row.

    `columns` names the set value first, then the measured values (`measure` returns one number
    or a tuple). Example, the current of a resistor at several voltages::

        log = measure_series(
            [1, 2, 3], lambda v: source.settings(v, 0.1), lambda: measure_current(dmm),
            ["U [V]", "I [A]"],
        )
        log.save("data/measurements/resistor.csv")
    """
    log = MeasurementLog(*columns)
    for value in values:
        set_value(value)
        time.sleep(settle)
        results = _as_tuple(measure())
        log.add(value, *results)
        if verbose:
            print(f"{value} -> {', '.join(str(r) for r in results)}")
    return log


def measure_timeseries(
    measure: Callable[[], float | tuple[float, ...]],
    duration: float,
    interval: float,
    columns: list[str],
    verbose: bool = False,
) -> MeasurementLog:
    """Measure every `interval` seconds for `duration` seconds.

    The first column is the **real** time since the start in seconds (taken when the measurement
    starts), not the planned time, so a slow instrument does not distort the time axis. The
    rows are timed from the start, so the delays do not add up. Example::

        log = measure_timeseries(
            lambda: measure_voltage(dmm), duration=600, interval=2, columns=["t [s]", "U [V]"]
        )
    """
    log = MeasurementLog(*columns)
    start = time.monotonic()
    for k in range(int(duration / interval + 1e-9) + 1):
        wait = start + k * interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        elapsed = time.monotonic() - start
        results = _as_tuple(measure())
        log.add(elapsed, *results)
        if verbose:
            print(f"{elapsed:.1f} s -> {', '.join(str(r) for r in results)}")
    return log


def _as_tuple(result) -> tuple:
    return tuple(result) if isinstance(result, tuple | list) else (result,)


def measure_repeated(measure: Callable[[], float], n: int = 10, wait: float = 0.0) -> list[float]:
    """`n` measurements one after the other, e.g. as input for a mean."""
    values = []
    for _ in range(n):
        values.append(measure())
        time.sleep(wait)
    return values
