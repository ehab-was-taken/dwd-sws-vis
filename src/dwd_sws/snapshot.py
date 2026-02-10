import bz2
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .urls import DEFAULT_SWS_QA_URL

def download_snapshot(
    station_code: str,
    base_url: str = DEFAULT_SWS_QA_URL,
    timeout: int = 30
) -> bytes:
    """
    Downloads and decompresses the XML snapshot for a given station.
    """
    filename = f"observation_{station_code}.xml.bz2"
    url = f"{base_url.rstrip('/')}/{filename}"
    
    print(f"Fetching {url}...")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    
    try:
        xml_bytes = bz2.decompress(resp.content)
        return xml_bytes
    except Exception as e:
        raise ValueError(f"Failed to decompress snapshot for {station_code}: {e}")

def parse_snapshot(xml_bytes: bytes) -> list[Dict[str, Any]]:
    """
    Parses the XML snapshot.
    Returns a list of dictionaries, each with:
      - timestamp_utc: str (ISO 8601)
      - numeric: dict { "short_tag_name": float } (simplified keys for measures)
      - raw: dict (metadata)
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    # Strategy: Look for <measure-list> -> <measure>
    # If found, iterate them.
    # If not found, do global traversal (fallback).

    records = []
    
    # 1. Try to find measure-list
    # Note: namespace handling might be needed if tags have {ns}...
    # But usually DWD road weather XML is simple.
    
    # Use iter because tag might be namespaced or nested differently
    measure_list = None
    for elem in root.iter():
        if 'measure-list' in elem.tag.lower():
            measure_list = elem
            break
            
    if measure_list is not None:
        # Iterate over measures
        for measure in measure_list:
            if 'measure' not in measure.tag.lower():
                continue
                
            record = {
                "timestamp_utc": None,
                "numeric": {},
                "raw": {}
            }
            
            # Extract data from this measure block
            for child in measure:
                tag_name = child.tag
                # Remove namespace if present {url}tag -> tag
                if '}' in tag_name:
                    tag_name = tag_name.split('}', 1)[1]
                
                tag_lower = tag_name.lower()
                text = child.text.strip() if child.text else ""
                
                if not text:
                    continue

                if "time" in tag_lower:
                    record["timestamp_utc"] = text
                    record["raw"][tag_name] = text
                else:
                    # Try numeric
                    text_val = text.replace(',', '.')
                    try:
                        val = float(text_val)
                        record["numeric"][tag_name] = val
                    except ValueError:
                        record["raw"][tag_name] = text
            
            # Ensure timestamp
            if not record["timestamp_utc"]:
                record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
            
            records.append(record)
            
    # 2. Fallback: Global traversal (if no measure-list found or empty)
    if not records:
        result = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "numeric": {},
            "raw": {}
        }
        
        def _traverse(node, path_parts):
            curr_path = "/".join(path_parts)
            tag_lower = node.tag.lower()
            
            if "time" in tag_lower and node.text:
                result["raw"][curr_path] = node.text.strip()

            if node.text and node.text.strip():
                text_val = node.text.strip().replace(',', '.')
                try:
                    val = float(text_val)
                    result["numeric"][curr_path] = val
                except ValueError:
                    pass
            
            for child in node:
                _traverse(child, path_parts + [child.tag])

        _traverse(root, [root.tag])
        
        # timestamp promotion
        for k, v in result["raw"].items():
            if "time" in k.lower() and len(v) > 10:
                result["timestamp_utc"] = v
                break
        
        records.append(result)

    return records
