from typing import Dict, NamedTuple

class VarMeta(NamedTuple):
    description: str
    unit: str

# Mapping based on common DWD SWIS XML tags
VARIABLE_METADATA: Dict[str, VarMeta] = {
    "at": VarMeta("Air Temperature", "°C"),
    "st": VarMeta("Surface Temperature", "°C"),
    "td": VarMeta("Dew Point Temperature", "°C"),
    "rh": VarMeta("Relative Humidity", "%"),
    "ws": VarMeta("Wind Speed", "m/s"),
    "wd": VarMeta("Wind Direction", "°"),
    "p": VarMeta("Precipitation", "mm"),
    "pr": VarMeta("Precipitation", "mm"),
    "w_state": VarMeta("Road Condition State", "code"),
    "wd_state": VarMeta("Water Film Thickness", "mm"),
    "sw": VarMeta("Saline concentration", "%"),
    "ft": VarMeta("Freezing Temperature", "°C"),
}

def get_variable_label(code: str) -> str:
    """Returns a formatted label like 'Air Temperature (at) [°C]'."""
    meta = VARIABLE_METADATA.get(code.lower())
    if meta:
        return f"{meta.description} ({code}) [{meta.unit}]"
    return code

def get_variable_unit(code: str) -> str:
    """Returns the unit or empty string."""
    meta = VARIABLE_METADATA.get(code.lower())
    return meta.unit if meta else ""
