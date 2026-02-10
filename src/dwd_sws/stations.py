import re
import requests
import bz2
import pandas as pd
from pathlib import Path
from typing import List, Optional
from .urls import DEFAULT_SWS_QA_URL, DEFAULT_SWS_STATIONS_CATALOG_URL

def list_station_codes(base_url: str = DEFAULT_SWS_QA_URL) -> List[str]:
    """
    Scrapes the DWD OpenData directory listing to find available station codes.
    Expects filenames like 'observation_{CODE}.xml.bz2'.
    """
    try:
        resp = requests.get(base_url, timeout=30)
        resp.raise_for_status()
        # Pattern: match href="observation_..." or just the text
        # Content example: <a href="observation_A006.xml.bz2">
        # Regex: observation_([A-Za-z0-9]+)\.xml\.bz2
        pattern = re.compile(r'observation_([A-Za-z0-9]+)\.xml\.bz2')
        codes = sorted(list(set(pattern.findall(resp.text))))
        return codes
    except Exception as e:
        print(f"Error listing stations: {e}")
        return []

def fetch_station_catalog(
    catalog_url: str = DEFAULT_SWS_STATIONS_CATALOG_URL,
    cache_path: str = "data/swsKatalog.csv"
) -> Path:
    """
    Downloads and decompresses the SWS station catalog (CSV) if not already cached.
    """
    path = Path(cache_path)
    if path.exists():
        return path
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading station catalog from {catalog_url}...")
    resp = requests.get(catalog_url, timeout=30)
    resp.raise_for_status()
    
    # Decompress bz2 content
    try:
        content = bz2.decompress(resp.content)
    except OSError:
        # Fallback if it's not compressed (just in case)
        content = resp.content

    with open(path, "wb") as f:
        f.write(content)
    
    return path

def load_station_metadata(path_or_url: Optional[str] = None) -> pd.DataFrame:
    """
    Loads station metadata (Code, Name, Lat, Lon) from local CSV or URL.
    Returns a DataFrame with standardized columns: ['station_code', 'name', 'lat', 'lon'].
    """
    if path_or_url is None:
        try:
            path_or_url = str(fetch_station_catalog())
        except Exception as e:
            print(f"Warning: Could not fetch station catalog from remote: {e}")
            if Path("data/swsKatalog.csv").exists():
                path_or_url = "data/swsKatalog.csv"
            else:
                return pd.DataFrame(columns=['station_code', 'name', 'lat', 'lon'])

    try:
        if not Path(path_or_url).exists():
             return pd.DataFrame(columns=['station_code', 'name', 'lat', 'lon'])
             
        # Read CSV with German format (semicolon sep, comma decimal)
        # Columns observed: Kennung;Name;Streckentyp...;Breite;Laenge;...
        df = pd.read_csv(path_or_url, sep=';', decimal=',', encoding='latin1') 
        # encoding='latin1' or 'utf-8' is guess, strict often fails on German names
        
        col_map = {}
        for col in df.columns:
            lower = str(col).lower()
            if any(k in lower for k in ['kennung', 'station_code', 'id', 'code']):
                col_map[col] = 'station_code'
            elif any(k in lower for k in ['name', 'standort']):
                col_map[col] = 'name'
            elif any(k in lower for k in ['breite', 'lat']):
                col_map[col] = 'lat'
            elif any(k in lower for k in ['laenge', 'länge', 'lon']):
                col_map[col] = 'lon'
        
        df = df.rename(columns=col_map)
        
        if 'station_code' not in df.columns and not df.empty:
            # Fallback: assume first column is code
            df = df.rename(columns={df.columns[0]: 'station_code'})

        # Ensure numeric lat/lon
        for c in ['lat', 'lon']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        final_cols = [c for c in ['station_code', 'name', 'lat', 'lon'] if c in df.columns]
        return df[final_cols].dropna(subset=['station_code'])
        
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return pd.DataFrame(columns=['station_code', 'name', 'lat', 'lon'])