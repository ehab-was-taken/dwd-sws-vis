import ipywidgets as widgets
from ipyleaflet import Map, Marker, MarkerCluster, basemaps, WMSLayer
import matplotlib.pyplot as plt
from IPython.display import display
import pandas as pd
from typing import Optional
from .stations import load_station_metadata
from .swsmos import list_forecast_files, load_forecast_data
from .variables import get_variable_label, get_variable_unit

# SWSMOS Variable Descriptions (Subset)
SWSMOS_VARS = {
    "TL": {"desc": "Air Temperature (2m)", "unit": "°C"},
    "TS": {"desc": "Surface Temperature", "unit": "°C"},
    "TD": {"desc": "Dew Point Temperature", "unit": "°C"},
    "TLSTA": {"desc": "Air Temperature (Reference)", "unit": "°C"},
    "RR6": {"desc": "Precipitation (6h)", "unit": "mm"},
    "R650": {"desc": "Precip Probability (>5mm/6h)", "unit": "%"},
    "RC": {"desc": "Road Condition Code", "unit": "code"},
    "WWL6": {"desc": "Liquid Precip Probability (6h)", "unit": "%"},
    "WWS3": {"desc": "Solid Precip Probability (3h)", "unit": "%"},
    "RRL1c": {"desc": "Liquid Precip Rate", "unit": "mm/h"},
    "RRS1c": {"desc": "Solid Precip Rate", "unit": "mm/h"},
    "RRS3c": {"desc": "Solid Precip Rate (3h)", "unit": "mm/3h"}
}

# Road Condition Codes (Revised according to DWD guide)
RC_LABELS = {
    1: "Dry",
    2: "Wet",
    3: "Snow",
    4: "Frost",
    5: "Freezing wet conditions",
    6: "Black ice"
}

# Distinct colors for RC codes
RC_COLORS = {
    1: "green",
    2: "blue",
    3: "lightgray", # Snow (white is hard to see)
    4: "cyan",      # Frost
    5: "purple",    # Freezing wet
    6: "black"      # Black ice
}

