"""Tests of the plot styles: they must change how the plots look, and the defaults stay sensible."""

from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pemlab import FitStyle, LayoutStyle, PointStyle, Project
from pemlab.data import PlotData
from pemlab.fit import fit_function
from pemlab.plotting import make_data_figure, make_fit_figure


def line_function(x, a, b):
    return a * x + b


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def data():
    x = np.linspace(0, 10, 20)
    return PlotData(("$x$ [m]", x), ("$y$ [m]", 2 * x + 1))


@pytest.fixture
def data_sigma(data):
    return PlotData(data.x, data.y, ("$u(y)$ [m]", np.full(20, 0.1)))


def fit_figure(data, points=None, fit=None, layout=None):
    result = fit_function(line_function, data.x[1], data.y[1])
    return make_fit_figure(data, line_function, result, "a x + b", points, fit, layout)


# --- PointStyle ---


def test_default_markers_are_small():
    assert PointStyle().marker_size < plt.rcParams["lines.markersize"]


def test_marker_options(data):
    points = PointStyle(marker="s", marker_size=1.5, marker_color="red", marker_alpha=0.4)
    line = make_data_figure(data, points).axes[0].lines[0]
    assert (line.get_marker(), line.get_markersize()) == ("s", 1.5)
    assert line.get_color() == "red"
    assert line.get_alpha() == 0.4
    assert line.get_linestyle() == "None"


def test_connect_points(data):
    line = make_data_figure(data, PointStyle(connect_points=True)).axes[0].lines[0]
    assert line.get_linestyle() == "-"


def test_errorbar_options(data_sigma):
    points = PointStyle(capsize=5.0, errorbar_linewidth=2.0, marker_size=2.0)
    container = make_data_figure(data_sigma, points).axes[0].containers[0]
    data_line, caplines, barlinecols = container.lines
    assert data_line.get_markersize() == 2.0
    assert caplines[0].get_markersize() == 2 * 5.0  # capsize is the half cap length in points
    assert barlinecols[0].get_linewidth()[0] == 2.0


def test_data_label_none_gives_no_entry(data):
    fig = fit_figure(data, PointStyle(label=None), FitStyle(label="nur der Fit"))
    assert [t.get_text() for t in fig.axes[0].get_legend().get_texts()] == ["nur der Fit"]


# --- FitStyle ---


def test_fit_line_options(data):
    fit = FitStyle(color="green", linewidth=3.0, linestyle="--", points=50)
    fit_line = fit_figure(data, fit=fit).axes[0].lines[-1]
    assert fit_line.get_color() == "green"
    assert fit_line.get_linewidth() == 3.0
    assert fit_line.get_linestyle() == "--"
    assert len(fit_line.get_xdata()) == 50


def test_fit_label_default_and_custom(data):
    default = fit_figure(data).axes[0].get_legend().get_texts()[1].get_text()
    assert "a x + b" in default and "a=2" in default
    custom = fit_figure(data, fit=FitStyle(label="meine Gerade")).axes[0].get_legend()
    assert custom.get_texts()[1].get_text() == "meine Gerade"


# --- LayoutStyle ---


def test_axes_options(data):
    layout = LayoutStyle(
        xlabel="Zeit", ylabel="Weg", title="Titel", xscale="log", yscale="log",
        xlim=(1, 9), ylim=(2, 20), grid=False, figsize=(3.0, 2.0),
    )  # fmt: skip
    fig = make_data_figure(data, layout=layout)
    ax = fig.axes[0]
    assert (ax.get_xlabel(), ax.get_ylabel(), ax.get_title()) == ("Zeit", "Weg", "Titel")
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "log")
    assert (ax.get_xlim(), ax.get_ylim()) == ((1, 9), (2, 20))
    assert not ax.xaxis.get_gridlines()[0].get_visible()
    assert tuple(fig.get_size_inches()) == (3.0, 2.0)


