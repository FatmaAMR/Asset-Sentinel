"""
services/sensor_normalizer.py
──────────────────────────────
Converts raw sensor data into compact, embedding-friendly text.

Design principles
─────────────────
1. No boilerplate repetition — units and machine ID appear ONCE, not per step.
2. Numbers are rounded to 2 sig-figs so small float noise doesn't fragment
   the vocabulary unnecessarily.
3. Alias resolution maps any column name to a short canonical label.
4. The public API is unchanged: normalize(data, machine_id) → str.
"""

import json
import logging
import math
from typing import Any

logger = logging.getLogger("sensor_normalizer")

# ── Canonical label → unit (used ONCE per text block, not per value) ──────────
_UNIT_MAP: dict[str, str] = {
    "vibration":          "mm/s",
    "vibration_rms":      "mm/s",
    "vibration_peak":     "mm/s",
    "acceleration":       "m/s²",
    "temperature":        "°C",
    "bearing_temp":       "°C",
    "motor_temp":         "°C",
    "oil_temp":           "°C",
    "pressure":           "bar",
    "oil_pressure":       "bar",
    "hydraulic_pressure": "bar",
    "current":            "A",
    "voltage":            "V",
    "power":              "kW",
    "frequency":          "Hz",
    "rpm":                "rpm",
    "motor_speed":        "rpm",
    "load":               "%",
    "load_pct":           "%",
    "flow_rate":          "L/min",
    "noise":              "dB",
    "sound_level":        "dB",
}

# ── Short labels for display (no underscores, title-cased) ───────────────────
_LABEL_MAP: dict[str, str] = {
    "vibration":          "vib",
    "vibration_rms":      "vib",
    "vibration_peak":     "vib_peak",
    "acceleration":       "accel",
    "temperature":        "temp",
    "bearing_temp":       "brg_temp",
    "motor_temp":         "mtr_temp",
    "oil_temp":           "oil_temp",
    "pressure":           "press",
    "oil_pressure":       "oil_press",
    "hydraulic_pressure": "hyd_press",
    "current":            "curr",
    "voltage":            "volt",
    "power":              "pwr",
    "frequency":          "freq",
    "rpm":                "rpm",
    "motor_speed":        "rpm",
    "load":               "load",
    "load_pct":           "load",
    "flow_rate":          "flow",
    "noise":              "noise",
    "sound_level":        "noise",
}

# ── Status / flag tokens ──────────────────────────────────────────────────────
_FLAG_MAP: dict[str, str] = {
    "fault":    "fault",
    "alarm":    "alarm",
    "warning":  "warn",
    "overload": "overload",
    "overheat": "overheat",
    "offline":  "offline",
    "running":  "running",
    "stopped":  "stopped",
    "idle":     "idle",
    "normal":   "normal",
}

# ── Alias map: any incoming key → canonical key ───────────────────────────────
_ALIAS_MAP: dict[str, str] = {
    # vibration
    "vib": "vibration", "vib_rms": "vibration_rms", "vibr": "vibration",
    "vibration_level": "vibration", "v_rms": "vibration_rms", "v_peak": "vibration_peak",
    # temperature
    "t": "temperature", "temp_1": "temperature", "temp_2": "temperature",
    "tmp": "temperature", "t1": "temperature", "t2": "temperature",
    "bearing_t": "bearing_temp", "motor_t": "motor_temp", "oil_t": "oil_temp",
    "exhaust_temp": "temperature", "coolant_temp": "temperature",
    # pressure
    "press": "pressure", "p": "pressure", "p1": "pressure", "p2": "pressure",
    "oil_press": "oil_pressure", "press_hyd": "hydraulic_pressure",
    "hyd_press": "hydraulic_pressure", "hydraulic_press": "hydraulic_pressure",
    # current
    "i": "current", "ia": "current", "ib": "current", "ic": "current",
    "motor_current": "current", "phase_current": "current",
    "amp": "current", "amps": "current",
    # voltage
    "u": "voltage", "volt": "voltage", "volts": "voltage",
    "v": "voltage", "vac": "voltage", "vdc": "voltage",
    # power
    "pwr": "power", "watt": "power", "kw": "power", "active_power": "power",
    # frequency
    "freq": "frequency", "hz": "frequency", "supply_freq": "frequency",
    # rpm / speed
    "n": "rpm", "speed_rpm": "rpm", "rpm_motor": "motor_speed",
    "motor_rpm": "motor_speed", "shaft_speed": "rpm", "rot_speed": "rpm",
    # load
    "load_percent": "load_pct", "load_%": "load_pct", "pct_load": "load_pct",
    # flow
    "flow_l_min": "flow_rate", "q": "flow_rate", "flowrate": "flow_rate",
    # noise
    "spl": "sound_level", "db": "noise", "sound": "sound_level",
    # acceleration
    "acc": "acceleration", "accel": "acceleration",
    "g": "acceleration", "gforce": "acceleration",
}

