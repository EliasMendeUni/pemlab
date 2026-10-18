"""Beispiel-Auswertung: zwei Messreihen, zwei Plots, ein Bericht.

Start: python analyse.py  (läuft aus jedem Ordner, alle Pfade hängen am Ort dieser Datei)
Alles landet in ./_build (wird bei jedem Lauf komplett neu erzeugt) und wird in main.tex
mit \\input eingebunden.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pemlab import Project

HERE = Path(__file__).parent

# Build-Ordner einmal festlegen. Am Ende schreibt lab.build() alles dorthin.
# tex_prefix: so findet LaTeX den Build-Ordner, wenn main.tex neben diesem Skript liegt.
lab = Project(HERE / "_build", tex_prefix="_build")


# --- Messreihe 1: ohmscher Widerstand (data/widerstand.csv: "U [V]", "I [mA]") -----------

widerstand = lab.edit_csv(HERE / "data" / "widerstand.csv", name="widerstand")

# Eine Spalte ändern statt eine neue anzulegen: aus "I [mA]" wird "I [A]".
# In der Formel steht I für die alte Spalte. Die Rohdatei bleibt unverändert.
widerstand.replace_column("I [mA]", "I [A]", "I * 1e-3")

# Fehler der Spannung: Gerätegenauigkeit als Konstante (die CSV hat keine sigma-Spalte).
widerstand.add_uncertainty(r"$\sigma_U$ [V]", "U", sigmas={"U": 0.01})

# Neue Spalte mit Formel, auf 1 Nachkommastelle gerundet. Namen dürfen Math-Text enthalten.
widerstand.add_column(r"$R$ [\Omega]", "U / I", decimals=1)

# Fehlerfortpflanzung (analytisch): der Fehler von U kommt automatisch aus der Spalte
# "$\sigma_U$ [V]" (Symbol sigma_U), für I gibst du den Fehler als Konstante an.
widerstand.add_uncertainty(
    r"$\sigma_R$ [\Omega]", "U / I", sigmas={"I": 2e-5}, decimals=1
)

analyse_widerstand = lab.analysis(widerstand)
daten_widerstand = analyse_widerstand.make_PlotData("I [A]", "U [V]", r"$\sigma_U$ [V]")


def ohm(x, R):
    return R * x


# Regression: Funktion, Plot, Parameter mit Fehler und die verwendeten Berechnungen
# landen zusammen in build/plots/ohmsches_gesetz/ohmsches_gesetz.tex
analyse_widerstand.regression("ohmsches_gesetz", ohm, daten_widerstand)


# --- Messreihe 2: RC-Tiefpass (data/tiefpass.csv: f, U_in, U_out, sigma_U_out) -------------

tiefpass = lab.edit_csv(HERE / "data" / "tiefpass.csv", name="tiefpass")

# Spalten ohne Einheit sind möglich (Verstärkung ist dimensionslos).
tiefpass.add_column("H", "U_Out / U_In", decimals=4)

# sigma_U_out steht schon in der CSV und wird automatisch gefunden, U_in bekommt eine Konstante.
tiefpass.add_uncertainty(r"$\sigma_H$", "U_Out / U_In", sigmas={"U_In": 0.01}, decimals=4)

analyse_tiefpass = lab.analysis(tiefpass)
daten_tiefpass = analyse_tiefpass.make_PlotData("f [Hz]", "H", r"$\sigma_H$")


def tiefpass_modell(x, f_g):
    return 1 / np.sqrt(1 + (x / f_g) ** 2)


# Bei nichtlinearen Funktionen helfen Startwerte (p0) dem Fit.
analyse_tiefpass.regression("tiefpass_gain", tiefpass_modell, daten_tiefpass, p0=[1500])


# --- Rohdaten als Tabellen und alles schreiben ---------------------------------------------

lab.tables_from_folder(HERE / "data")  # eine LaTeX-Tabelle pro CSV in data/
lab.build()

#plt.show()  # optional: Plots am Bildschirm ansehen
