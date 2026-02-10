# DWD Road Weather Stations (SWS) Visualization

A Python library and interactive dashboard for DWD Road Weather Stations.

## Try it Online (Voila + Binder)

Launch the SWSMOS Dashboard directly in your browser - no installation required:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dadiyorto-wendi/dwd-sws-vis/HEAD?urlpath=voila%2Frender%2Fnotebooks%2Fswsmos_dashboard.ipynb)

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

### Interactive Dashboard (Jupyter)

1. Start Jupyter Lab:
   ```bash
   jupyter lab
   ```
2. Open `notebooks/interactive_map.ipynb`.
3. Run the cells to launch the dashboard.

### Library Usage

```python
from dwd_sws import list_station_codes
from dwd_sws.snapshot import download_snapshot, parse_snapshot

# List stations
codes = list_station_codes()
print(f"Found {len(codes)} stations")

# Get data for a station
code = "A006" # Example
xml_bytes = download_snapshot(code)
data = parse_snapshot(xml_bytes)
print(data['numeric'])
```

## Development

Run tests:
```bash
pytest
```
