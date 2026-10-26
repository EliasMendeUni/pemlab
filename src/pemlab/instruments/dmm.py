"""Digital multimeter: every function takes the opened pyvisa resource and returns a float.

The commands follow the Rigol DM3000 series (SCPI).
"""

from math import sqrt

# Callendar-Van Dusen coefficients of platinum resistance thermometers (IEC 60751)
_A = 3.9083e-3
_B = -5.775e-7
_C = -4.183e-12


def _measure(dmm, command: str, range_) -> float:
    """Manual mode, set the range and read one value. `command` is e.g. ':MEASure:VOLTage:DC'."""
    dmm.write(":MEASure MANU")
    dmm.write(command if range_ is None else f"{command} {range_}")
    return float(dmm.query(f"{command}?"))


def measure_voltage(dmm, range=None, ac: bool = False) -> float:
    """Voltage in V. `range` is passed to the instrument (None: keep its setting)."""
    return _measure(dmm, f":MEASure:VOLTage:{'AC' if ac else 'DC'}", range)


def measure_current(dmm, range=None, ac: bool = False) -> float:
    """Current in A."""
    return _measure(dmm, f":MEASure:CURRent:{'AC' if ac else 'DC'}", range)


def measure_resistance(dmm, range=None, four_wire: bool = False) -> float:
    """Resistance in Ohm (two-wire, or four-wire with `four_wire=True`)."""
    return _measure(dmm, ":MEASure:FRESistance" if four_wire else ":MEASure:RESistance", range)


def pt100_temperature(resistance: float, r0: float = 100.0) -> float:
    """Temperature in degrees Celsius of a platinum thermometer (Pt100: r0=100, Pt1000: 1000)."""
    ratio = resistance / r0
    if ratio >= 1:  # T >= 0: R = R0 (1 + A T + B T^2) solved for T
        return (-_A + sqrt(_A * _A - 4 * _B * (1 - ratio))) / (2 * _B)
    temperature = (ratio - 1) / _A  # T < 0 has an extra term, solve with Newton's method
    for _ in range(20):
        t = temperature
        value = 1 + _A * t + _B * t**2 + _C * (t - 100) * t**3
        slope = _A + 2 * _B * t + _C * (4 * t**3 - 300 * t**2)
        temperature -= (value - ratio) / slope
    return temperature


def measure_temperature_pt100(dmm, r0: float = 100.0, four_wire: bool = True) -> float:
    """Temperature in degrees Celsius from a Pt100 (Pt1000: r0=1000), measured as a resistance."""
    return pt100_temperature(measure_resistance(dmm, four_wire=four_wire), r0)
