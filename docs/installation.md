# Installation

## For users

Use this if you just want to use Plim in your own project (no need to
edit Plim's own source).

0. (optional) create and activate a dedicated conda environment
   ```bash
   conda create --name plim python=3.10
   conda activate plim
   ```
1. install directly from the GitHub repository
   ```bash
   python -m pip install git+https://github.com/ondrejstranik/plim.git
   ```

This installs the latest version from the `main` branch, along with its
dependencies ([Viscope](https://ondrejstranik.github.io/viscope/) and
[spectralCamera](https://github.com/ondrejstranik/spectralCamera) included).
To upgrade later, re-run the same command with `--upgrade`.

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
   ```bash
   python -m pip install -e .
   ```

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
