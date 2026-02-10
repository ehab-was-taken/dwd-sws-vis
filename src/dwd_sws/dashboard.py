import ipywidgets as widgets
from ipyleaflet import Map, Marker, MarkerCluster, basemaps, WMSLayer
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional
from .stations import load_station_metadata
from .timeseries import update_timeseries, load_timeseries, available_variables_from_timeseries
from .variables import get_variable_label, get_variable_unit

class Dashboard:
    def __init__(self, catalog_df: pd.DataFrame, station_code_default: Optional[str] = None):
        self.catalog = catalog_df
        self.station_code = station_code_default
        self.variable = None
        self.ts_df = pd.DataFrame()
        
        # UI Components
        self.output_plot = widgets.Output()
        
        # Station Selector (Combobox allows typing/searching)
        codes = sorted(self.catalog['station_code'].unique().tolist())
        self.select_station_ui = widgets.Combobox(
            placeholder='Type or select station code',
            options=codes,
            description='Station:',
            ensure_option=True,
            value=self.station_code if self.station_code else ""
        )
        
        self.dropdown_var = widgets.Dropdown(description="Variable:", disabled=True)
        self.btn_fetch = widgets.Button(description="Fetch Latest", disabled=True, icon="download")
        self.btn_refresh = widgets.Button(description="Reload CSV", disabled=True, icon="refresh")
        self.lbl_status = widgets.Label(value="Select a station (map or dropdown).")
        
        # Map
        self.map_widget = Map(center=(51.1657, 10.4515), zoom=6, basemap=basemaps.OpenStreetMap.Mapnik)
        self._init_highway_layer()
        self._init_markers()
        
        # Layout
        self.controls_top = widgets.HBox([self.select_station_ui, self.lbl_status])
        self.controls_vars = widgets.HBox([self.dropdown_var, self.btn_fetch, self.btn_refresh])
        self.layout = widgets.VBox([
            self.controls_top,
            self.map_widget,
            self.controls_vars,
            self.output_plot
        ])
        
        # Events
        self.select_station_ui.observe(self._on_station_ui_change, names='value')
        self.dropdown_var.observe(self._on_var_change, names='value')
        self.btn_fetch.on_click(self._on_fetch_click)
        self.btn_refresh.on_click(self._on_refresh_click)

        if self.station_code:
            self.select_station(self.station_code)

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

    def _on_station_ui_change(self, change):
        if change['new'] in self.select_station_ui.options:
            self.select_station(change['new'])

    def _init_markers(self):
        markers = []
        # Filter for rows with coordinates
        geo_df = self.catalog.dropna(subset=['lat', 'lon'])
        for _, row in geo_df.iterrows():
            m = Marker(location=(row['lat'], row['lon']), title=f"{row['station_code']} {row.get('name', '') or ''}", draggable=False)
            setattr(m, 'station_code', row['station_code'])
            
            def on_click_wrapper(code=row['station_code'], **kwargs):
                self.select_station(code)
                # Also update UI dropdown to match
                self.select_station_ui.value = code
                
            m.on_click(on_click_wrapper)
            markers.append(m)
            
        if markers:
            cluster = MarkerCluster(markers=markers)
            self.map_widget.add_layer(cluster)
        else:
            self.lbl_status.value = "Warning: No coordinates found. Use station dropdown."

    def select_station(self, code: str):
        self.station_code = code
        self.lbl_status.value = f"Selected Station: {code}. Loading data..."
        self.btn_fetch.disabled = False
        self.btn_refresh.disabled = False
        
        self.reload_data()

    def reload_data(self):
        if not self.station_code:
            return
            
        self.ts_df = load_timeseries(self.station_code)
        
        # Temporarily disconnect observer to avoid triggering plot() multiple times
        try:
            self.dropdown_var.unobserve(self._on_var_change, names='value')
        except ValueError:
            pass # was not observed

        if self.ts_df.empty:
            self.lbl_status.value = f"No local data for {self.station_code}. Click 'Fetch Latest'."
            self.dropdown_var.options = []
            self.dropdown_var.disabled = True
            with self.output_plot:
                self.output_plot.clear_output()
        else:
            vars_list = available_variables_from_timeseries(self.ts_df)
            dropdown_options = [(get_variable_label(v), v) for v in vars_list]
            
            self.dropdown_var.options = dropdown_options
            self.dropdown_var.disabled = False
            self.lbl_status.value = f"Loaded {len(self.ts_df)} rows for {self.station_code}."
            
            if vars_list:
                if self.variable not in vars_list:
                    self.variable = vars_list[0]
                self.dropdown_var.value = self.variable
        
        # Re-connect observer
        self.dropdown_var.observe(self._on_var_change, names='value')
        
        # Plot once
        self.plot()

    def _on_var_change(self, change):
        if change['new']:
            self.variable = change['new']
            self.plot()

    def _on_fetch_click(self, b):
        if not self.station_code:
            return
        
        self.lbl_status.value = f"Fetching snapshot for {self.station_code}..."
        try:
            update_timeseries(self.station_code) 
            self.reload_data()
        except Exception as e:
            self.lbl_status.value = f"Fetch failed: {e}"

    def _on_refresh_click(self, b):
        self.reload_data()

    def plot(self):
        if self.ts_df.empty or not self.variable:
            return
            
        with self.output_plot:
            self.output_plot.clear_output(wait=True)
            # Use object-oriented approach to avoid global state issues
            fig, ax = plt.subplots(figsize=(10, 4))
            
            try:
                times = pd.to_datetime(self.ts_df['timestamp_utc'])
                ax.plot(times, self.ts_df[self.variable], marker='o')
                
                label = get_variable_label(self.variable)
                unit = get_variable_unit(self.variable)
                
                ax.set_title(f"{self.station_code}: {label}")
                ax.set_xlabel("Time (UTC)")
                ax.set_ylabel(f"{self.variable} [{unit}]" if unit else self.variable)
                ax.grid(True)
                
                plt.tight_layout()
                plt.show()
                # Close the figure to free memory and prevent double display
                plt.close(fig)
            except Exception as e:
                print(f"Plotting error: {e}")
                plt.close(fig)

def build_dashboard(catalog_df: pd.DataFrame, station_code_default=None) -> widgets.VBox:
    dashboard = Dashboard(catalog_df, station_code_default)
    return dashboard.layout

def launch():
    """
    Entry point to build catalog and show dashboard.
    """
    print("Loading station catalog...")
    df = load_station_metadata()
    if df.empty:
        print("Catalog empty. Check network or 'data/SWS_stations.xlsx'.")
        # Try to list codes from directory as fallback if catalog failed
        from .stations import list_station_codes
        codes = list_station_codes()
        if codes:
            print(f"Found {len(codes)} codes from directory listing (no coords).")
            # Create dummy catalog
            df = pd.DataFrame({'station_code': codes, 'lat': [None]*len(codes), 'lon': [None]*len(codes)})
    
    return build_dashboard(df)
