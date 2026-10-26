"""Evaluate a recorded signal: edges, rise time and the maximum of a curve."""

import numpy as np


def edge_times(t, u, level: float | None = None, rising: bool = True) -> list[float]:
    """Times at which the signal crosses `level` (default: the middle between minimum and
    maximum), interpolated between the samples. `rising=False` finds the falling edges.

    A pulse and its echo: the times of the rising edges, `t_pulse, t_echo = edge_times(t, u, 0.5)`.
    Choose `level` below the height of the smaller echo.
    """
    t = np.asarray(t, dtype=float)
    u = np.asarray(u, dtype=float)
    if level is None:
        level = (u.max() + u.min()) / 2
    above = u >= level
    times = []
    for i in np.flatnonzero(above[1:] != above[:-1]):
        if (u[i + 1] > u[i]) != rising:
            continue
        fraction = (level - u[i]) / (u[i + 1] - u[i])
        times.append(float(t[i] + fraction * (t[i + 1] - t[i])))
    return times


def edge_duration(t, u, rising: bool = True, low: float = 0.1, high: float = 0.9) -> float:
    """Rise time (or fall time with `rising=False`) of the first edge: the time between `low` and
    `high` of the amplitude (default 10 % to 90 %)."""
    bottom, top = float(np.min(u)), float(np.max(u))
    first, second = (low, high) if rising else (high, low)
    starts = edge_times(t, u, bottom + first * (top - bottom), rising)
    if not starts:
        raise ValueError("Keine passende Flanke im Signal gefunden.")
    later = edge_times(t, u, bottom + second * (top - bottom), rising)
    ends = [time for time in later if time > starts[0]]
    if not ends:
        raise ValueError("Die Flanke erreicht den zweiten Pegel nicht.")
    return ends[0] - starts[0]


def find_peak(x, y) -> tuple[float, float]:
    """Position and height of the maximum of a curve, e.g. the resonance frequency.

    A parabola through the highest point and its two neighbors refines the result beyond the
    spacing of the samples.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    i = int(np.argmax(y))
    if i == 0 or i == len(y) - 1:
        return float(x[i]), float(y[i])
    x1, x2, x3 = x[i - 1 : i + 2]
    y1, y2, y3 = y[i - 1 : i + 2]
    denominator = (x1 - x2) * (x1 - x3) * (x2 - x3)
    a = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denominator
    b = (x3**2 * (y1 - y2) + x2**2 * (y3 - y1) + x1**2 * (y2 - y3)) / denominator
    c = (
        x2 * x3 * (x2 - x3) * y1 + x3 * x1 * (x3 - x1) * y2 + x1 * x2 * (x1 - x2) * y3
    ) / denominator
    if a >= 0:  # flat or not a maximum: keep the sample
        return float(x2), float(y2)
    x_peak = -b / (2 * a)
    return float(x_peak), float(a * x_peak**2 + b * x_peak + c)
