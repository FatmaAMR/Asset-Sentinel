"""
services/window_chunker.py
───────────────────────────
Converts a machine window event into a human-readable, embedding-optimised
text chunk for ChromaDB storage.

Output format
─────────────

  Machine: pump_01  |  Fault: Bearing Fault  |  Remaining Life: 142 cycles (Low)
  ────────────────────────────────────────────────────────────────────────────────
  Sensor Readings (16 steps):
    • Temperature   : 75.0 °C    [72.0 – 76.0 °C]   ↑ Rising    (spike at end)
    • Vibration     : 6.3 mm/s   [4.1 – 6.3 mm/s]   ↑ Rising
    • RPM           : 1470 rpm   [1460 – 1490 rpm]   ↓ Falling
    • Sensor s1     : 2.2        [1.2 – 2.2]         ↑ Rising

  Diagnosis Note: ...

Anomaly detection
─────────────────
Instead of hardcoded thresholds (which only work for known physical sensors),
anomaly annotations are derived purely from the window's own statistics:

  • "spike at end"   — last value > mean + 2σ
  • "drop at end"    — last value < mean - 2σ
  • "high variance"  — std > 20% of |mean|  (noisy / oscillating)
  • "sudden jump"    — max single-step change > 3σ of all step changes

This works for any sensor — named (temperature, vibration) or generic (s1, s2).
No units or domain knowledge required.

Generic column names (s1, s2, s3 …) are fully supported.
Column order: natural sort (s1 < s2 < s10).
"""

import logging
import math
import re as _re
from typing import Any

logger = logging.getLogger("window_chunker")

_SKIP_KEYS = frozenset({
    "timestamp", "message_id", "msg_id", "ts", "time",
    "time_cycles", "unit_nr",         # ← add these
})

# ── Human-readable full names for known canonical keys ────────────────────────
_FULL_NAME_MAP: dict[str, str] = {
    "vibration":          "Vibration",
    "vibration_rms":      "Vibration RMS",
    "vibration_peak":     "Vibration Peak",
    "acceleration":       "Acceleration",
    "temperature":        "Temperature",
    "bearing_temp":       "Bearing Temperature",
    "motor_temp":         "Motor Temperature",
    "oil_temp":           "Oil Temperature",
    "pressure":           "Pressure",
    "oil_pressure":       "Oil Pressure",
    "hydraulic_pressure": "Hydraulic Pressure",
    "current":            "Current",
    "voltage":            "Voltage",
    "power":              "Power",
    "frequency":          "Frequency",
    "rpm":                "RPM",
    "motor_speed":        "Motor Speed",
    "load":               "Load",
    "load_pct":           "Load",
    "flow_rate":          "Flow Rate",
    "noise":              "Noise Level",
    "sound_level":        "Sound Level",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _natural_sort_keys(keys: list[str]) -> list[str]:
    def _key(s: str):
        parts = _re.split(r"(\d+)", s)
        return [int(p) if p.isdigit() else p.lower() for p in parts]
    return sorted(keys, key=_key)


def _rul_label(rul: float | None) -> str:
    """Display RUL as a plain number — no hardcoded buckets."""
    if rul is None:
        return "Unknown"
    if rul <= 0:
        return "0 cycles — machine has failed"
    return f"{_fmt(rul)} cycles remaining"


def _format_label(label: str) -> str:
    return label.replace("_", " ").replace("-", " ").title() if label else "Unknown"


def _fmt(v: float) -> str:
    rounded = round(v, 1)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)


def _trend_word(values: list[float]) -> tuple[str, str]:
    """
    Determine trend direction using a normalized linear regression slope.

    Slope is divided by the signal own standard deviation so the result
    is dimensionless and works for any sensor, any scale, any unit.
    The thresholds (0.3 and 0.05) are on the normalized slope — unitless.
    """
    if len(values) < 2:
        return "→", "Stable"

    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n

    num = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den > 1e-12 else 0.0

    variance = sum((v - y_mean) ** 2 for v in values) / n
    std = math.sqrt(variance) if variance > 1e-12 else 1.0
    norm_slope = slope / std

    if norm_slope > 0.3:
        return "↑", "Rising"
    if norm_slope < -0.3:
        return "↓", "Falling"
    if norm_slope > 0.05:
        return "↗", "Slightly Rising"
    if norm_slope < -0.05:
        return "↘", "Slightly Falling"
    return "→", "Stable"


