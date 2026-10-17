from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dataclasses import dataclass

@dataclass
class CSVData:
    columns: list[np.ndarray]


def make_csv_data(file: str | Path) -> CSVData:
    df = pd.read_csv(file)
    return [df[c].to_numpy() for c in df.columns]


@dataclass
class PlotData:
    x_points: np.ndarray
    y_points: np.ndarray
    y_sigma: np.ndarray

class Analysis:
    def __init__(self, file: str | Path):
        self.csv_data = make_csv_data(file)

    def make_data(self, x_index: int, y_index: int, y_sigma_index: int) -> PlotData:
        x_points = self.csv_data.iloc[:, x_index].to_numpy()
        y_points = self.csv_data.iloc[:, y_index].to_numpy()
        y_sigma_points = self.csv_data.iloc[:, y_sigma_index].to_numpy()
        return PlotData(x_points, y_points, y_sigma_points)
        

    def plot_data(self, data: PlotData):
        plt.plot(data.x_points, data.y_points, 'o')
        plt.show