"""Tests of NumberStyle: only the display is rounded, small numbers get e-notation."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pemlab import NumberStyle, Project
from pemlab.formulas import fit_expression_latex


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "ohm.csv"
    path.write_text("U [V],I [A]\n1.5,0.0003\n3.0,0.0006\n4.5,0.0009\n", encoding="utf-8")
    return path


def read(path):
    return path.read_text(encoding="utf-8")


# --- NumberStyle ---


def test_small_numbers_get_e_notation():
    numbers = NumberStyle()
    assert numbers.number(0.001) == "1.000e-3"
    assert numbers.number(0.00000000006) == "6.000e-11"
    assert numbers.number(0.05) == "0.05000"
    assert numbers.number(123456) == "1.235e5"


def test_thresholds_are_adjustable():
    numbers = NumberStyle(sci_below=1e-4, sci_above=1e3)
    assert numbers.number(0.001) == "0.001000"
    assert numbers.number(5000) == "5.000e3"


def test_value_error_plain_and_scientific():
    numbers = NumberStyle()
    assert numbers.value_error(469.74, 0.31) == ("469.74", "0.31")
    assert numbers.value_error(2.848e-9, 3.7e-12) == ("2.8480e-9", "0.0037e-9")
    assert numbers.value_error(0.0, 3.0e-5) == ("0.0e-5", "3.0e-5")  # value 0: like the error


def test_error_digits():
    assert NumberStyle(error_digits=1).value_error(2.848e-9, 3.7e-12) == ("2.848e-9", "0.004e-9")


def test_cell_keeps_digits_unless_asked():
    assert NumberStyle().cell("0.6740") == "0.6740"
    assert NumberStyle().cell("0.0000674") == "6.74e-5"
    assert NumberStyle(decimals=2).cell("0.6740") == "0.67"
    assert NumberStyle(decimals=2).cell("0.0000674") == "6.74e-5"
    assert NumberStyle().cell("abc") == "abc"


def test_invalid_values_are_rejected():
    with pytest.raises(ValueError):
        NumberStyle(decimals=-1)
    with pytest.raises(ValueError):
        NumberStyle(sci_below=1.0, sci_above=0.1)


# --- csv keeps the full values ---


def test_columns_are_not_rounded(tmp_path, csv_file):
    lab = Project(tmp_path / "build")
    table = lab.edit_csv(csv_file)
    table.add_column("R [Ohm]", "U / I", numbers=NumberStyle(decimals=1))
    assert table.column("R [Ohm]")[0] == pytest.approx(5000.0)
    table.add_column("x [m]", "I / 3")
    lab.build()
    saved = pd.read_csv(tmp_path / "build" / "data" / "ohm" / "ohm.csv")
    assert saved["x [m]"][0] == pytest.approx(1e-4, rel=1e-9)
    tex = read(tmp_path / "build" / "data" / "ohm" / "ohm.tex")
    assert r"\num{1.000e-4}" in tex  # computed column: 4 significant digits, not 0.0001


def test_table_shows_rounded_and_scientific(tmp_path, csv_file):
    lab = Project(tmp_path / "build")
    table = lab.edit_csv(csv_file)
    table.add_column("R [Ohm]", "U / I", numbers=NumberStyle(decimals=1))
    lab.build()
    tex = read(tmp_path / "build" / "data" / "ohm" / "ohm.tex")
    assert "5000.0" in tex  # column style: one decimal
    assert r"\num{3e-4}" in tex  # I = 0.0003 is below 0.01


def test_project_default_style_reaches_raw_tables(tmp_path, csv_file):
    lab = Project(tmp_path / "build", numbers=NumberStyle(sci_below=1e-6, decimals=2))
    lab.tables_from_folder(csv_file.parent)
    lab.build()
    tex = read(tmp_path / "build" / "tables" / "ohm" / "ohm.tex")
    assert "1.50" in tex and "0.00" in tex  # decimals=2, nothing in e-notation
    assert "num" not in tex


# --- add_column without assigning the columns ---


def test_variables_are_column_names(tmp_path, csv_file):
    table = Project(tmp_path / "build").edit_csv(csv_file)
    table.add_column("P [W]", "U * I")
    assert table.column("P [W]")[1] == pytest.approx(3.0 * 0.0006)


def test_explicit_assignment_still_works(tmp_path, csv_file):
    table = Project(tmp_path / "build").edit_csv(csv_file)
    table.add_column("P [W]", "a * b", a="U [V]", b="I [A]")
    assert table.column("P [W]")[0] == pytest.approx(1.5 * 0.0003)


def test_unknown_variable_names_the_problem(tmp_path, csv_file):
    table = Project(tmp_path / "build").edit_csv(csv_file)
    with pytest.raises(ValueError, match="keine Spalte gleichen Namens"):
        table.add_column("P [W]", "U * Z")


def test_ambiguous_variable_is_an_error(tmp_path):
    path = tmp_path / "two.csv"
    path.write_text("I [A],I [mA]\n1,1000\n", encoding="utf-8")
    table = Project(tmp_path / "build").edit_csv(path)
    with pytest.raises(ValueError, match="mehreren Spalten"):
        table.add_column("x", "I * 2")
    table.add_column("x", "I * 2", I="I [A]")
    assert table.column("x")[0] == 2


def test_math_names_are_found(tmp_path):
    path = tmp_path / "math.csv"
    path.write_text("$R_x$ [$k\\Omega$],$f_{res}$ [kHz]\n100,2\n", encoding="utf-8")
    table = Project(tmp_path / "build").edit_csv(path)
    table.add_column("y", "1 / (R_x * 1e3) + f_res")
    assert table.column("y")[0] == pytest.approx(1e-5 + 2)


def test_replace_column_uses_the_old_column(tmp_path, csv_file):
    table = Project(tmp_path / "build").edit_csv(csv_file)
    table.replace_column("I [A]", "I [mA]", "I * 1e3")
    assert list(table.df.columns) == ["U [V]", "I [mA]"]
    assert table.column("I [mA]")[0] == pytest.approx(0.3)


def test_old_decimals_argument_is_explained(tmp_path, csv_file):
    table = Project(tmp_path / "build").edit_csv(csv_file)
    with pytest.raises(ValueError, match="NumberStyle"):
        table.add_column("P [W]", "U * I", decimals=2)


def test_calculations_are_hidden_by_default(tmp_path, csv_file):
    lab = Project(tmp_path / "build")
    table = lab.edit_csv(csv_file)
    table.add_column("P [W]", "U * I")
    table.add_column("Q [W]", "U * I * 2", show=True)
    lab.build()
    tex = read(tmp_path / "build" / "data" / "ohm" / "ohm.tex")
    assert "Calculations" in tex and "Q" in tex
    assert "P" not in tex.split("Calculations")[1]


# --- fit result and formula ---


def test_fit_result_in_scientific_notation(tmp_path):
    path = tmp_path / "c.csv"
    x = np.linspace(1e-5, 1e-4, 8)
    rows = "\n".join(f"{v},{3.5e8 * v + 1000 + i * 0.01}" for i, v in enumerate(x))
    path.write_text("$x$ [1/Ohm],$y$ [1/s]\n" + rows + "\n", encoding="utf-8")
    lab = Project(tmp_path / "build")
    analysis = lab.analysis(path)

    def line(x, slope, offset):
        return slope * x + offset

    data = analysis.make_PlotData("$x$ [1/Ohm]", "$y$ [1/s]")
    analysis.regression("fit", line, data, p0=[1e8, 0])
    lab.build()
    tex = read(tmp_path / "build" / "plots" / "fit" / "fit.tex")
    assert r"\num{3.5" in tex and "e8}" in tex


def test_formula_of_a_math_column_is_valid_latex():
    R_O = 1e6

    def kapazität(R_x_inv, C_ges):
        return 1 / C_ges * (R_x_inv + 1 / R_O)

    latex = fit_expression_latex(kapazität, r"\frac{1}{R_x}")
    assert latex is not None and "frac1" not in latex
    assert r"\frac{1}{R_x}" in latex and "C_{ges}" in latex


def test_numpy_arc_functions_are_known():
    def arc(x, a):
        return a * np.arctan(x)

    assert "atan" in (fit_expression_latex(arc, "x") or "")


def test_unit_change_keeps_the_digits_but_new_columns_get_four(tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("$C_x$ [nF],f [kHz]\n1.5595,3\n", encoding="utf-8")
    lab = Project(tmp_path / "build")
    table = lab.edit_csv(path)
    table.replace_column("$C_x$ [nF]", "$C_x$ [F]", "C_x * 1e-9")
    table.add_column("y [1]", "f / 7")
    lab.build()
    tex = read(tmp_path / "build" / "data" / "c" / "c.tex")
    assert r"\num{1.5595e-9}" in tex  # a unit change is not a calculation: all digits stay
    assert "0.4286" in tex  # f / 7 = 0.428571...: four significant digits


def test_set_column_is_shown_with_significant_digits(tmp_path, csv_file):
    lab = Project(tmp_path / "build")
    table = lab.edit_csv(csv_file)
    table.set_column("w [1]", [3918.92509304, 4291.17235094, 4777.02840883])
    lab.build()
    saved = pd.read_csv(tmp_path / "build" / "data" / "ohm" / "ohm.csv")
    assert saved["w [1]"][0] == pytest.approx(3918.92509304)
    tex = read(tmp_path / "build" / "data" / "ohm" / "ohm.tex")
    assert "3919 " in tex and "3918.925" not in tex
    with pytest.raises(ValueError, match="Zeilen"):
        table.set_column("v [1]", [1.0])
