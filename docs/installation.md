# Installation

pemlab needs **Python 3.10 or newer**. It is not on PyPI, you install it from GitHub.

## For your lab reports

Use a separate environment that contains the released state of pemlab:

```bash
conda create -n praktikum python=3.13
conda activate praktikum
pip install git+https://github.com/EliasMendeUni/pemlab.git
```

Update later with:

```bash
pip install -U --force-reinstall --no-deps git+https://github.com/EliasMendeUni/pemlab.git
```

For Jupyter notebooks add the kernel and select this environment in your editor:

```bash
pip install ipykernel
```

## For development

Use a second environment in which pemlab is installed *editable*. It points to your clone, so
every change takes effect immediately and no commit is needed:

```bash
git clone https://github.com/EliasMendeUni/pemlab.git
cd pemlab
conda create -n pemlab-dev python=3.13
conda activate pemlab-dev
pip install -e ".[dev]"
```

Check that the editable install is active:

```bash
python -c "import pemlab; print(pemlab.__file__)"
```

The path must lead into your clone (`.../pemlab/src/pemlab/__init__.py`), not into
`site-packages`.

## Build this documentation

```bash
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
```

## LaTeX packages

The generated `.tex` files need these packages in the preamble of your report:

```latex
\usepackage{graphicx}   % plots
\usepackage{booktabs}   % tables
\usepackage{siunitx}    % quantities such as \SI{0.01}{V}
\usepackage{float}      % tables and plots stay exactly where you \input them
```
