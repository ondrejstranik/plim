# Installation

## For users

Use this if you just want to use Plim in your own project (no need to
edit Plim's own source).

0. (optional) create and activate a dedicated conda environment
   ```bash
   conda create --name plim python=3.10
   conda activate plim
   ```
1. install directly from the GitHub repository, using the `all` extra so
   [Viscope](https://ondrejstranik.github.io/viscope/) and
   [spectralCamera](https://github.com/ondrejstranik/spectralCamera) are
   installed along with it
   ```bash
   python -m pip install "plim[all] @ git+https://github.com/ondrejstranik/plim.git"
   ```
   Without the `[all]` extra, Viscope and spectralCamera are **not** installed.

This installs the latest version from the `main` branch.

2. to upgrade later, force a fresh install of all three packages. A plain
   `--upgrade` is not enough for git dependencies -- pip only checks that the
   URL still matches, not whether the remote has new commits -- so
   `--force-reinstall` is required too (`--no-deps` keeps it from also
   reinstalling every other dependency such as napari):
   ```bash
   python -m pip install --upgrade --force-reinstall --no-deps "plim[all] @ git+https://github.com/ondrejstranik/plim.git" "viscope @ git+https://github.com/ondrejstranik/viscope.git" "spectralCamera @ git+https://github.com/ondrejstranik/spectralCamera.git"
   ```

3. (optional) create Desktop shortcuts for the run scripts
   ```bash
   plim-create-shortcut
   ```
   This adds a "plim" folder to the Desktop containing an icon for each
   `run*` script (e.g. Signal Analyser, Real IFC, Virtual IFC), each
   launching using this environment's Python. Run it again from within the
   environment if the shortcuts are ever lost.

## For developers

Use this if you want to modify Plim itself -- the package is installed
in editable mode, so changes to the source take effect immediately without
reinstalling.

0. clone the repository and move into it
   ```bash
   git clone https://github.com/ondrejstranik/plim.git
   cd plim
   ```
1. create and activate a conda environment
   ```bash
   conda create --name plim python=3.9
   conda activate plim
   ```
2. install the package in editable mode

   - If you're only developing Plim itself (not Viscope or spectralCamera),
     use the `all` extra so they get installed for you from GitHub:
     ```bash
     python -m pip install -e ".[all]"
     ```
   - If you're also a developer of Viscope and/or spectralCamera and already
     have them installed locally (e.g. in editable mode from their own
     repos), leave out the extra so pip doesn't touch them:
     ```bash
     python -m pip install -e .
     ```
     See [Viscope's installation guide](https://ondrejstranik.github.io/viscope/installation/)
     and [spectralCamera's repository](https://github.com/ondrejstranik/spectralCamera)
     for how to install those in editable mode, so that changes to those
     packages take effect immediately too, the same way they do for Plim.

If you use Pylance in VS Code, add the following to `.vscode\settings.json`
so it can resolve the package while it's installed in editable mode:
```json
    "python.languageServer": "Pylance",
    "python.analysis.extraPaths": [
        "path\to\the\package\folder"
    ],
```

## Building the docs locally

Install the `docs` extra and run mkdocs:
```bash
python -m pip install -e .[docs]
mkdocs serve
```
