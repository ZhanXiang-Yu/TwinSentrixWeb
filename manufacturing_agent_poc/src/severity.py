"""Machine severity calculation and sorting helpers."""

from __future__ import annotations


SEVERITY_RANK = {"normal": 0, "caution": 1, "warning": 2, "critical": 3}


def calculate_severity(flags: list[dict]) -> str:
    if not flags:
        return "normal"
    if any(flag["severity"] == "critical" for flag in flags) or len(flags) >= 3:
        return "critical"
    if len(flags) == 1 and flags[0]["severity"] == "caution":
        return "caution"
    if len(flags) == 1 and flags[0]["severity"] == "warning":
        return "warning"
    caution_count = sum(flag["severity"] == "caution" for flag in flags)
    if caution_count >= 2:
        return "warning"
    return "warning"


def sort_flags(flags: list[dict]) -> list[dict]:
    return sorted(flags, key=lambda flag: SEVERITY_RANK.get(flag["severity"], 0), reverse=True)


def sort_records_by_severity(records: list[dict]) -> list[dict]:
    return sorted(records, key=lambda record: SEVERITY_RANK.get(record.get("severity", "normal"), 0), reverse=True)
