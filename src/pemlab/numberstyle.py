"""NumberStyle: how numbers are shown in tables, fit results and means.

Only the display is rounded. The csv files and all calculations keep the full values.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from math import floor, isfinite, log10


@dataclass(frozen=True)
class NumberStyle:
    """Rounding and notation of shown numbers. Every field has a default.

    Numbers below `sci_below` or from `sci_above` on are written as 1.5e-3 (in LaTeX
    \\num{1.5e-3}) instead of 0.0015.
    """

    decimals: int | None = None  # table cells: decimals shown (None: the digits of the csv)
    error_digits: int = 2  # significant digits of an uncertainty; the value gets the same place
    significant_digits: int = 4  # a number without uncertainty
    sci_below: float = 1e-2  # |x| < sci_below is written as 1.5e-3
    sci_above: float = 1e5  # |x| >= sci_above is written as 1.5e5

    def __post_init__(self) -> None:
        if self.decimals is not None and self.decimals < 0:
            raise ValueError(f"decimals muss >= 0 sein, nicht {self.decimals}")
        if self.error_digits < 1 or self.significant_digits < 1:
            raise ValueError("error_digits und significant_digits müssen >= 1 sein")
        if not 0 < self.sci_below <= self.sci_above:
            raise ValueError("Es muss 0 < sci_below <= sci_above gelten")

    def is_scientific(self, value: float) -> bool:
        return value != 0 and not self.sci_below <= abs(value) < self.sci_above

    def number(self, value: float, digits: int | None = None) -> str:
        """A number with `digits` significant digits (default: significant_digits)."""
        digits = digits or self.significant_digits
        if value == 0 or not isfinite(value):
            return f"{value:g}"
        exponent = floor(log10(abs(value)))
        if self.is_scientific(value):
            return f"{value / 10**exponent:.{digits - 1}f}e{exponent}"
        return f"{value:.{max(0, digits - 1 - exponent)}f}"

    def value_error(self, value: float, error: float) -> tuple[str, str]:
        """Round the error to `error_digits` digits and the value to the same decimal place.

        Both get the exponent of the value if it is written as 2.848e-9 ('0.0037e-9' for the
        error), so they can be compared at a glance.
        """
        if not (isfinite(error) and error > 0):
            return self.number(value), f"{error:.2g}"
        reference = value if value != 0 and isfinite(value) else error
        shift = floor(log10(abs(reference))) if self.is_scientific(reference) else 0
        decimals = self.error_digits - 1 - (floor(log10(error)) - shift)
        suffix = f"e{shift}" if shift else ""
        return (
            _fixed(value / 10**shift, decimals) + suffix,
            _fixed(error / 10**shift, decimals) + suffix,
        )

    def cell(self, text: str, computed: bool = False) -> str:
        """A number from a csv cell: as written, rounded to `decimals`, e-notation if needed.

        A computed column has no precision of its own, so without `decimals` it gets
        `significant_digits`. Text that is not a number is returned unchanged.
        """
        try:
            number = Decimal(text.strip())
        except InvalidOperation:
            return text
        if not number.is_finite():
            return text
        scientific = self.is_scientific(float(number))
        if self.decimals is not None:
            return format(number, f".{self.decimals}{'e' if scientific else 'f'}")
        if computed:
            return self.number(float(number))
        if not scientific:
            return text
        if number == number.to_integral_value():  # 3240000 is 3.24e6, its zeros mean nothing
            number = number.normalize()
        return format(number, "e")


def _fixed(value: float, decimals: int) -> str:
    if decimals >= 0:
        return f"{value:.{decimals}f}"
    return f"{round(value, decimals):.0f}"
