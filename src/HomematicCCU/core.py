# -*- coding: utf-8 -*-
"""
Platform-neutral business-logic helpers.

Transforms raw CCU3 JSON-RPC data into the dicts consumed by screens.py.
No Enigma2 or Kodi imports – safe to unit-test standalone.

Data contracts
--------------
device_summary  dict
    name        str
    icon        str   – display prefix, e.g. "[Thermostat]"
    address     str   – device serial / address
    channels    list of channel_summary

channel_summary dict
    name        str
    address     str
    interface   str   – e.g. "BidCos-RF", "HmIP-RF"
    datapoints  list of datapoint_summary

datapoint_summary dict
    name        str   – CCU3 key, e.g. "SET_POINT_TEMPERATURE"
    type        str   – "BOOL" | "FLOAT" | "INTEGER" | "ENUM" | "ACTION"
    value       str   – human-readable formatted value
    raw_value   any   – original value from the CCU3
    writable    bool
    interface   str
    address     str   – channel address (for Interface.setValue)
    min         any | None
    max         any | None
    value_list  list  – for ENUM / cyclic values

sysvar_summary  dict (same shape as datapoint_summary plus id)
    id          int | str
    name        str
    type        str
    value       str
    raw_value   any
    writable    bool  – always True for system variables
    min / max / value_list  as above
"""
from __future__ import absolute_import

# ---------------------------------------------------------------------------
# Device-type display icons
# ---------------------------------------------------------------------------

_DEVICE_ICONS = {
    # Window / door contacts
    "SHUTTER_CONTACT":                        u"[Fenster]",
    "ROTARY_HANDLE":                          u"[Griff]",
    # Thermostats
    "HEATING_CLIMATECONTROL_TRANSCEIVER":     u"[Thermostat]",
    "CLIMATECONTROL_RT_TRANSCEIVER":          u"[Thermostat]",
    "THERMOSTAT_TRANSCEIVER":                 u"[Thermostat]",
    # Switches
    "SWITCH":                                 u"[Schalter]",
    "SWITCH_TRANSMITTER":                     u"[Schalter]",
    "SWITCH_INTERFACE_TRANSCEIVER":           u"[Schalter]",
    # Dimmers
    "DIMMER":                                 u"[Dimmer]",
    "DIMMER_TRANSMITTER":                     u"[Dimmer]",
    # Motion detectors
    "MOTION_DETECTOR":                        u"[Bewegung]",
    "MOTION_DETECTOR_TRANSCEIVER":            u"[Bewegung]",
    "PRESENCE_DETECTOR_TRANSCEIVER":          u"[Bewegung]",
    # Smoke detectors
    "SMOKE_DETECTOR":                         u"[Rauch]",
    "SMOKE_DETECTOR_TEAM_TRANSCEIVER":        u"[Rauch]",
    # Buttons / keys
    "KEY":                                    u"[Taster]",
    "KEY_TRANSCEIVER":                        u"[Taster]",
    # Blind / roller shutter
    "BLIND":                                  u"[Rolladen]",
    "BLIND_TRANSMITTER":                      u"[Rolladen]",
    # Weather station
    "WEATHER":                                u"[Wetter]",
    "WEATHER_TRANSMITTER":                    u"[Wetter]",
    # Energy meter
    "POWERMETER":                             u"[Energie]",
    "POWERMETER_TRANSCEIVER":                 u"[Energie]",
    # Siren
    "ALARM_SWITCH_VIRTUAL_RECEIVER":          u"[Sirene]",
    # Fallback
    "DEFAULT":                                u"[Gerät]",
}

# Datapoint types we want to surface to the user
_SHOW_TYPES = frozenset(("BOOL", "ACTION", "FLOAT", "INTEGER", "ENUM"))


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------

