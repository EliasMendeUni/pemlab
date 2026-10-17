import inspect
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from pemlab.data import PlotData, get_csv_data

def _function_expression(function, x_name: str) -> str:
    """Return the expression after `return` with the x argument replaced by x_name."""
    try:
        lines = inspect.getsource(function).splitlines()
    except (OSError, TypeError):
        return function.__name__
    x_arg = next(iter(inspect.signature(function).parameters))
    for line in reversed(lines):
        line = line.strip()
        if line.startswith("return "):
            expression = line.removeprefix("return ")
            return re.sub(rf"\b{re.escape(x_arg)}\b", lambda _: x_name, expression)
    return function.__name__

class Analysis:
    def __init__(self, file: str | Path):
        self.csv_data = get_csv_data(file)

    def make_PlotData(self, x_index: int, y_index: int, y_sigma_index: int) -> PlotData:
        return PlotData(self.csv_data[x_index], self.csv_data[y_index], self.csv_data[y_sigma_index])
        
    def plot_data(self, data: PlotData):
        fig, ax = plt.subplots()
        ax.plot(data.x[1], data.y[1], "o")
        ax.set_xlabel(data.x[0])
        ax.set_ylabel(data.y[0])
        ax.grid(True)
        plt.show()

    def plot_regression(self, function, data: PlotData, p0=None):
        x_name, x = data.x
        y_name, y = data.y
        _, y_sigma = data.y_sigma

        # Parameternamen aus der Funktionssignatur (alles nach dem ersten Argument)
        names = list(inspect.signature(function).parameters)[1:]
        if p0 is None:
            p0 = np.ones(len(names))

        popt, pcov = curve_fit(function, x, y, p0=p0, sigma=y_sigma, absolute_sigma=True)
        perr = np.sqrt(np.diag(pcov))

        for name, value, err in zip(names, popt, perr):
            print(f"{name} = {value:.4g} ± {err:.2g}")

        chi2 = np.sum(((y - function(x, *popt)) / y_sigma) ** 2)
        dof = len(x) - len(popt)
        if dof > 0:
            print(f"chi²/ndf = {chi2:.3g}/{dof} = {chi2 / dof:.3g}")

        fig, ax = plt.subplots()
        ax.errorbar(x, y, yerr=y_sigma, fmt="o", capsize=3, label="Messdaten")
        xs = np.linspace(x.min(), x.max(), 200)
        params = ", ".join(f"{n}={v:.3g}" for n, v in zip(names, popt))
        fit_label = f"Fit: {y_name} = {_function_expression(function, x_name)}\n{params}"
        ax.plot(xs, function(xs, *popt), label=fit_label)
        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.legend()
        ax.grid(True)
        plt.show()
        return popt, perr
