# AGENTS.md

## Cursor Cloud specific instructions

This is a Python library + Jupyter dashboard project for visualizing DWD (German Weather Service) road weather station data. No Docker, databases, or backend servers are needed.

### Quick reference

- **Activate venv**: `source .venv/bin/activate`
- **Run tests**: `pytest -v` (3 tests in `tests/`)
- **Lint**: `ruff check src/ tests/` (ruff is installed in venv; no linter is configured by the project itself)
- **Start JupyterLab**: `jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token='' --NotebookApp.password='' --allow-root`
- **Dashboards**: Open `notebooks/swsmos_dashboard.ipynb` or `notebooks/interactive_map.ipynb` in JupyterLab and run all cells.

### Caveats

- The dashboards fetch live data from `opendata.dwd.de` over HTTPS (no auth). Internet access is required.
- The `ipyleaflet` map widget renders only inside Jupyter (not in plain Python scripts).
- The project specifies `python-3.11` in `runtime.txt` (for Binder), but `pyproject.toml` requires `>=3.10`. Python 3.12 works fine.
- No linting tool is configured in the project. `ruff` is installed as a convenience; pre-existing lint warnings (unused imports, bare `except`) exist in the codebase.