def format_value(dp_type, raw_value):
    """Return a human-readable string for *raw_value* given its *dp_type*."""
    if raw_value is None:
        return u"–"
    s = str(raw_value).strip()
    sl = s.lower()

    if dp_type in ("BOOL", "ACTION"):
        if sl in ("true", "1"):
            return u"AN  ✓"
        if sl in ("false", "0"):
            return u"AUS ✗"
        return s

    if dp_type == "FLOAT":
        try:
            return u"%.1f" % float(raw_value)
        except (TypeError, ValueError):
            return s

    if dp_type in ("INTEGER", "ENUM"):
        try:
            return str(int(float(raw_value)))
        except (TypeError, ValueError):
            return s

    return s


# ---------------------------------------------------------------------------
# Writability check
# ---------------------------------------------------------------------------

def check_writable(datapoint):
    """Return True when the datapoint's operations bitmask has bit 1 set (write)."""
    ops = datapoint.get("operations", 0)
    try:
        return bool(int(ops) & 2)
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Device & channel parsing
# ---------------------------------------------------------------------------

def device_icon(device_type):
    """Return the display icon string for a CCU3 device type key."""
    return _DEVICE_ICONS.get(device_type, _DEVICE_ICONS["DEFAULT"])


def extract_device_summary(device):
    """Transform a raw CCU3 device dict into a *device_summary* dict."""
    name        = device.get("name", u"Unbekannt")
    dev_type    = device.get("type", "DEFAULT")
    dev_address = device.get("address", "")
    icon        = device_icon(dev_type)

    channels = []
    for ch in device.get("channels", []):
        ch_name      = ch.get("name", u"")
        ch_address   = ch.get("address", "")
        ch_interface = ch.get("interfaceName", "")

        dps = []
        for dp in ch.get("datapoints", []):
            dp_type = dp.get("type", "")
            if dp_type not in _SHOW_TYPES:
                continue
            dp_name  = dp.get("name", "")
            raw_val  = dp.get("value")
            if raw_val is None:
                continue
            dps.append({
                "name":       dp_name,
                "type":       dp_type,
                "value":      format_value(dp_type, raw_val),
                "raw_value":  raw_val,
                "writable":   check_writable(dp),
                "interface":  ch_interface,
                "address":    ch_address,
                "min":        dp.get("min"),
                "max":        dp.get("max"),
                "value_list": dp.get("valueList") or [],
            })

        if dps:
            channels.append({
                "name":       ch_name,
                "address":    ch_address,
                "interface":  ch_interface,
                "datapoints": dps,
            })

    return {
        "name":     name,
        "icon":     icon,
        "address":  dev_address,
        "channels": channels,
    }


# ---------------------------------------------------------------------------
# System variable parsing
# ---------------------------------------------------------------------------

def format_sysvar(sv):
    """Transform a raw CCU3 system variable dict into a *sysvar_summary* dict."""
    sv_type  = sv.get("type", "")
    raw_val  = sv.get("value")
    return {
        "id":         sv.get("id"),
        "name":       sv.get("name", u"Unbekannt"),
        "type":       sv_type,
        "value":      format_value(sv_type, raw_val),
        "raw_value":  raw_val,
        "writable":   True,          # system variables are always writable
        "interface":  "",
        "address":    "",
        "min":        sv.get("minValue"),
        "max":        sv.get("maxValue"),
        "value_list": sv.get("valueList") or [],
    }


# ---------------------------------------------------------------------------
# Value coercion  (shared between SetValueScreen and SetSysVarScreen)
# ---------------------------------------------------------------------------

def coerce_value(dp_type, value):
    """Cast *value* to the correct Python type expected by Interface.setValue / SysVar.setValue."""
    if dp_type == "FLOAT":
        return float(value)
    if dp_type == "INTEGER":
        return int(float(value))
    if dp_type in ("BOOL", "ACTION"):
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1")
    return value  # ENUM / unknown – pass as-is


def step_for_type(dp_type):
    """Return a sensible default step size for a numeric datapoint type."""
    return 0.5 if dp_type == "FLOAT" else 1
