"""Measure inside a `with` block: you write the loop body, the sweep takes care of the rest."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

import numpy as np

from pemlab_instruments.log import MeasurementLog


class Sweep:
    """The values to go through, the rows measured so far and (optionally) the csv file.

    Use it as a context manager and loop over it. What happens in the loop is up to you: set
    the instruments, measure, update plots, print. `add` stores a row. The first column is the
    value of the loop (set value or time), `add` takes the measured values behind it::

        with LogSweep(10, 20_000, 60, columns=["f [Hz]", "U_e [V]", "U_a [V]"],
                      save="data/measurements/hp.csv") as sweep:
            plot = LivePlot(sweep, x="f [Hz]", y=lambda r: r["U_a [V]"] / r["U_e [V]"])
            for f in sweep:
                awg.set_frequency(f)
                sweep.wait(0.3)
                sweep.add(measure_voltage(dmm_1, ac=True), measure_voltage(dmm_2, ac=True))

    Ctrl+C anywhere in the block ends the measurement cleanly: the rows so far stay in `sweep.log`
    (and in the csv file, which is written row by row), the code after the block runs on. An
    endless measurement is `Sweep(itertools.count(), ...)`.
    """

    def __init__(
        self,
        values: Iterable[float],
        columns: list[str],
        save: str | Path | None = None,
        verbose: bool = False,
    ):
        self.values = values
        self.log = MeasurementLog(*columns)
        self.save_path = None if save is None else Path(save)
        self.verbose = verbose
        self.value: float | None = None  # the current value of the loop
        self.interrupted = False
        self._callbacks: list[Callable[[Sweep], None]] = []
        self._live: list = []  # live plots, so `wait` can keep their windows responsive

    def __enter__(self) -> Sweep:
        self.interrupted = False
        if self.save_path is not None:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            self.save_path.write_text(",".join(self.log.columns) + "\n", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is not None and issubclass(exc_type, KeyboardInterrupt):
            self.interrupted = True
            print(f"Messung abgebrochen nach {len(self.log)} Zeilen.")
            return True  # swallow Ctrl+C, the code behind the block continues
        return False

    def __iter__(self) -> Iterator[float]:
        for value in self.values:
            self.value = value
            yield value

    def add(self, *measured: float) -> None:
        """Store a row: the current value of the loop, then the measured values."""
        row = (self.value, *measured)
        self.log.add(*row)
        if self.save_path is not None:
            line = ",".join(format(float(v), ".12g") for v in self.log.rows[-1])
            with self.save_path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
        if self.verbose:
            pairs = zip(self.log.columns, self.log.rows[-1])
            print(" | ".join(f"{c}: {v:.6g}" for c, v in pairs))
        for callback in self._callbacks:
            callback(self)

    def on_row(self, callback: Callable[[Sweep], None]) -> None:
        """Call `callback(sweep)` after every `add`, for your own live displays."""
        self._callbacks.append(callback)

    def wait(self, seconds: float) -> None:
        """Wait (e.g. for the instrument to settle). Live plots stay responsive meanwhile."""
        if self._live:
            import matplotlib.pyplot as plt

            plt.pause(seconds)
        else:
            time.sleep(seconds)

    def rows_as_dicts(self) -> list[dict[str, np.float64]]:
        columns = self.log.columns
        return [dict(zip(columns, map(np.float64, row))) for row in self.log.rows]


class LinSweep(Sweep):
    """`num` linearly spaced values from `start` to `stop`."""

    def __init__(self, start: float, stop: float, num: int, columns: list[str], **kwargs):
        super().__init__(np.linspace(start, stop, num), columns, **kwargs)


class LogSweep(Sweep):
    """`num` logarithmically spaced values from `start` to `stop` (both > 0)."""

    def __init__(self, start: float, stop: float, num: int, columns: list[str], **kwargs):
        super().__init__(np.geomspace(start, stop, num), columns, **kwargs)


class Timed(Sweep):
    """A measurement over time: the loop value is the real time in s since the start.

    One round every `interval` seconds (timed from the start, so delays do not add up), for
    `duration` seconds, or until Ctrl+C when `duration` is None::

        with Timed(2, columns=["t [s]", "U [V]"], duration=600) as run:
            for t in run:
                run.add(measure_voltage(dmm_1))
    """

    def __init__(
        self, interval: float, columns: list[str], duration: float | None = None, **kwargs
    ):
        super().__init__([], columns, **kwargs)
        self.interval = interval
        self.duration = duration

    def __iter__(self) -> Iterator[float]:
        start = time.monotonic()
        k = 0
        while self.duration is None or k * self.interval <= self.duration + 1e-9:
            wait = start + k * self.interval - time.monotonic()
            if wait > 0:
                self.wait(wait)
            self.value = time.monotonic() - start
            yield self.value
            k += 1
