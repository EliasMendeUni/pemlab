"""Function generator (commands of the Rigol DG series)."""

from collections.abc import Iterator
from contextlib import contextmanager

_SHAPES = {"sine": "SINusoid", "square": "SQUare", "ramp": "RAMP", "noise": "NOISe", "dc": "DC"}


class FunctionGenerator:
    """Wraps an opened pyvisa resource: awg = FunctionGenerator(rm.open_resource(address))."""

    def __init__(self, resource):
        self.resource = resource

    def settings(
        self,
        shape: str = "sine",
        frequency: float = 1000.0,
        amplitude: float = 1.0,
        offset: float = 0.0,
        channel: int = 1,
    ) -> None:
        """Set waveform ("sine", "square", "ramp"), frequency (Hz), amplitude (Vpp), offset (V)."""
        if shape not in _SHAPES:
            raise ValueError(f"Unbekannte Signalform '{shape}'. Möglich: {list(_SHAPES)}")
        self.resource.write(
            f":SOURce{channel}:APPLy:{_SHAPES[shape]} {frequency},{amplitude},{offset},0"
        )

    def on(self, channel: int = 1) -> None:
        self.resource.write(f":OUTPut{channel} ON")

    def off(self, channel: int = 1) -> None:
        self.resource.write(f":OUTPut{channel} OFF")

    @contextmanager
    def output(self, channel: int = 1) -> Iterator[None]:
        """Output on inside the `with` block, and off again afterwards, also after an error."""
        self.on(channel)
        try:
            yield
        finally:
            self.off(channel)