class SWSMOSDashboard:
    def __init__(self, catalog_df: pd.DataFrame):
        self.catalog = catalog_df
        self.forecast_df = pd.DataFrame()
        self.station_code = None
        self.variable = "TL" # Default
        self._is_loading = False # Guard to prevent duplicate plots during setup
        
        # UI Components
        self.output_plot = widgets.Output()
        self.lbl_status = widgets.Label(value="Initializing...")
        
        # 1. Forecast File Selector
        self.dropdown_file = widgets.Dropdown(description="Forecast Run:", options=[], disabled=True, layout=widgets.Layout(width='50%'))
        self.btn_load_file = widgets.Button(description="Load Data", disabled=True, icon="cloud-download", tooltip="Download and parse the selected forecast file")
        
        # 2. Station Selector
        self.select_station_ui = widgets.Combobox(
            placeholder='Type station code (e.g. A006)',
            description='Station:',
            ensure_option=True,
            disabled=True
        )
        
        # 3. Variable Selector
        self.dropdown_var = widgets.Dropdown(description="Variable:", options=list(SWSMOS_VARS.keys()), value="TL", disabled=True)
        
        # Map
        self.map_widget = Map(center=(51.1657, 10.4515), zoom=6, basemap=basemaps.OpenStreetMap.Mapnik)
        self._init_highway_layer()
        self._init_markers()

        # Layout
        self.controls_file = widgets.HBox([self.dropdown_file, self.btn_load_file])
        self.controls_station = widgets.HBox([self.select_station_ui, self.dropdown_var])
        self.layout = widgets.VBox([
            self.lbl_status,
            self.controls_file,
            widgets.HTML("<i>Select a Forecast Run and click Load. Each file contains a ~7-day forecast for all stations.</i>"),
            self.map_widget,
            self.controls_station,
            self.output_plot
        ])
        
        # Events
        self.btn_load_file.on_click(self._on_load_file_click)
        self.select_station_ui.observe(self._on_station_change, names='value')
        self.dropdown_var.observe(self._on_var_change, names='value')
        
        # Initial Load
        self._refresh_file_list()

    def _init_highway_layer(self):
        """Adds Autobahn overlay from BASt WMS."""
        highway_wms = WMSLayer(
            url="https://inspire.bast.de/bisstra/strasse_wms",
            layers="bisstra.strasse:tbl_BFStr_Sektor_BAB",
            format="image/png",
            transparent=True,
            name="German Autobahn"
        )
        self.map_widget.add_layer(highway_wms)

    def _refresh_file_list(self):
        self.lbl_status.value = "Fetching file list..."
        try:
            files = list_forecast_files()
            if files:
                options = []
                for f in files:
                    try:
                        # Extract timestamp from filename like swsmos_20260210190000_opendata.csv.bz2
                        ts_str = f.split('_')[1]
                        formatted = f"{ts_str[:4]}-{ts_str[4:6]}-{ts_str[6:8]} {ts_str[8:10]}:{ts_str[10:12]}:{ts_str[12:14]}"
                        options.append((formatted, f))
                    except:
                        options.append((f, f))
                
                self.dropdown_file.options = options
                self.dropdown_file.value = files[-1] # Default to latest (value)
                self.dropdown_file.disabled = False
                self.btn_load_file.disabled = False
                self.lbl_status.value = f"Found {len(files)} forecast runs. Click 'Load Data' to visualize."
            else:
                self.lbl_status.value = "No forecast files found."
        except Exception as e:
            self.lbl_status.value = f"Error listing files: {e}"

    def _init_markers(self):
        # Similar to main dashboard, use catalog for markers
        markers = []
        geo_df = self.catalog.dropna(subset=['lat', 'lon'])
        
        # Optimization: Only show markers, don't attach big data
        for _, row in geo_df.iterrows():
            m = Marker(location=(row['lat'], row['lon']), title=f"{row['station_code']}", draggable=False)
            
            def on_click_wrapper(code=row['station_code'], **kwargs):
                self.select_station_ui.value = code
                
            m.on_click(on_click_wrapper)
            markers.append(m)
            
        if markers:
            cluster = MarkerCluster(markers=markers)
            self.map_widget.add_layer(cluster)

    def _on_load_file_click(self, b):
        filename = self.dropdown_file.value
        if not filename:
            return
            
        self.lbl_status.value = f"Downloading {filename} (approx 2MB)..."
        self.btn_load_file.disabled = True
        self._is_loading = True # Start guard
        
        try:
            self.forecast_df = load_forecast_data(filename)
            if not self.forecast_df.empty:
                count = len(self.forecast_df)
                unique_stations = sorted(self.forecast_df['ID'].astype(str).unique().tolist())
                self.select_station_ui.options = unique_stations
                
                self.lbl_status.value = f"Loaded {count} rows. {len(unique_stations)} stations available."
                self.select_station_ui.disabled = False
                self.dropdown_var.disabled = False
                
                # Update variable options based on actual columns
                cols = [c for c in self.forecast_df.columns if c not in ['ID', 'Lat', 'Lon', 'YYYYMMDDHHmm', 'timestamp_utc']]
                
                def _fmt_var(c):
                    info = SWSMOS_VARS.get(c)
                    if info and isinstance(info, dict):
                        return f"{c} - {info['desc']}"
                    return c

                self.dropdown_var.options = [(_fmt_var(c), c) for c in cols]
                
                # Auto-select a station if none selected, or if current selection is invalid
                if not self.select_station_ui.value or self.select_station_ui.value not in unique_stations:
                    default = "A006" if "A006" in unique_stations else unique_stations[0]
                    self.select_station_ui.value = default
                    self.station_code = default
                
                self._is_loading = False # End guard before explicit plot
                self.plot()
            else:
                self.lbl_status.value = "File loaded but empty."
                self._is_loading = False
        except Exception as e:
            self.lbl_status.value = f"Load failed: {e}"
            self._is_loading = False
        finally:
            self.btn_load_file.disabled = False

    def _on_station_change(self, change):
        if self._is_loading: return
        if change['new'] and not self.forecast_df.empty:
            self.station_code = change['new']
            self.plot()

    def _on_var_change(self, change):
        if self._is_loading: return
        if change['new']:
            self.variable = change['new']
            self.plot()

    def plot(self):
        if self.forecast_df.empty or not self.station_code or not self.variable:
            return
            
        # Filter data
        station_data = self.forecast_df[self.forecast_df['ID'] == self.station_code]
        
        with self.output_plot:
            self.output_plot.clear_output(wait=True)
            # Create a fresh figure using object-oriented approach to avoid global state issues
            fig = plt.figure(figsize=(10, 4))
            ax = fig.add_subplot(111)
            
            try:
                if station_data.empty:
                    ax.text(0.5, 0.5, f"No data for station {self.station_code} in this run.", ha='center')
                else:
                    times = station_data['timestamp_utc']
                    
                    # Get metadata
                    var_info = SWSMOS_VARS.get(self.variable, {})
                    desc = var_info.get('desc', self.variable)
                    unit = var_info.get('unit', '')
                    
                    if unit == "code" and self.variable == "RC":
                        # Categorical scatter plot for Road Condition
                        unique_codes = sorted(station_data[self.variable].dropna().unique())
                        
                        for code in unique_codes:
                            subset = station_data[station_data[self.variable] == code]
                            code_int = int(code)
                            label = RC_LABELS.get(code_int, f"Code {code_int}")
                            color = RC_COLORS.get(code_int, 'gray')
                            
                            ax.scatter(subset['timestamp_utc'], subset[self.variable], 
                                       label=label, c=[color], s=50, edgecolors='black', zorder=3)
                        
                        ax.set_ylabel(f"Condition Code [{unit}]")
                        ax.set_yticks(unique_codes)
                        ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', title="Road Condition")
                        
                    else:
                        # Standard continuous plot for numeric and probabilities
                        ax.plot(times, station_data[self.variable], marker='o', label='Forecast')
                        
                        ylabel = f"{self.variable} [{unit}]" if unit else self.variable
                        ax.set_ylabel(ylabel)
                        ax.legend(loc='best')
                    
                    ax.set_title(f"SWSMOS Forecast: {self.station_code} - {desc}")
                    ax.set_xlabel("Time (UTC)")
                    ax.grid(True, linestyle='--', alpha=0.6)
                
                plt.tight_layout()
                display(fig)
                plt.close(fig)
            except Exception as e:
                print(f"Plotting error: {e}")
                plt.close(fig)

def launch_swsmos():
    """
    Entry point for SWSMOS dashboard.
    """
    print("Loading station catalog...")
    df = load_station_metadata()
    return SWSMOSDashboard(df).layout
