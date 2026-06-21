"""Rule-based warning flag engine."""

from __future__ import annotations


def _flag(record: dict, flag_type: str, severity: str, trigger_value, threshold, message: str) -> dict:
    return {
        "flag_type": flag_type,
        "severity": severity,
        "machine_id": record["machine_id"],
        "machine_name": record["machine_name"],
        "trigger_value": trigger_value,
        "threshold": threshold,
        "message": message,
    }


def get_flags(record: dict) -> list[dict]:
    flags: list[dict] = []
    machine = record["machine_name"]
    horizon = record["horizon_min"]
    risk = record["failure_risk"]
    throughput = record["predicted_throughput_units_per_hr"]
    baseline = record["baseline_throughput_units_per_hr"]
    queue_ratio = record["queue_length"] / max(record["queue_capacity"], 1)
    rul = record["remaining_useful_life_min"]
    temp = record["temperature_c"]
    vib = record["vibration_rms"]
    unc = record["model_uncertainty"]

    if risk >= 0.85:
        flags.append(_flag(record, "High Failure Risk", "critical", risk, 0.85, f"{machine} has critical predicted failure risk over the next {horizon} minutes."))
    elif risk >= 0.75:
        flags.append(_flag(record, "High Failure Risk", "warning", risk, 0.75, f"{machine} has elevated predicted failure risk over the next {horizon} minutes."))

    if throughput < 0.75 * baseline:
        flags.append(_flag(record, "Throughput Drop", "critical", throughput, f"<75% of {baseline:g}", f"{machine} throughput is critically below baseline."))
    elif throughput < 0.85 * baseline:
        flags.append(_flag(record, "Throughput Drop", "warning", throughput, f"<85% of {baseline:g}", f"{machine} throughput is below expected baseline."))

    if queue_ratio >= 0.90:
        flags.append(_flag(record, "Queue Congestion", "critical", round(queue_ratio, 2), 0.90, f"{machine} queue is near capacity."))
    elif queue_ratio >= 0.80:
        flags.append(_flag(record, "Queue Congestion", "warning", round(queue_ratio, 2), 0.80, f"{machine} queue is building up."))

    if rul < 30:
        flags.append(_flag(record, "Low Remaining Useful Life", "critical", rul, 30, f"{machine} has critically low remaining useful life."))
    elif rul < 45:
        flags.append(_flag(record, "Low Remaining Useful Life", "warning", rul, 45, f"{machine} has low remaining useful life."))

    if temp > 90:
        flags.append(_flag(record, "High Temperature", "critical", temp, 90, f"{machine} temperature exceeds critical threshold."))
    elif temp > 80:
        flags.append(_flag(record, "High Temperature", "warning", temp, 80, f"{machine} temperature exceeds warning threshold."))

    if vib > 0.80:
        flags.append(_flag(record, "High Vibration", "critical", vib, 0.80, f"{machine} vibration exceeds critical threshold."))
    elif vib > 0.65:
        flags.append(_flag(record, "High Vibration", "warning", vib, 0.65, f"{machine} vibration exceeds warning threshold."))

    if unc > 0.45:
        flags.append(_flag(record, "High Model Uncertainty", "warning", unc, 0.45, f"{machine} model uncertainty is high."))
    elif unc > 0.30:
        flags.append(_flag(record, "High Model Uncertainty", "caution", unc, 0.30, f"{machine} model uncertainty is elevated."))

    return flags
