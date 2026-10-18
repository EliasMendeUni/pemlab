# Beispiel: Praktikumsauswertung mit pemlab

Zwei Messreihen, zwei Plots, ein Bericht. Dieses Beispiel zeigt den ganzen Ablauf.

```bash
python analyse.py     # läuft aus jedem Ordner; erzeugt ./_build neben dem Skript
pdflatex main.tex     # braucht graphicx, booktabs, siunitx, float
```

## Ablauf

1. **`Project("build")`**: Build-Ordner einmal festlegen.
2. **`lab.edit_csv(...)`**: Rohdaten laden (die CSV wird nie verändert) und Spalten ergänzen:
   - `add_column(name, formel, decimals=...)`: neue Spalte aus einer Formel
   - `replace_column(alt, neu, formel)`: Spalte ändern statt eine neue anzulegen
   - `add_uncertainty(name, formel, sigmas={...})`: Fehlerfortpflanzung, analytisch hergeleitet
3. **`lab.analysis(tabelle)`**: Plots und Regressionen
   - `make_PlotData(x, y, y_sigma)`: Spalten über ihren Namen wählen
   - `regression(name, funktion, daten, p0=...)`: Fit, Plot und Ergebnisse
   - `plot_data(name, daten)`: nur die Messpunkte plotten
4. **`lab.tables_from_folder("data")`**: Rohdaten als LaTeX-Tabellen
5. **`lab.build()`**: löscht `build/` und schreibt alles neu

## Regeln für Namen und Formeln

- Spaltennamen haben die Einheit in eckigen Klammern: `U [V]`, `$R$ [\Omega]`.
  Math-Text (`$R_i$`) und `\Omega` sind erlaubt. Eine Spalte ohne Klammern hat keine Einheit.
- In Formeln steht der Name **ohne Einheit**: `"U / I"`, nicht `"U [V] / I [A]"`.
- Der Fehler eines Symbols `X` kommt aus der Spalte mit dem Symbol `sigma_X`, also z. B.
  `sigma_X [V]` oder `$\sigma_X$ [V]`. Fehlt sie, gibst du ihn mit `sigmas={"X": Wert}` an
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
