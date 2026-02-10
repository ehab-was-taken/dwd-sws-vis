import pandas as pd
from pathlib import Path
from typing import List, Optional
from .snapshot import download_snapshot, parse_snapshot

def update_timeseries(
    station_code: str,
    variables: Optional[List[str]] = None,
    out_csv: str = "data/timeseries_{code}.csv"
) -> pd.DataFrame:
    """
    Fetches the latest snapshot for a station and appends it to the local CSV.
    """
    # Resolve CSV path
    file_path = Path(out_csv.format(code=station_code))
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Fetch
    try:
        data_bytes = download_snapshot(station_code)
        records = parse_snapshot(data_bytes) # Now returns list
    except Exception as e:
        print(f"Update failed for {station_code}: {e}")
        if file_path.exists():
            return pd.read_csv(file_path)
        return pd.DataFrame()

    if not records:
        return pd.DataFrame()

    # Flatten for DataFrame
    flattened_rows = []
    for rec in records:
        row = {"timestamp_utc": rec["timestamp_utc"]}
        if variables:
            for v in variables:
                row[v] = rec["numeric"].get(v, None)
        else:
            # Take all numeric fields found in this record
            # (In measure-list mode, keys are short like 'at', 'st')
            row.update(rec["numeric"])
        flattened_rows.append(row)
    
    new_df = pd.DataFrame(flattened_rows)
    
    # Load existing
    if file_path.exists():
        existing_df = pd.read_csv(file_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
        
    # Deduplicate by timestamp
    if not combined_df.empty and "timestamp_utc" in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=['timestamp_utc'], keep='last')
        combined_df = combined_df.sort_values(by='timestamp_utc')
    
    combined_df.to_csv(file_path, index=False)
    return combined_df

def load_timeseries(
    station_code: str,
    csv_path: str = "data/timeseries_{code}.csv"
) -> pd.DataFrame:
    """
    Loads the local timeseries CSV for a station.
    """
    file_path = Path(csv_path.format(code=station_code))
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)

def available_variables_from_timeseries(df: pd.DataFrame) -> List[str]:
    """
    Returns list of numeric variable columns (excluding timestamp).
    """
    return [c for c in df.columns if c != "timestamp_utc"]