def _anomaly_note(values: list[float]) -> str:
    """
    Detect anomalies purely from the window's own statistics.
    No hardcoded thresholds — works for any sensor or unit.

    Checks (in priority order):
      1. Spike at end   — last value deviates > 2σ above mean
      2. Drop at end    — last value deviates > 2σ below mean
      3. Sudden jump    — any single step-change > 3σ of all step-changes
      4. High variance  — std > 20% of |mean|  (noisy signal)

    Returns a short annotation string, or "" if nothing unusual.
    """
    if len(values) < 3:
        return ""

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance) if variance > 0 else 0.0

    # 1 & 2 — endpoint spike / drop
    if std > 1e-9:
        z_last = (values[-1] - mean) / std
        if z_last > 2.0:
            return "(spike at end)"
        if z_last < -2.0:
            return "(drop at end)"

    # 3 — sudden jump anywhere in the window
    if len(values) >= 3:
        diffs = [abs(values[i+1] - values[i]) for i in range(len(values) - 1)]
        d_mean = sum(diffs) / len(diffs)
        d_var  = sum((d - d_mean) ** 2 for d in diffs) / len(diffs)
        d_std  = math.sqrt(d_var) if d_var > 0 else 0.0
        if d_std > 1e-9 and max(diffs) > d_mean + 3 * d_std:
            return "(sudden jump)"

    # 4 — high variance / noisy signal
    if abs(mean) > 1e-9 and std / abs(mean) > 0.20:
        return "(high variance)"

    return ""


def _get_sensor_info(key: str) -> tuple[str, str]:
    """Return (full_name, unit) for a channel key."""
    try:
        from services.sensor_normalizer import _canonical, _UNIT_MAP
        canon     = _canonical(key)
        full_name = _FULL_NAME_MAP.get(canon, f"Sensor {key}")
        unit      = _UNIT_MAP.get(canon, "")
        return full_name, unit
    except Exception:
        return f"Sensor {key}", ""


def _extract_channels(window_sliding: list) -> dict[str, list[float]]:
    raw: dict[str, list[float]] = {}
    for step in window_sliding:
        if not isinstance(step, dict):
            continue
        for k, v in step.items():
            if k.lower() in _SKIP_KEYS:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            raw.setdefault(k, []).append(float(v))
    return {k: raw[k] for k in _natural_sort_keys(list(raw.keys()))}


def _build_sensor_lines(channels: dict[str, list[float]]) -> list[str]:
    lines: list[str] = []
    for key, vals in channels.items():
        full_name, unit = _get_sensor_info(key)
        last = vals[-1]
        lo   = min(vals)
        hi   = max(vals)
        arrow, word = _trend_word(vals)
        note = _anomaly_note(vals)

        unit_str  = f" {unit}" if unit else ""
        range_str = f"[{_fmt(lo)}-{_fmt(hi)}{unit_str}]"
        note_str  = f", {note}" if note else ""

        lines.append(
            f"{full_name}: {_fmt(last)}{unit_str} {range_str} {arrow} {word}{note_str}"
        )
    return lines


def _columnar_to_row_list(data: dict) -> list[dict]:
    max_len = max(
        (len(v) for v in data.values() if isinstance(v, (list, tuple))),
        default=1,
    )
    rows: list[dict] = []
    for i in range(max_len):
        row: dict = {}
        for col, vals in data.items():
            row[col] = vals[i] if isinstance(vals, (list, tuple)) and i < len(vals) else vals
        rows.append(row)
    return rows


# ── Public API ────────────────────────────────────────────────────────────────

def window_event_to_chunks(event: Any) -> list[dict]:
    """Convert a window event into exactly ONE human-readable text chunk."""

    if hasattr(event, "model_dump"):
        data = event.model_dump()
    elif hasattr(event, "dict"):
        data = event.dict()
    elif isinstance(event, dict):
        data = event
    else:
        data = vars(event)

    machine_id     = str(data.get("machine_id", "unknown"))
    label          = str(data.get("label", "")).strip()
    rul            = data.get("rul")
    window_sliding = data.get("window_sliding") or []
    message_id     = str(data.get("message_id", "no_id"))
    reason         = str(data.get("reason", "")).strip()

    if isinstance(window_sliding, dict):
        window_sliding = _columnar_to_row_list(window_sliding)
    elif not isinstance(window_sliding, list):
        window_sliding = [window_sliding]

    n_steps = len(window_sliding)

    header = (
        f"Machine: {machine_id}, "
        f"Fault: {_format_label(label)}, "
        f"Remaining Life: {_rul_label(rul)}"
    )

    channels = _extract_channels(window_sliding)
    sensor_lines = _build_sensor_lines(channels) if channels else ["No numeric data"]

    parts = [header, f"Sensor Readings ({n_steps} steps):"] + sensor_lines
    if reason:
        parts.append(f"Reason: {reason}")

    full_text = " | ".join(parts[:2]) + "\n" + "\n".join(parts[2:])

    chunk = {
        "id":     f"{message_id}_chunk0",
        "source": f"window:{machine_id}",
        "page":   0,
        "text":   full_text,
    }

    logger.info(
        "Window %s → 1 chunk | %d chars | %d channels | %d steps | machine=%s",
        message_id, len(full_text), len(channels), n_steps, machine_id,
    )
    return [chunk]