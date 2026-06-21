"""Streamlit UI rendering helpers."""

from __future__ import annotations

import html
import json
from textwrap import dedent

import streamlit as st

from .severity import SEVERITY_RANK


STATUS_LABEL = {
    "normal": "HEALTHY",
    "caution": "CAUTION",
    "warning": "WARNING",
    "critical": "CRITICAL",
}

GUIDANCE_SOURCE_LABELS = {
    "failure_modes.md": "Failure Mode Playbook",
    "maintenance_guidelines.md": "Maintenance Guidance",
    "machine_descriptions.md": "Station Profile",
    "warning_thresholds.md": "Warning Logic",
    "operator_troubleshooting.md": "Operator Checklist",
    "manufacturing_glossary.md": "Operations Glossary",
}


def severity_class(severity: str) -> str:
    return f"sev-{severity}"


def _sparkline(record: dict) -> str:
    risk = record["failure_risk"]
    queue = record["queue_length"] / max(record["queue_capacity"], 1)
    uncertainty = record["model_uncertainty"]
    values = [
        22 + risk * 22,
        18 + queue * 35,
        24 + uncertainty * 34,
        19 + (1 - min(record["predicted_throughput_units_per_hr"] / max(record["baseline_throughput_units_per_hr"], 1), 1.2) / 1.2) * 28,
        28 + risk * 18,
        20 + queue * 26,
    ]
    points = " ".join(f"{idx * 10},{60 - value:.1f}" for idx, value in enumerate(values))
    color = {
        "critical": "#ff5252",
        "warning": "#ff9f31",
        "caution": "#f5c542",
        "normal": "#48d27b",
    }.get(record.get("severity", "normal"), "#48d27b")
    return f'<svg class="spark" viewBox="0 0 55 40" aria-hidden="true"><polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def _badge(label: str, severity: str) -> str:
    return f'<span class="badge {severity_class(severity)}">{html.escape(label)}</span>'


def render_machine_overview(records: list[dict]) -> None:
    rows_html = []
    for record in records:
        queue_util = record["queue_length"] / max(record["queue_capacity"], 1)
        severity = record["severity"]
        mode = record["predicted_failure_mode"]
        rows_html.append(
            dedent(f"""
            <div class="overview-row row-{severity}">
              <div>{html.escape(record["machine_id"])}</div>
              <div><span class="badge sev-{severity}">{html.escape(record["machine_state"].upper())}</span></div>
              <div><span class="badge sev-{severity}">{STATUS_LABEL[severity]}</span></div>
              <div class="num">{record["failure_risk"]:.2f}</div>
              <div>{html.escape("None" if mode == "none" else mode.replace("_", " ").title())}</div>
              <div><span class="bar"><span style="width:{queue_util:.0%};"></span></span>{queue_util:.0%}</div>
              <div class="num">{record["predicted_throughput_units_per_hr"]:,.0f}</div>
              <div class="num">{record["remaining_useful_life_min"] / 60:.1f} h</div>
              <div class="num">{record["model_uncertainty"]:.2f}</div>
            </div>
            """)
        )
    st.markdown(
        dedent(f"""
        <div class="overview-head"><div>Machine</div><div>State</div><div>Severity</div><div>Risk</div><div>Mode</div><div>Queue</div><div>UPH</div><div>RUL</div><div>Unc.</div></div>
        {''.join(rows_html)}
        """),
        unsafe_allow_html=True,
    )


def render_warning_panel(flags: list[dict]) -> None:
    if not flags:
        st.markdown('<div class="empty-ok"><div class="ok-icon">OK</div><strong>No active warnings</strong><br>All selected stations are within normal parameters.</div>', unsafe_allow_html=True)
        return
    for flag in flags:
        escaped_message = html.escape(flag["message"])
        icon = "!" if flag["severity"] in {"critical", "warning"} else "i"
        st.markdown(
            dedent(f"""
            <div class="warning-list-item {severity_class(flag['severity'])}">
              <div class="warning-icon">{icon}</div>
              <div class="warning-copy">
                <strong>{html.escape(flag['machine_id'])} {html.escape(flag['flag_type'])}</strong>
                <span>{escaped_message}</span>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )


def render_machine_detail(record: dict, flags: list[dict]) -> None:
    queue_util = record["queue_length"] / max(record["queue_capacity"], 1)
    cols = st.columns(4)
    cols[0].metric("Failure Risk", f"{record['failure_risk']:.2f}")
    cols[1].metric("Queue Utilization", f"{queue_util:.0%}")
    cols[2].metric("Predicted Downtime", f"{record['predicted_downtime_min']:.1f} min")
    cols[3].metric("RUL", f"{record['remaining_useful_life_min']:.0f} min")
    st.markdown("**Raw IDN string**")
    st.code(record["raw_idn"], language="text")
    left, right = st.columns(2)
    with left:
        st.markdown("**Parsed prediction dictionary**")
        st.json({k: v for k, v in record.items() if k not in {"raw_idn", "flags"}})
    with right:
        st.markdown("**Active flags**")
        st.json(flags)
        st.markdown("**Top contributing signals**")
        st.write(", ".join(record.get("top_contributing_signals") or ["none"]))


def render_context_cards(contexts: list[dict], compact: bool = False) -> None:
    if not contexts:
        st.info("No relevant guidance found for the selected machine and question.")
        return
    for ctx in contexts:
        source_label = GUIDANCE_SOURCE_LABELS.get(ctx["document"], "Internal Guidance")
        section = ctx["section"].replace("_", " ").title()
        reason = ctx.get("match_reason", "Relevant to selected machine and warning")
        text = ctx["text"]
        if compact and len(text) > 120:
            text = text[:117].rsplit(" ", 1)[0] + "..."
        st.markdown(
            dedent(f"""
            <div class="evidence-card {'compact-evidence' if compact else ''}">
              <div class="context-title">{html.escape(source_label)}</div>
              <div class="evidence-topic">{html.escape(section)}</div>
              <p>{html.escape(text)}</p>
              <small>{html.escape(reason)}</small>
            </div>
            """),
            unsafe_allow_html=True,
        )


def render_context_summary(contexts: list[dict]) -> None:
    if not contexts:
        st.info("No relevant guidance found.")
        return
    for ctx in contexts:
        source_label = GUIDANCE_SOURCE_LABELS.get(ctx["document"], "Internal Guidance")
        section = ctx["section"].replace("_", " ").title()
        text = ctx["text"]
        if len(text) > 82:
            text = text[:79].rsplit(" ", 1)[0] + "..."
        st.markdown(
            dedent(f"""
            <div class="evidence-list-item">
              <div class="doc-icon">D</div>
              <div class="evidence-copy">
                <strong>{html.escape(source_label)}</strong>
                <span>{html.escape(section)} - {html.escape(text)}</span>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )


def render_contract(record: dict, flags: list[dict], contexts: list[dict]) -> None:
    st.code(
        json.dumps(
            {
                "agent_input": {
                    "prediction": {k: v for k, v in record.items() if k not in {"flags"}},
                    "active_flags": flags,
                    "retrieved_context": contexts,
                },
                "agent_output_schema": {
                    "direct_answer": "string",
                    "warning_explanation": "string",
                    "trigger_values": ["string"],
                    "guidance_sources_used": ["source_title/topic"],
                    "recommended_next_checks": ["string"],
                    "uncertainty_note": "string",
                },
            },
            indent=2,
        ),
        language="json",
    )
