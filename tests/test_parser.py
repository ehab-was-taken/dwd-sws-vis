import pytest
import xml.etree.ElementTree as ET
from dwd_sws.snapshot import parse_snapshot

def test_parse_snapshot_measure_list():
    xml_content = b"""
    <observation>
        <measure-list>
            <measure>
                <observation-time>2026-02-03T12:00:00Z</observation-time>
                <at>12,5</at>
            </measure>
            <measure>
                <observation-time>2026-02-03T12:15:00Z</observation-time>
                <at>12.8</at>
            </measure>
        </measure-list>
    </observation>
    """
    results = parse_snapshot(xml_content)
    
    assert isinstance(results, list)
    assert len(results) == 2
    
    assert results[0]['timestamp_utc'] == '2026-02-03T12:00:00Z'
    assert results[0]['numeric']['at'] == 12.5
    
    assert results[1]['timestamp_utc'] == '2026-02-03T12:15:00Z'
    assert results[1]['numeric']['at'] == 12.8

def test_parse_snapshot_fallback_single():
    xml_content = b"""
    <road_weather_station>
        <header>
            <time>2026-02-03T12:00:00Z</time>
        </header>
        <sensor>
            <air_temp>12,5</air_temp>
            <surface_temp>4.2</surface_temp>
            <status>OK</status>
        </sensor>
    </road_weather_station>
    """
    
    results = parse_snapshot(xml_content)
    assert isinstance(results, list)
    assert len(results) == 1
    result = results[0]
    
    # Check numeric extraction (paths are keys in fallback)
    assert result['numeric']['road_weather_station/sensor/air_temp'] == 12.5
    
    # Check timestamp heuristic
    # It might be in raw or extracted
    assert 'road_weather_station/header/time' in result['raw']
