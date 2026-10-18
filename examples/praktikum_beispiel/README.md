# Beispiel: Praktikumsauswertung mit pemlab

Zwei Messreihen, zwei Plots, ein Bericht. Dieses Beispiel zeigt den ganzen Ablauf.

```bash
python analyse.py     # läuft aus jedem Ordner; erzeugt ./_build neben dem Skript
pdflatex main.tex     # braucht graphicx, booktabs, siunitx, float
```

## Ablauf

1. **`Project("build")`**: Build-Ordner einmal festlegen.
2. **`lab.edit_csv(...)`**: Rohdaten laden (die CSV wird nie verändert) und Spalten ergänzen:
   - `add_column(name, formel, U=..., I=..., decimals=...)`: neue Spalte aus einer Formel
   - `replace_column(alt, neu, formel, ...)`: Spalte ändern statt eine neue anzulegen
   - `add_uncertainty(name, formel, sigmas, U=..., ...)`: Fehlerfortpflanzung, analytisch
   - `show=False`: Rechnung nicht unter "Calculations" im Bericht auflisten
3. **`lab.analysis(tabelle)`**: Plots und Regressionen
   - `make_PlotData(x, y, y_sigma)`: Spalten über ihren Namen wählen
   - `regression(name, funktion, daten, p0=...)`: Fit, Plot und Ergebnisse
   - `plot_data(name, daten)`: nur die Messpunkte plotten
   - `mean(name, spalte, sigma=..., reference=...)`: Mittelwert mit Standardabweichung
4. **`lab.tables_from_folder("data")`**: Rohdaten als LaTeX-Tabellen
5. **`lab.build()`**: löscht `build/` und schreibt alles neu

## Regeln für Namen und Formeln

- Ein Spaltenname ist nur eine Beschriftung, am besten mit der Einheit in eckigen Klammern:
  `U [V]`, `$R$ [\Omega]`. Math-Text (`$R_i$`) und `\Omega` sind erlaubt.
- Überall, wo eine Spalte gebraucht wird, übergibst du den **vollen Namen**. Lege jeden Namen
  einmal als Variable an (`U = "U [V]"`) und verwende sie überall.
- `lab.column_names_from_folder("data")` druckt diese Variablen für alle Spalten aller CSV-Dateien
  eines Ordners, sortiert nach Datei. Kopiere sie ins Skript und lösche den Aufruf wieder.
- Die Variablen einer Formel ordnest du Spalten zu: `add_column(R, "U / I", U=U, I=I)`.
- `sigmas` nennt für **jede** Variable den Fehler: eine Zahl oder eine Fehlerspalte
  (`0` für exakte Größen).
- Fit-Funktionen: erstes Argument ist x, die weiteren sind die Parameter, der Rückgabewert steht
  in **einer** `return`-Zeile (dann erscheint die Formel im Bericht).

## Was in `build/` entsteht

```
build/
  data/widerstand/     widerstand.csv, .calc.json, .tex (Tabelle + Berechnungen)
  data/tiefpass/
  plots/ohmsches_gesetz/   ohmsches_gesetz.pdf, .png, .tex (Plot + Regression + Berechnungen)
  plots/tiefpass_gain/
  tables/...               Tabellen der Rohdaten
```

Tabelle bzw. Plot und die zugehörigen Berechnungen stehen jeweils in **einem** LaTeX-Float und
bleiben beim Einbinden zusammen.
