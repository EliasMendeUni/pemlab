"""Beispiel-Auswertung: zwei Messreihen, zwei Plots, ein Bericht.

Start: python analyse.py  (läuft aus jedem Ordner, alle Pfade hängen am Ort dieser Datei)
Alles landet in ./_build (wird bei jedem Lauf komplett neu erzeugt) und wird in main.tex
mit \\input eingebunden.
"""

from pathlib import Path

import numpy as np

from pemlab import Project

HERE = Path(__file__).parent

# Build-Ordner einmal festlegen. Am Ende schreibt lab.build() alles dorthin.
# tex_prefix: so findet LaTeX den Build-Ordner, wenn main.tex neben diesem Skript liegt.
lab = Project(HERE / "_build", tex_prefix="_build")


# --- Messreihe 1: ohmscher Widerstand (data/widerstand.csv: "U [V]", "I [mA]") -----------

# Jeden Spaltennamen einmal als Variable festlegen und dann überall verwenden.
# Name = Beschriftung in Tabelle und Plot: Math-Text ($...$) und \Omega sind erlaubt.
U = "U [V]"
I_mA = "I [mA]"
I = "I [A]"
SIGMA_U = r"$\sigma_U$ [V]"
R = r"$R$ [\Omega]"
SIGMA_R = r"$\sigma_R$ [\Omega]"

widerstand = lab.edit_csv(HERE / "data" / "widerstand.csv", name="widerstand")

# Eine Spalte ändern statt eine neue anzulegen. In der Formel steht eine Variable, der du mit
# I_mA=... eine Spalte zuordnest. Die Rohdatei bleibt unverändert. show=False: diese triviale
# Umrechnung erscheint nicht unter "Calculations".
widerstand.replace_column(I_mA, I, "I_mA * 1e-3", I_mA=I_mA, show=False)

# Fehler der Spannung: Gerätegenauigkeit als Konstante (die CSV hat keine sigma-Spalte).
widerstand.add_uncertainty(SIGMA_U, "U", {"U": 0.01}, U=U)

# Neue Spalte aus einer Formel, auf 1 Nachkommastelle gerundet.
widerstand.add_column(R, "U / I", U=U, I=I, decimals=1)

# Fehlerfortpflanzung (analytisch). sigmas gibt für jede Variable den Fehler an: eine Zahl
# oder den Namen einer Spalte (0 für exakte Größen).
widerstand.add_uncertainty(SIGMA_R, "U / I", {"U": SIGMA_U, "I": 2e-5}, U=U, I=I, decimals=1)

analyse_widerstand = lab.analysis(widerstand)
daten_widerstand = analyse_widerstand.make_PlotData(I, U, SIGMA_U)


def ohm(x, R):
    return R * x


# Regression: Funktion, Plot, Parameter mit Fehler und die verwendeten Berechnungen
# landen zusammen in build/plots/ohmsches_gesetz/ohmsches_gesetz.tex
analyse_widerstand.regression("ohmsches_gesetz", ohm, daten_widerstand)

# Mittelwert der einzelnen Widerstandswerte mit Standardabweichung, Fehler des Mittelwerts und
# Abweichung vom Sollwert (470 Ohm). Mit sigma=SIGMA_R wäre es der gewichtete Mittelwert.
analyse_widerstand.mean("widerstand_mittelwert", R, reference=470)


# --- Messreihe 2: RC-Tiefpass (data/tiefpass.csv: f, U_in, U_out, sigma_U_out) -------------

F = "f [Hz]"
U_IN = "$U_{in}$ [V]"
U_OUT = "$U_{out}$ [V]"
SIGMA_U_OUT = r"$\sigma_{U_{out}}$ [V]"  # so steht es in der Kopfzeile der CSV-Datei
H = "H"  # Spalten ohne Einheit sind möglich (die Verstärkung ist dimensionslos)
SIGMA_H = r"$\sigma_H$"

tiefpass = lab.edit_csv(HERE / "data" / "tiefpass.csv", name="tiefpass")
tiefpass.add_column(H, "U_out / U_in", U_out=U_OUT, U_in=U_IN, decimals=4)
tiefpass.add_uncertainty(
    SIGMA_H, "U_out / U_in", {"U_out": SIGMA_U_OUT, "U_in": 0.01},
    U_out=U_OUT, U_in=U_IN, decimals=4,
)

analyse_tiefpass = lab.analysis(tiefpass)
daten_tiefpass = analyse_tiefpass.make_PlotData(F, H, SIGMA_H)


def tiefpass_modell(x, f_g):
    return 1 / np.sqrt(1 + (x / f_g) ** 2)


# Bei nichtlinearen Funktionen helfen Startwerte (p0) dem Fit.
analyse_tiefpass.regression("tiefpass_gain", tiefpass_modell, daten_tiefpass, p0=[1500])


# --- Rohdaten als Tabellen und alles schreiben ---------------------------------------------

lab.tables_from_folder(HERE / "data")  # eine LaTeX-Tabelle pro CSV in data/
lab.build()

# import matplotlib.pyplot as plt; plt.show()  # optional: Plots am Bildschirm ansehen
