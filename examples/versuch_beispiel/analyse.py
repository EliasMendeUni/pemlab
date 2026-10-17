r"""Beispiel-Skript für einen Versuch: erzeugt die Tabellen für das Protokoll.

Ausführen (im conda-Env mit installiertem pemlab):
    python analyse.py
Die .tex-Dateien landen in ./build und werden im Protokoll mit \input{build/...} eingebunden.
"""

from pathlib import Path

import pemlab

HIER = Path(__file__).parent
BUILD = HIER / "build"

pemlab.csv_to_tex(
    HIER / "data" / "iv_messdaten.csv",
    BUILD / "tab_iv.tex",
    caption=r"Gemessene $I$--$U$-Kennlinie.",
    label="tab:iv",
    header=[r"$U$ (V)", r"$I$ (A)", r"$\sigma_I$ (A)"],
    decimals={"U [V]": 3, "I [A]": 5, "sigma_I [A]": 5},
)
print(f"Tabellen geschrieben nach {BUILD}")