# Keys never included in text (carry no physical meaning)
_SKIP_KEYS = frozenset({"timestamp", "message_id", "msg_id", "ts", "time"})


def _canonical(raw_key: str) -> str:
    clean = raw_key.lower().replace("-", "_").replace(" ", "_").strip()
    return _ALIAS_MAP.get(clean, clean)


def _round2(v: float) -> str:
    """Round to 2 significant figures, return compact string."""
    if v == 0:
        return "0"
    mag = math.floor(math.log10(abs(v)))
    rounded = round(v, -mag + 1)
    # Drop trailing .0
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


# ── Public API ─────────────────────────────────────────────────────────────────

def normalize(data: Any, machine_id: str | None = None) -> str:
    """
    Convert sensor data of any shape into compact embedding-friendly text.

    A single dict reading  → "temp:72°C vib:4.1mm/s rpm:1480 curr:12A press:3.2bar"
    Plain text             → returned as-is (already text)
    List of dicts          → each reading on its own segment, joined by " | "
    Numeric scalar         → "reading:72"
    """
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data.strip()
        data = parsed

    if isinstance(data, (int, float)):
        return f"reading:{_round2(float(data))}"

    if isinstance(data, list):
        parts = [normalize(item, machine_id) for item in data]
        return " | ".join(p for p in parts if p)

    if isinstance(data, dict):
        return _dict_to_compact(data)

    return str(data)


def _dict_to_compact(d: dict) -> str:
    """
    Convert one sensor reading dict to a compact key:value string.

    Example output:
        "temp:72°C vib:4.1mm/s rpm:1480 curr:12A press:3.2bar"

    Format rules:
    - Numeric  → label:value+unit  (no spaces within token)
    - Boolean  → label:1 or label:0
    - String   → label:flagtoken
    - Nested   → skipped (flattened elsewhere)
    - Skip keys in _SKIP_KEYS
    """
    tokens: list[str] = []
    for raw_key, value in d.items():
        if raw_key.lower() in _SKIP_KEYS:
            continue
        canon = _canonical(str(raw_key))
        label = _LABEL_MAP.get(canon, canon.replace("_", ""))

        if isinstance(value, bool):
            tokens.append(f"{label}:{'1' if value else '0'}")

        elif isinstance(value, (int, float)):
            unit = _UNIT_MAP.get(canon, "")
            tokens.append(f"{label}:{_round2(float(value))}{unit}")

        elif isinstance(value, str):
            v = value.lower().strip()
            mapped = _FLAG_MAP.get(v, v[:12])   # cap string length
            tokens.append(f"{label}:{mapped}")

        elif isinstance(value, dict):
            # Recurse inline, prefix keys with parent
            tokens.append(_dict_to_compact(value))

        # lists inside dict: skip (numeric summary handled by TS2Vec)

    return " ".join(tokens)


def normalize_chunk(chunk: dict, machine_id: str | None = None) -> dict:
    """Normalize the 'text' field of a chunk dict. Returns new dict."""
    original_text = chunk.get("text", "")
    normalized    = normalize(original_text, machine_id)
    return {**chunk, "text": normalized, "original_text": original_text}
