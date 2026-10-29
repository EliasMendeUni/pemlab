"""Mean of a measurement series with its spread and uncertainty."""

from dataclasses import dataclass

import numpy as np

from pemlab.numberstyle import NumberStyle


@dataclass
class MeanResult:
    n: int
    mean: float
    std: float | None  # sample standard deviation, None for a single value
    error: float | None  # uncertainty of the mean (standard error, or weighted), None if n == 1
    weighted: bool
    chi2_ndf: float | None  # weighted mean only: do the values agree within their uncertainties?
    reference: float | None = None

    @property
    def deviation(self) -> float | None:
        """Mean minus reference value."""
        return None if self.reference is None else self.mean - self.reference

    @property
    def relative_deviation(self) -> float | None:
        """Deviation in percent of the reference value."""
        if self.deviation is None or self.reference == 0:
            return None
        return self.deviation / self.reference * 100

    @property
    def deviation_in_sigma(self) -> float | None:
        """Absolute deviation in units of the uncertainty of the mean."""
        if self.deviation is None or not self.error:
            return None
        return abs(self.deviation) / self.error

    def formatted_mean(self, numbers: NumberStyle | None = None) -> tuple[str, str | None]:
        """Mean and its uncertainty as rounded strings (uncertainty None if unknown)."""
        numbers = numbers or NumberStyle()
        if self.error is None:
            return numbers.number(self.mean), None
        return numbers.value_error(self.mean, self.error)

    def summary(self, numbers: NumberStyle | None = None) -> str:
        value, error = self.formatted_mean(numbers)
        kind = "weighted mean" if self.weighted else "mean"
        lines = [f"n = {self.n}", f"{kind} = {value}" + ("" if error is None else f" ± {error}")]
        if self.std is not None:
            lines.append(f"standard deviation = {self.std:.3g}")
        if self.chi2_ndf is not None:
            lines.append(f"chi²/ndf = {self.chi2_ndf:.3g}")
        if self.deviation is not None:
            parts = [f"{self.deviation:+.3g}"]
            if self.relative_deviation is not None:
                parts.append(f"{self.relative_deviation:+.2g} %")
            if self.deviation_in_sigma is not None:
                parts.append(f"{self.deviation_in_sigma:.2g} sigma")
            lines.append(f"deviation from {self.reference:g} = " + ", ".join(parts))
        return "\n".join(lines)


def mean_of(values, sigma=None, reference: float | None = None) -> MeanResult:
    """Mean of `values`. Without `sigma`: arithmetic mean with standard error s/sqrt(n).

    With `sigma` (one uncertainty per value): weighted mean with its uncertainty
    1/sqrt(sum of weights) and chi-squared per degree of freedom.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    std = float(np.std(values, ddof=1)) if n > 1 else None

    if sigma is None:
        mean = float(np.mean(values))
        error = None if std is None else std / np.sqrt(n)
        return MeanResult(n, mean, std, error, False, None, reference)

    weights = 1 / np.asarray(sigma, dtype=float) ** 2
    mean = float(np.sum(weights * values) / np.sum(weights))
    error = float(1 / np.sqrt(np.sum(weights)))
    chi2_ndf = float(np.sum(weights * (values - mean) ** 2) / (n - 1)) if n > 1 else None
    return MeanResult(n, mean, std, error, True, chi2_ndf, reference)
