from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dataclasses import dataclass

def get_csv_data(file: str | Path) -> list[tuple[str, np.ndarray]]:
    df = pd.read_csv(file)
    return [(c, df[c].to_numpy()) for c in df.columns]

@dataclass
class PlotData:
    x: tuple[str, np.ndarray]
    y: tuple[str, np.ndarray]
    y_sigma: tuple[str, np.ndarray]

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