# Installation

There are two packages in one repository. Install what you need where you need it:

| Package | Python | Where |
| --- | --- | --- |
| `pemlab` (evaluation) | 3.10 or newer | your own computer |
| `pemlab-instruments` (measuring) | 3.8 or newer | the lab computers |

Neither is on PyPI, they are installed from GitHub.

## pemlab (evaluation)

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

## pemlab-instruments (measuring)

With git:

```bash
pip install "git+https://github.com/EliasMendeUni/pemlab.git#subdirectory=instruments"
```

### On a lab computer without git

1. Download the repository as ZIP in the browser
   (<https://github.com/EliasMendeUni/pemlab/archive/refs/heads/main.zip>) and unzip it.
2. Open a terminal in the unzipped folder, activate the environment you want to use, then:

   ```bash
   cd instruments
   python -m pip install .
   ```

   `python -m pip` installs into exactly the Python that `python` starts. Check with
   `python --version` (3.8 or newer) and `python -m pip list`.

### If pip reports conflicts with installed packages

pemlab-instruments only needs numpy, matplotlib and pyvisa. If pip wants to change packages
that must not change, install without dependencies and add only what is missing:

```bash
python -m pip install --no-deps .
python -m pip install pyvisa pyvisa-py      # only what `import pemlab_instruments` complains about
```

### Without installing at all

`pemlab_instruments` is a plain folder. Copy `instruments/src/pemlab_instruments` next to your
measurement script; `import pemlab_instruments` then finds it. numpy, matplotlib and pyvisa must be
installed. This also works for a single USB stick.

## For development

Use a second environment in which both packages are installed *editable*. They point to your
clone, so every change takes effect immediately and no commit is needed:

```bash
git clone https://github.com/EliasMendeUni/pemlab.git
cd pemlab
conda create -n pemlab-dev python=3.13
conda activate pemlab-dev
pip install -e ".[dev]"
pip install -e "./instruments[dev]"
```

Check that the editable install is active:

```bash
python -c "import pemlab; print(pemlab.__file__)"
```

The path must lead into your clone (`.../pemlab/src/pemlab/__init__.py`), not into
`site-packages`.

Run the tests of the two packages separately:

```bash
pytest
pytest instruments
```

## Build this documentation

```bash
pip install -e ".[docs]" -e ./instruments
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
