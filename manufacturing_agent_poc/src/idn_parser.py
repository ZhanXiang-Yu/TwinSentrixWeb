"""Parser for compact IDN-style manufacturing prediction strings."""

from __future__ import annotations


REQUIRED_FIELDS = {
    "ts",
    "line",
    "machine",
    "name",
    "state",
    "horizon",
    "risk",
    "mode",
    "conf",
    "downtime",
    "throughput",
    "baseline",
    "queue",
    "temp",
    "vib",
    "power",
    "rul",
    "unc",
    "signals",
}


def _as_float(value: str, field: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc


def _as_int(value: str, field: str) -> int:
    try:
        return int(float(value))
    except ValueError as exc:
        raise ValueError(f"Invalid integer value for {field}: {value!r}") from exc


def parse_idn(raw: str) -> dict:
    """Parse one IDN prediction line into a normalized dictionary."""
    line = raw.strip()
    if not line:
        raise ValueError("Empty IDN line")
    parts = [part.strip() for part in line.split("|")]
    if not parts or parts[0] != "IDN":
        raise ValueError("IDN line must start with 'IDN|'")

    fields: dict[str, str] = {}
    for part in parts[1:]:
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid field segment: {part!r}")
        key, value = part.split("=", 1)
        fields[key.strip()] = value.strip()

    missing = sorted(REQUIRED_FIELDS - fields.keys())
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    queue_bits = fields["queue"].split("/", 1)
    if len(queue_bits) != 2:
        raise ValueError("queue must use '<length>/<capacity>' format")

    signals = [signal.strip() for signal in fields["signals"].split(",") if signal.strip()]
    if signals == ["none"]:
        signals = []

    return {
        "raw_idn": line,
        "timestamp": fields["ts"],
        "line_id": fields["line"],
        "machine_id": fields["machine"],
        "machine_name": fields["name"],
        "machine_state": fields["state"],
        "horizon_min": _as_int(fields["horizon"], "horizon"),
        "failure_risk": _as_float(fields["risk"], "risk"),
        "predicted_failure_mode": fields["mode"],
        "failure_confidence": _as_float(fields["conf"], "conf"),
        "predicted_downtime_min": _as_float(fields["downtime"], "downtime"),
        "predicted_throughput_units_per_hr": _as_float(fields["throughput"], "throughput"),
        "baseline_throughput_units_per_hr": _as_float(fields["baseline"], "baseline"),
        "queue_length": _as_int(queue_bits[0].strip(), "queue_length"),
        "queue_capacity": _as_int(queue_bits[1].strip(), "queue_capacity"),
        "temperature_c": _as_float(fields["temp"], "temp"),
        "vibration_rms": _as_float(fields["vib"], "vib"),
        "power_kw": _as_float(fields["power"], "power"),
        "remaining_useful_life_min": _as_float(fields["rul"], "rul"),
        "model_uncertainty": _as_float(fields["unc"], "unc"),
        "top_contributing_signals": signals,
    }
