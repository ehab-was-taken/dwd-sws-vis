import re
import requests
import bz2
import pandas as pd
from io import BytesIO
from typing import List, Optional
from .urls import DEFAULT_SWSMOS_URL

def list_forecast_files(base_url: str = DEFAULT_SWSMOS_URL) -> List[str]:
    """
    Scrapes the DWD SWSMOS directory to find available forecast files.
    Expects filenames like 'swsmos_YYYYMMDDHHmmss_opendata.csv.bz2'.
    """
    try:
        resp = requests.get(base_url, timeout=30)
        resp.raise_for_status()
        # Regex: swsmos_([0-9]+)_opendata\.csv\.bz2
        pattern = re.compile(r'swsmos_([0-9]+)_opendata\.csv\.bz2')
        files = sorted(list(set(pattern.findall(resp.text))))
        # Return full filenames for convenience
        return [f"swsmos_{ts}_opendata.csv.bz2" for ts in files]
    except Exception as e:
        print(f"Error listing forecast files: {e}")
        return []

def load_forecast_data(filename: str, base_url: str = DEFAULT_SWSMOS_URL) -> pd.DataFrame:
    """
    Downloads and parses a SWSMOS forecast CSV file.
    Returns a DataFrame with columns: 
    ['ID', 'Lat', 'Lon', 'timestamp_utc', 'TL', 'TS', 'TD', ... and others]
    """
    url = f"{base_url.rstrip('/')}/{filename}"
    print(f"Fetching {url}...")
    
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        
        # Decompress
        csv_content = bz2.decompress(resp.content)
        
        df = pd.read_csv(
            BytesIO(csv_content), 
            sep=';', 
            skiprows=[1], # Skip the second line (index 1) which is just the run time
            dtype={'ID': str},
            low_memory=False
        )
        
        # Parse timestamp
        if 'YYYYMMDDHHmm' in df.columns:
            df['timestamp_utc'] = pd.to_datetime(df['YYYYMMDDHHmm'], format='%Y%m%d%H%M', errors='coerce')
            
        # Ensure numeric for known variables
        # Iterate over columns that shouldn't be string
        exclude = ['ID', 'YYYYMMDDHHmm', 'timestamp_utc']
        for col in df.columns:
            if col not in exclude:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
        
    except Exception as e:
        print(f"Error loading forecast data: {e}")
        return pd.DataFrame()
