"""Ollama-backed explanation agent with an offline deterministic fallback."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request


SYSTEM_PROMPT = """You are an internal manufacturing AI assistant for a digital
twin factory dashboard. Your job is not only to explain warnings, but to reason
about operator what-if scenarios such as continuing production, slowing the
line, stopping a station, clearing queue, inspecting equipment, or scheduling
maintenance.

Use only the supplied prediction data, active warning flags, retrieved context,
and scenario analysis. Do not invent sensor values, thresholds, or maintenance
procedures. If a scenario cannot be evaluated with the current data, say what
additional signal is needed.

Answer in this structure:
1. Direct answer
2. Expected effect on the digital twin
3. Risk impact
4. Recommended action
5. Evidence used
6. Uncertainty note"""

SOURCE_LABELS = {
    "failure_modes.md": "Failure Mode Playbook",
    "maintenance_guidelines.md": "Maintenance Guidance",
    "machine_descriptions.md": "Station Profile",
    "warning_thresholds.md": "Warning Logic",
    "operator_troubleshooting.md": "Operator Checklist",
    "manufacturing_glossary.md": "Operations Glossary",
}

SEVERITY_ORDER = ["normal", "caution", "warning", "critical"]


def _severity_after_shift(current: str, shift: int) -> str:
    idx = SEVERITY_ORDER.index(current if current in SEVERITY_ORDER else "normal")
    return SEVERITY_ORDER[max(0, min(len(SEVERITY_ORDER) - 1, idx + shift))]


def infer_scenario(question: str) -> str:
    q = question.lower()
    if any(term in q for term in ["continue", "keep running", "do nothing", "don't act", "no action", "不处理", "继续运行", "继续生产"]):
        return "continue_running"
    if any(term in q for term in ["stop", "shutdown", "pause", "停机", "停止", "暂停"]):
        return "stop_or_pause"
    if any(term in q for term in ["slow", "reduce speed", "reduce line speed", "lower speed", "lower line speed", "降速", "减速", "降低速度"]):
        return "reduce_speed"
    if re.search(r"\b(reduce|lower|decrease|cut)\b.*\b(speed|line|throughput|rate)\b", q):
        return "reduce_speed"
    if any(term in q for term in ["clear queue", "queue", "relieve", "buffer", "清队列", "缓冲", "排队"]):
        return "clear_queue"
    if any(term in q for term in ["inspect", "check", "inspection", "检查", "巡检"]):
        return "inspect_station"
    if any(term in q for term in ["maintenance", "repair", "replace", "维护", "维修", "更换"]):
        return "maintenance"
    if any(term in q for term in ["what if", "if we", "会怎么样", "如果"]):
        return "general_what_if"
    return "explain_current_state"


def analyze_scenario(record: dict, flags: list[dict], question: str) -> dict:
    scenario = infer_scenario(question)
    current_severity = record.get("severity", "normal")
    queue_ratio = record["queue_length"] / max(record["queue_capacity"], 1)
    throughput_ratio = record["predicted_throughput_units_per_hr"] / max(record["baseline_throughput_units_per_hr"], 1)
    thermal_or_vibration = any(flag["flag_type"] in {"High Temperature", "High Vibration"} for flag in flags)
    queue_flag = any(flag["flag_type"] == "Queue Congestion" for flag in flags)
    rul_flag = any(flag["flag_type"] == "Low Remaining Useful Life" for flag in flags)

    analysis = {
        "scenario": scenario,
        "current_severity": current_severity,
        "projected_severity": current_severity,
        "expected_effect": "The agent will explain the current digital twin state using active risk flags.",
        "risk_impact": "No operational change was requested, so projected risk remains unchanged.",
        "recommended_action": "Review the active warnings and inspect the top contributing signals before taking action.",
        "key_metrics": {
            "failure_risk": round(record["failure_risk"], 2),
            "queue_utilization": round(queue_ratio, 2),
            "throughput_ratio": round(throughput_ratio, 2),
            "remaining_useful_life_min": record["remaining_useful_life_min"],
            "temperature_c": record["temperature_c"],
            "vibration_rms": record["vibration_rms"],
        },
    }

    if scenario == "continue_running":
        analysis["projected_severity"] = _severity_after_shift(current_severity, 1 if flags else 0)
        analysis["expected_effect"] = "The digital twin would likely keep showing the same station as the bottleneck, with queue and downtime pressure persisting."
        analysis["risk_impact"] = "Risk increases if current warning drivers are not removed, especially when high failure risk, low RUL, high temperature, or high vibration are active."
        analysis["recommended_action"] = "Do not continue unattended. Escalate to inspection or controlled slowdown before the next prediction horizon expires."
    elif scenario == "stop_or_pause":
        analysis["projected_severity"] = _severity_after_shift(current_severity, -1)
        analysis["expected_effect"] = "The selected station would stop adding downstream risk, but line throughput would fall and upstream queue may rise."
        analysis["risk_impact"] = "Mechanical and thermal risk should stabilize, while production loss increases during the pause."
        analysis["recommended_action"] = "Use a short controlled stop when critical thermal, vibration, or RUL flags are present; document the intervention in the maintenance log."
    elif scenario == "reduce_speed":
        analysis["projected_severity"] = _severity_after_shift(current_severity, -1 if thermal_or_vibration or queue_flag else 0)
        analysis["expected_effect"] = "The digital twin should show lower throughput but less stress on the flagged station and slower queue growth."
        analysis["risk_impact"] = "Risk is likely reduced for thermal, vibration, and queue-driven warnings, but not fully resolved if RUL is already low."
        analysis["recommended_action"] = "Reduce line speed temporarily, then watch temperature, vibration, queue utilization, and throughput recovery over the next snapshot."
    elif scenario == "clear_queue":
        analysis["projected_severity"] = _severity_after_shift(current_severity, -1 if queue_flag else 0)
        analysis["expected_effect"] = "The bottleneck marker should weaken if the queue is the dominant cause; downstream starvation risk may also decrease."
        analysis["risk_impact"] = "Queue-related risk should fall, but failure-risk flags from temperature, vibration, or RUL may remain unchanged."
        analysis["recommended_action"] = "Relieve the queue first if utilization is above 80%, then verify whether failure risk remains high after flow normalizes."
    elif scenario == "inspect_station":
        analysis["projected_severity"] = current_severity
        analysis["expected_effect"] = "The digital twin state does not change immediately, but inspection reduces uncertainty and confirms whether the warning is actionable."
        analysis["risk_impact"] = "Risk is not automatically reduced until the root cause is corrected; uncertainty should decrease after inspection."
        analysis["recommended_action"] = "Inspect the top contributing signals and compare observed station behavior with the prediction snapshot."
    elif scenario == "maintenance":
        analysis["projected_severity"] = _severity_after_shift(current_severity, -2 if flags else 0)
        analysis["expected_effect"] = "After maintenance, the digital twin should trend toward fewer active warnings if the root cause is corrected."
        analysis["risk_impact"] = "Failure risk and downtime risk should decrease, especially when the active flags are mechanical, thermal, or RUL-related."
        analysis["recommended_action"] = "Schedule maintenance when critical flags or low RUL are present; verify recovery with the next temporal-model output."
    elif scenario == "general_what_if":
        analysis["expected_effect"] = "The requested scenario is underspecified, so the agent can only reason from current risk drivers."
        analysis["risk_impact"] = "Risk will move up or down depending on whether the action reduces the active warning drivers."
        analysis["recommended_action"] = "Specify the action, such as reduce speed, pause station, clear queue, inspect, or run maintenance."

    if rul_flag and scenario not in {"stop_or_pause", "maintenance"}:
        analysis["risk_impact"] += " Low RUL limits how much operational adjustments can reduce the risk."

    return analysis


def build_prompt(record: dict, flags: list[dict], contexts: list[dict], question: str) -> str:
    scenario = analyze_scenario(record, flags, question)
    return "\n\n".join(
        [
            SYSTEM_PROMPT,
            "Selected prediction data:\n" + json.dumps(record, indent=2),
            "Active warning flags:\n" + json.dumps(flags, indent=2),
            "Retrieved context:\n" + json.dumps(contexts, indent=2),
            "Scenario analysis from deterministic twin rules:\n" + json.dumps(scenario, indent=2),
            f"User question: {question}",
            "Use the scenario analysis as grounding. Do not claim the action was performed; describe the expected result if the operator takes it.",
        ]
    )


def fallback_answer(record: dict, flags: list[dict], contexts: list[dict], question: str) -> str:
    scenario = analyze_scenario(record, flags, question)
    severity = record.get("severity", "normal").upper()
    flag_names = ", ".join(flag["flag_type"] for flag in flags) or "no active warning flags"
    top_values = [
        f"risk {record['failure_risk']:.2f}",
        f"throughput {record['predicted_throughput_units_per_hr']:.0f} vs baseline {record['baseline_throughput_units_per_hr']:.0f} uph",
        f"queue {record['queue_length']}/{record['queue_capacity']}",
        f"RUL {record['remaining_useful_life_min']:.0f} min",
        f"uncertainty {record['model_uncertainty']:.2f}",
    ]
    used = "; ".join(
        f"{SOURCE_LABELS.get(ctx['document'], 'Internal Guidance')} / {ctx['section'].replace('_', ' ').title()}"
        for ctx in contexts[:3]
    ) or "no matching guidance"
    signals = ", ".join(record.get("top_contributing_signals") or ["no dominant signal reported"])
    if flags:
        next_checks = "Check the top contributing signals, compare actual station behavior with the queue/throughput trend, and follow the retrieved maintenance guidance before changing line speed."
    else:
        next_checks = "Continue monitoring the station and compare future snapshots against the same thresholds."
    if scenario["scenario"] == "explain_current_state":
        direct = (
            f"{record['machine_id']} is {severity} for this prediction snapshot. "
            f"The active logic is: {flag_names}."
        )
    else:
        direct = (
            f"If the operator chooses this scenario for {record['machine_id']}, the digital twin projects "
            f"{scenario['projected_severity'].upper()} risk from the current {severity} state."
        )

    return (
        f"Direct answer: {direct}\n\n"
        f"Expected effect on the digital twin: {scenario['expected_effect']}\n\n"
        f"Risk impact: {scenario['risk_impact']}\n\n"
        f"Trigger values: {', '.join(top_values)}. Main contributing signals: {signals}.\n\n"
        f"Recommended action: {scenario['recommended_action']} {next_checks}\n\n"
        f"Evidence used: {used}.\n\n"
        "Uncertainty note: this is a what-if estimate from simulated temporal-model output and rule-based twin logic, not a live control command."
    )


def ask_ollama(
    record: dict,
    flags: list[dict],
    contexts: list[dict],
    question: str,
    model: str = "gpt-oss:20b",
    host: str = "https://ollama.com",
    timeout: int = 45,
) -> tuple[str, bool]:
    """
    Ollama Cloud reasoning for the deployed Render demo.

    Uses:
      OLLAMA_API_BASE=https://ollama.com
      OLLAMA_API_KEY=your_key
      OLLAMA_MODEL optional override

    Falls back safely to deterministic reasoning if the API fails.
    """

    import os

    api_base = os.environ.get("OLLAMA_API_BASE", host).rstrip("/")
    api_key = os.environ.get("OLLAMA_API_KEY")
    selected_model = os.environ.get("OLLAMA_MODEL", model)

    if not api_key:
        return fallback_answer(record, flags, contexts, question), False

    prompt = build_prompt(record, flags, contexts, question)

    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }

    request = urllib.request.Request(
        f"{api_base}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            answer = (
                data.get("message", {})
                .get("content", "")
                .strip()
            )
            if answer:
                return answer, True

    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, KeyError):
        pass

    return fallback_answer(record, flags, contexts, question), False