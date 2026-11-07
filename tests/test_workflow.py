"""Tests of the functions as formulas, of Visualize (several layers in one plot) and of the
folder structure of the tables."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pemlab import EditCsv, FitStyle, LayoutStyle, PointStyle, Project
from pemlab.fit import exponential, fit_exponential  # noqa: F401
from pemlab.latex import calculation_to_tex

F = "$f$ [Hz]"
DT = r"$\Delta t$ [s]"


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def phase_csv(tmp_path):
    path = tmp_path / "phase.csv"
    pd.DataFrame({F: [100.0, 200.0, 400.0], DT: [1e-3, 1e-3, 1e-3]}).to_csv(path, index=False)
    return path


def straight(x, a, b):
    return a * x + b


# --- functions as formulas ---


def test_lambda_with_numpy_gives_the_same_column_as_the_formula_text(phase_csv):
    table = EditCsv(phase_csv)
    table.add_column("a [deg]", lambda dt, f: np.degrees(2 * np.pi * f * dt), dt=DT, f=F)
    table.add_column("b [deg]", "360 * dt * f", dt=DT, f=F)
    assert table.column("a [deg]") == pytest.approx(table.column("b [deg]"))
    assert table.column("a [deg]") == pytest.approx([36.0, 72.0, 144.0])


def test_function_arguments_are_found_by_column_name(phase_csv):
    table = EditCsv(phase_csv)
    table.add_column("T [s]", lambda f: 1 / f)  # the column "$f$ [Hz]" is f
    assert table.column("T [s]") == pytest.approx([0.01, 0.005, 0.0025])


def test_the_report_shows_the_expression_of_a_function(phase_csv):
    table = EditCsv(phase_csv)
    table.add_column("p [deg]", lambda dt, f: np.degrees(2 * np.pi * f * dt), dt=DT, f=F, show=True)
    tex = calculation_to_tex(table.calculations[0])
    assert r"360 \cdot dt \cdot f" in tex
    assert table.calculations[0].formula == "np.degrees(2 * np.pi * f * dt)"


def test_a_function_with_several_lines_is_shown_as_text(phase_csv):
    def double(f):
        factor = 2
        return f * factor

    table = EditCsv(phase_csv)
    table.add_column("d [Hz]", double, f=F, show=True)
    assert table.column("d [Hz]") == pytest.approx([200.0, 400.0, 800.0])
    assert r"\texttt{f * factor}" in calculation_to_tex(table.calculations[0])


def test_uncertainty_of_a_function_needs_a_single_expression(phase_csv):
    table = EditCsv(phase_csv)
    table.add_uncertainty("s [deg]", lambda dt, f: 360 * dt * f, {"dt": 1e-6, "f": 0.1}, dt=DT, f=F)
    assert table.column("s [deg]") == pytest.approx(
        np.sqrt((360 * 1e-3 * 0.1) ** 2 + (360 * np.array([100, 200, 400]) * 1e-6) ** 2)
    )

    def two_lines(f):
        g = f
        return g

    with pytest.raises(ValueError, match="ableiten"):
        table.add_uncertainty("s2", two_lines, {"f": 0.1}, f=F)


def test_replace_column_with_a_function(phase_csv):
    table = EditCsv(phase_csv)
    table.replace_column(F, "f [kHz]", lambda f: f / 1000, f=F)
    assert list(table.df.columns)[0] == "f [kHz]"
    assert table.column("f [kHz]") == pytest.approx([0.1, 0.2, 0.4])


# --- Visualize ---


@pytest.fixture
def lab_with_data(tmp_path):
    x = np.linspace(1, 10, 20)
    for name, a in (("one", 2.0), ("two", 3.0)):
        frame = pd.DataFrame({"$x$ [m]": x, "$y$ [m]": a * x + 1, "s [m]": 0.1})
        frame.to_csv(tmp_path / f"{name}.csv", index=False)
    lab = Project(tmp_path / "build")
    return lab, lab.analysis(tmp_path / "one.csv"), lab.analysis(tmp_path / "two.csv")


def test_visualize_draws_every_layer_in_one_axes(lab_with_data):
    lab, one, two = lab_with_data
    plot = lab.Visualize("both", layout=LayoutStyle(title="Beide"))
    plot.add(one.make_PlotData("$x$ [m]", "$y$ [m]"), points=PointStyle(label="eins"))
    plot.add(two.make_regression(straight, two.make_PlotData("$x$ [m]", "$y$ [m]")))
    plot.add(lambda x: 4 * x, fit=FitStyle(label="Theorie", linestyle="--"), x=(1, 5))
    fig = plot.figure()
    assert len(fig.axes) == 1
    ax = fig.axes[0]
    assert len(ax.lines) == 4  # points, points, fit, function
    assert [t.get_text() for t in ax.get_legend().get_texts()][0] == "eins"
    assert "Theorie" in [t.get_text() for t in ax.get_legend().get_texts()]
    assert ax.lines[-1].get_xdata()[[0, -1]] == pytest.approx([1, 5])
    assert ax.get_title() == "Beide"


def test_visualize_without_curve_and_one_set_has_no_legend(lab_with_data):
    lab, one, _ = lab_with_data
    plot = lab.Visualize("single").add(one.make_PlotData("$x$ [m]", "$y$ [m]"))
    assert plot.figure().axes[0].get_legend() is None


def test_visualize_function_uses_the_range_of_all_points_and_log_spacing(lab_with_data):
    lab, one, _ = lab_with_data
    plot = lab.Visualize("log", layout=LayoutStyle(xscale="log"))
    plot.add(one.make_PlotData("$x$ [m]", "$y$ [m]"))
    plot.add(lambda x: x)
    xs = plot.figure().axes[0].lines[-1].get_xdata()
    assert xs[0] == pytest.approx(1) and xs[-1] == pytest.approx(10)
    assert xs[1] / xs[0] == pytest.approx(xs[2] / xs[1])  # geometric steps


def test_visualize_is_written_with_fits_and_calculations(lab_with_data, tmp_path):
    lab, one, _ = lab_with_data
    table = one.table
    table.add_column("z [m]", lambda y: 2 * y, show=True)
    data = one.make_PlotData("$x$ [m]", "z [m]")
    lab.Visualize("both").add(one.make_regression(straight, data))
    lab.build()
    tex = (tmp_path / "build" / "plots" / "both" / "both.tex").read_text(encoding="utf-8")
    assert "Regression" in tex and "Calculations" in tex
    assert (tmp_path / "build" / "plots" / "both" / "both.pdf").exists()
    assert (tmp_path / "build" / "plots" / "both" / "both.png").exists()
    assert not plt.get_fignums()  # figures are closed after writing


def test_visualize_rejects_wrong_input_and_empty_plots(lab_with_data):
    lab, one, _ = lab_with_data
    plot = lab.Visualize("x")
    with pytest.raises(TypeError):
        plot.add("not a plot")
    with pytest.raises(ValueError, match="leer"):
        plot.figure()
    with pytest.raises(ValueError, match="Messreihe"):
        lab.Visualize("y").add(lambda x: x).figure()


def test_plot_data_and_regression_still_work_as_one_liners(lab_with_data):
    lab, one, _ = lab_with_data
    data = one.make_PlotData("$x$ [m]", "$y$ [m]")
    one.plot_data("points", data)
    result = one.regression("fit", straight, data)
    assert result.values == pytest.approx([2.0, 1.0])
    lab.build()


# --- tables from a folder ---


def test_tables_have_the_folder_structure_of_the_csv_files(tmp_path):
    data = tmp_path / "data"
    (data / "circuits" / "rc").mkdir(parents=True)
    for path in (data / "top.csv", data / "circuits" / "a.csv", data / "circuits" / "rc" / "a.csv"):
        path.write_text("U [V],I [A]\n1,2\n", encoding="utf-8")
    lab = Project(tmp_path / "build", raw_data_folder=data)
    lab.create_latex_tables_from_raw_data()
    lab.build()
    tables = tmp_path / "build" / "tables"
    found = sorted(p.relative_to(tables).as_posix() for p in tables.rglob("*.tex"))
    assert found == ["circuits/a.tex", "circuits/rc/a.tex", "top.tex"]
    tex = (tables / "circuits" / "rc" / "a.tex").read_text(encoding="utf-8")
    assert "tab:circuits_rc_a_raw" in tex


def test_tables_from_folder_skip_the_build_folder(tmp_path):
    (tmp_path / "m.csv").write_text("U [V]\n1\n", encoding="utf-8")
    lab = Project(tmp_path / "build")
    table = lab.edit_csv(tmp_path / "m.csv")
    lab.build()  # copies m.csv into build/data/m/
    lab2 = Project(tmp_path / "build")
    lab2.create_latex_tables_from_raw_data(tmp_path)
    assert len(lab2._artifacts) == 1
    assert table.name == "m"


# --- find_columns ---


def test_find_columns_prints_a_header_and_variables_for_every_csv(tmp_path, capsys):
    data = tmp_path / "data"
    (data / "rc").mkdir(parents=True)
    (data / "a.csv").write_text("f [Hz],U_e [V]\n1,2\n", encoding="utf-8")
    (data / "rc" / "b.csv").write_text("f [Hz],$U_a$ [V]\n1,2\n", encoding="utf-8")
    Project(tmp_path / "build", raw_data_folder=data).find_columns()
    out = capsys.readouterr().out
    assert out.index("# a.csv") < out.index("# rc/b.csv")
    assert 'U_e = "U_e [V]"' in out
    assert 'U_a = "$U_a$ [V]"' in out
    assert out.count('f = "f [Hz]"') == 2  # the same column keeps the same variable


def test_raw_data_functions_need_a_folder(tmp_path):
    lab = Project(tmp_path / "build")
    with pytest.raises(ValueError, match="raw_data_folder"):
        lab.find_columns()
    with pytest.raises(ValueError, match="raw_data_folder"):
        lab.create_latex_tables_from_raw_data()
