"""Oscilloscope (commands of the Rigol DS1000Z series)."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np

_ITEMS = {
    "vpp": "VPP",
    "vrms": "VRMS",
    "vmax": "VMAX",
    "vmin": "VMIN",
    "mean": "VAVerage",
    "freq": "FREQuency",
    "period": "PERiod",
}


class Oscilloscope:
    """Wraps an opened pyvisa resource: scope = Oscilloscope(rm.open_resource(address))."""

    def __init__(self, resource):
        self.resource = resource

    def run(self) -> None:
        self.resource.write(":RUN")

    def stop(self) -> None:
        self.resource.write(":STOP")

    def single(self) -> None:
        """Arm a single acquisition (wait for one trigger, then stop)."""
        self.resource.write(":SINGle")

    @contextmanager
    def stopped(self) -> Iterator[None]:
        """The scope is stopped inside the `with` block and runs again afterwards.

        Example::

            with scope.stopped():
                time, voltage = scope.read_waveform()
        """
        self.stop()
        try:
            yield
        finally:
            self.run()

    def measure(self, quantity: str, channel: int = 1) -> float:
        """One value from the scope's measurement: "vpp", "vrms", "vmax", "vmin", "mean",
        "freq" (Hz) or "period" (s)."""
        if quantity not in _ITEMS:
            raise ValueError(f"Unbekannte Größe '{quantity}'. Möglich: {list(_ITEMS)}")
        return float(self.resource.query(f":MEASure:ITEM? {_ITEMS[quantity]},CHANnel{channel}"))

    def read_waveform(self, channel: int = 1) -> tuple[np.ndarray, np.ndarray]:
        """Time (s) and voltage (V) of the trace on the screen. Read it inside
        `with scope.stopped():` so the trace does not change while it is transferred."""
        r = self.resource
        r.write(f":WAVeform:SOURce CHANnel{channel}")
        r.write(":WAVeform:MODE NORMal")
        r.write(":WAVeform:FORMat BYTE")
        preamble = [float(value) for value in r.query(":WAVeform:PREamble?").split(",")]
        x_increment, x_origin, x_reference = preamble[4:7]
        y_increment, y_origin, y_reference = preamble[7:10]

        raw = np.array(r.query_binary_values(":WAVeform:DATA?", datatype="B"), dtype=float)
        voltage = (raw - y_origin - y_reference) * y_increment
        time = (np.arange(len(raw)) - x_reference) * x_increment + x_origin
        return time, voltage

    def screenshot(self, path: str | Path) -> Path:
        """Save the screen as PNG."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.resource.query_binary_values(
            ":DISPlay:DATA? ON,OFF,PNG", datatype="B", container=bytes
        )
        path.write_bytes(bytes(data))
        return path
