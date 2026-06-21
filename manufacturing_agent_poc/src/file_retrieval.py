"""Small Markdown-section retrieval layer for local manufacturing docs."""

from __future__ import annotations

import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def load_sections(kb_dir: str | Path) -> list[dict]:
    sections: list[dict] = []
    for path in sorted(Path(kb_dir).glob("*.md")):
        current_title = path.stem
        current_lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = HEADING_RE.match(line)
            if match:
                if current_lines:
                    sections.append({"document": path.name, "section": current_title, "text": "\n".join(current_lines).strip()})
                current_title = match.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines:
            sections.append({"document": path.name, "section": current_title, "text": "\n".join(current_lines).strip()})
    return [section for section in sections if section["text"]]


def retrieve_context(
    sections: list[dict],
    machine_name: str,
    failure_mode: str,
    flags: list[dict],
    question: str = "",
    limit: int = 6,
) -> list[dict]:
    terms = {
        machine_name.lower(),
        failure_mode.lower().replace("_", " "),
        failure_mode.lower(),
        *[flag["flag_type"].lower() for flag in flags],
        *[word.lower() for word in re.findall(r"[A-Za-z_]+", question) if len(word) > 3],
    }
    terms.discard("none")
    machine_term = machine_name.lower().replace("_", " ")
    mode_term = failure_mode.lower().replace("_", " ")
    flag_terms = [flag["flag_type"].lower().replace("_", " ") for flag in flags]
    scored: list[tuple[int, dict, list[str]]] = []
    for section in sections:
        section_title = section["section"].lower().replace("_", " ")
        document_name = section["document"].lower()
        haystack = f"{document_name} {section_title} {section['text']}".lower().replace("_", " ")
        reasons = [term for term in terms if term and term.replace("_", " ") in haystack]
        score = len(reasons)
        if mode_term and mode_term != "none" and mode_term in section_title:
            score += 5
            reasons.append("exact failure mode")
            if document_name == "failure_modes.md":
                score += 3
                reasons.append("failure mode reference")
        if machine_term and machine_term in section_title:
            score += 4
            reasons.append("selected machine")
        for flag_term in flag_terms:
            if flag_term and flag_term in section_title:
                score += 3
                reasons.append("active flag")
        if section["document"] in {"warning_thresholds.md", "operator_troubleshooting.md"} and flags:
            score += 1
            reasons.append("active warning support")
        if score:
            scored.append((score, section, reasons))

    scored.sort(key=lambda item: item[0], reverse=True)
    results: list[dict] = []
    for _, section, reasons in scored[:limit]:
        text = section["text"].replace("\n", " ")
        results.append(
            {
                "document": section["document"],
                "section": section["section"],
                "text": text[:520],
                "match_reason": ", ".join(dict.fromkeys(reasons[:4])),
            }
        )
    return results
