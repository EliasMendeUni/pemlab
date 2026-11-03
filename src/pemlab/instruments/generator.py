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

    def set_frequency(self, frequency: float, channel: int = 1) -> None:
        """Only the frequency (Hz), faster than `settings` inside a sweep."""
        self.resource.write(f":SOURce{channel}:FREQuency {frequency}")

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


_AFG_SHAPES = {
    "sine": "SINusoid",
    "square": "SQUare",
    "ramp": "RAMP",
    "noise": "PRNoise",
    "dc": "DC",
}


class AFG1022(FunctionGenerator):
    """Tektronix AFG1022 (its own command set): awg = AFG1022(rm.open_resource(address)).

    `load` is the load the display assumes: 50 (Ohm) or "INF". The physical output impedance
    stays 50 Ohm.
    """

    def __init__(self, resource, load: float | str = 50):
        super().__init__(resource)
        self.load = load

    def settings(
        self,
        shape: str = "sine",
        frequency: float = 1000.0,
        amplitude: float = 1.0,
        offset: float = 0.0,
        channel: int = 1,
    ) -> None:
        """Set waveform, frequency (Hz), amplitude (Vpp), offset (V) and the load."""
        if shape not in _AFG_SHAPES:
            raise ValueError(f"Unbekannte Signalform '{shape}'. Möglich: {list(_AFG_SHAPES)}")
        write = self.resource.write
        write(f"OUTPut{channel}:IMPedance {self.load}")
        write(f"SOURce{channel}:FUNCtion:SHAPe {_AFG_SHAPES[shape]}")
        write(f"SOURce{channel}:VOLTage:LEVel:IMMediate:OFFSet {offset}V")
        write(f"SOURce{channel}:VOLTage:LEVel:IMMediate:AMPLitude {amplitude}Vpp")
        write(f"SOURce{channel}:FREQuency:FIXed {frequency}Hz")

    def set_frequency(self, frequency: float, channel: int = 1) -> None:
        self.resource.write(f"SOURce{channel}:FREQuency:FIXed {frequency}Hz")

    def on(self, channel: int = 1) -> None:
        self.resource.write(f"OUTPut{channel}:STATe ON")

    def off(self, channel: int = 1) -> None:
        self.resource.write(f"OUTPut{channel}:STATe OFF")
