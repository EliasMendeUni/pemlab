"""Power supply (commands of the Rigol DP800 series)."""

from collections.abc import Iterator
from contextlib import contextmanager


class PowerSupply:
    """Wraps an opened pyvisa resource: source = PowerSupply(rm.open_resource(address))."""

    def __init__(self, resource):
        self.resource = resource

    def settings(self, voltage: float, current: float, channel: int = 1) -> None:
        """Set voltage (V) and current limit (A) of a channel. The output stays as it is."""
        self.resource.write(f"APPL CH{channel},{voltage},{current}")

    def on(self, channel: int = 1) -> None:
        self.resource.write(f"OUTPUT CH{channel},ON")

    def off(self, channel: int = 1) -> None:
        self.resource.write(f"OUTPUT CH{channel},OFF")

    @contextmanager
    def output(self, channel: int = 1) -> Iterator[None]:
        """Output on inside the `with` block, and off again afterwards, also after an error.

            with source.output(): ...
        """
        self.on(channel)
        try:
            yield
        finally:
            self.off(channel)
