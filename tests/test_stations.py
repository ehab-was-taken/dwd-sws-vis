import pandas as pd
from unittest.mock import patch, MagicMock
from dwd_sws.stations import load_station_metadata

def test_load_station_metadata_normalization():
    # Mock return dataframe from read_csv
    mock_df = pd.DataFrame({
        'Kennung': ['A001', 'A002'],
        'Name': ['Station 1', 'Station 2'],
        'Breite': [50.0, 51.0],
        'Laenge': [10.0, 11.0],
        'Extra': [1, 2]
    })
    
    # We need to mock Path.exists to return True
    with patch('dwd_sws.stations.Path.exists', return_value=True):
        # Mock read_csv instead of read_excel
        with patch('pandas.read_csv', return_value=mock_df):
            df = load_station_metadata("dummy.csv")
            
            assert 'station_code' in df.columns
            assert 'lat' in df.columns
            assert 'lon' in df.columns
            assert len(df) == 2
            assert df.iloc[0]['station_code'] == 'A001'
            assert df.iloc[0]['lat'] == 50.0