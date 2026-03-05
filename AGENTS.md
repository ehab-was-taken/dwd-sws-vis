# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

DWD SWS Vis — a Python library and Jupyter-based dashboard for visualizing DWD (German Weather Service) Road Weather Station data. Single Python package, not a monorepo. No Docker, databases, or backend services required.

### Development environment

- **Python 3.12** with a virtualenv at `.venv/`
- Install: `pip install -e ".[test]"` (editable mode with pytest)
- Activate: `source .venv/bin/activate`

### Running services

- **Jupyter Lab**: `jupyter lab --no-browser --ip=0.0.0.0 --port=8888 --ServerApp.token='' --ServerApp.password=''`
- Open `notebooks/interactive_map.ipynb` (observation dashboard) or `notebooks/swsmos_dashboard.ipynb` (SWSMOS forecast dashboard) and run all cells.
- Both dashboards require internet access to `opendata.dwd.de` for live data. Cached/fallback data exists in `data/` for the station catalog.

### Testing

- `pytest` — runs 3 unit tests in `tests/` (mocked, no network needed)
- No linter is configured in the project. All source files in `src/dwd_sws/` should compile cleanly (`python -m py_compile`).

### Key caveats

- The `requirements.txt` is for Binder deployment only (includes `voila`). For development, use `pyproject.toml` via `pip install -e ".[test]"`.
- `python3.12-venv` system package must be installed (`sudo apt-get install -y python3.12-venv`) before creating the virtualenv.
- The library's `list_station_codes()` makes a live HTTP request to DWD OpenData; tests mock this via `unittest.mock`.