def test_labels_come_from_columns_by_default(data):
    ax = make_data_figure(data).axes[0]
    assert ax.get_xlabel() == "$x$ [m]"
    assert ax.get_ylabel() == "$y$ [m]"


def test_legend_automatic_and_explicit(data):
    assert make_data_figure(data).axes[0].get_legend() is None
    assert fit_figure(data).axes[0].get_legend() is not None
    assert make_data_figure(data, layout=LayoutStyle(legend=True)).axes[0].get_legend()
    assert fit_figure(data, layout=LayoutStyle(legend=False)).axes[0].get_legend() is None


def test_font_size_applies_to_all_text(data):
    fig = fit_figure(data, layout=LayoutStyle(font_size=20))
    fig.canvas.draw()
    ax = fig.axes[0]
    assert ax.xaxis.label.get_fontsize() == 20
    assert ax.get_xticklabels()[0].get_fontsize() == 20
    assert ax.get_legend().get_texts()[0].get_fontsize() == 20


def test_font_size_does_not_leak_into_other_plots(data):
    before = plt.rcParams["font.size"]
    make_data_figure(data, layout=LayoutStyle(font_size=20))
    assert plt.rcParams["font.size"] == before


# --- validation and copies ---


def test_invalid_values_are_rejected():
    with pytest.raises(ValueError):
        PointStyle(marker_size=0)
    with pytest.raises(ValueError):
        PointStyle(marker_alpha=1.5)
    with pytest.raises(ValueError):
        FitStyle(points=1)


def test_styles_are_frozen_and_copyable():
    layout = LayoutStyle()
    with pytest.raises(AttributeError):
        layout.grid = False
    assert replace(layout, grid=False).grid is False and layout.grid is True


# --- Project and Analysis ---


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "linear.csv"
    rows = [f"{x},{2 * x + 1}" for x in range(10)]
    path.write_text("$x$ [m],$y$ [m]\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def plot_figure(lab, name):
    return lab._artifacts[("plots", name)].figure


def test_project_styles_reach_the_plots(tmp_path, csv_file):
    lab = Project(
        tmp_path / "build",
        points=PointStyle(marker_size=1.0),
        fit=FitStyle(linewidth=4.0),
        layout=LayoutStyle(title="Projekt"),
    )
    analysis = lab.analysis(csv_file)
    data = analysis.make_PlotData("$x$ [m]", "$y$ [m]")
    analysis.plot_data("points", data)
    analysis.regression("fit", line_function, data)
    for name in ("points", "fit"):
        ax = plot_figure(lab, name).axes[0]
        assert ax.lines[0].get_markersize() == 1.0
        assert ax.get_title() == "Projekt"
    assert plot_figure(lab, "fit").axes[0].lines[-1].get_linewidth() == 4.0


def test_arguments_override_one_part_at_a_time(tmp_path, csv_file):
    lab = Project(
        tmp_path / "build", points=PointStyle(marker_size=1.0), layout=LayoutStyle(title="Projekt")
    )
    analysis = lab.analysis(csv_file)
    data = analysis.make_PlotData("$x$ [m]", "$y$ [m]")
    analysis.regression(
        "fit", line_function, data, layout=LayoutStyle(xscale="linear", title="Neu")
    )
    ax = plot_figure(lab, "fit").axes[0]
    assert ax.get_title() == "Neu"  # layout replaced
    assert ax.lines[0].get_markersize() == 1.0  # points still from the project


def test_png_dpi_is_used_when_building(tmp_path, csv_file):
    lab = Project(tmp_path / "build", layout=LayoutStyle(figsize=(3.0, 2.0), png_dpi=100))
    analysis = lab.analysis(csv_file)
    analysis.plot_data("points", analysis.make_PlotData("$x$ [m]", "$y$ [m]"))
    lab.build()
    image = plt.imread(tmp_path / "build" / "plots" / "points" / "points.png")
    assert image.shape[:2] == (200, 300)
