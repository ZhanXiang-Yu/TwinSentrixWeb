"""Data loading helpers for mock IDN predictions."""

from __future__ import annotations

from pathlib import Path

from .idn_parser import parse_idn


def load_predictions(path: str | Path) -> list[dict]:
    records: list[dict] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        record = parse_idn(line)
        record["source_line"] = line_no
        records.append(record)
    return records


def group_by_timestamp(records: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for record in records:
        grouped.setdefault(record["timestamp"], []).append(record)
    return grouped
