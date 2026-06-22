from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.agent import ask_ollama, fallback_answer
from src.data_loader import group_by_timestamp, load_predictions
from src.file_retrieval import load_sections, retrieve_context
from src.flag_engine import get_flags
from src.severity import SEVERITY_RANK, calculate_severity, sort_flags, sort_records_by_severity
from src.ui_components import (
    STATUS_LABEL,
    render_context_cards,
    render_context_summary,
    render_machine_detail,
    render_machine_overview,
    render_warning_panel,
)


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
KB_DIR = ROOT / "knowledge_base"
THREE_D_SCENE = ROOT.parent / "website-3d" / "index.html"


st.set_page_config(
    page_title="TwinSentrix - Manufacturing AI Agent",
    page_icon="TS",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --bg: #07111d;
            --panel: #0d1a2a;
            --panel2: #101f33;
            --line: rgba(136, 161, 190, 0.22);
            --text: #e8f2ff;
            --muted: #9fb0c5;
            --green: #46d483;
            --yellow: #f5b642;
            --orange: #ff8b3d;
            --red: #ff5252;
            --blue: #55b7ff;
          }
          .stApp { background: radial-gradient(circle at top, #10233a 0, #07111d 38%, #050b13 100%); color: var(--text); }
          [data-testid="stSidebar"] { background: #081523; border-right: 1px solid var(--line); }
          [data-testid="stSidebar"] * { color: var(--text); }
          [data-baseweb="select"] > div,
          [data-baseweb="input"] > div {
            background: #101f33 !important;
            border: 1px solid rgba(136,161,190,.32) !important;
            border-radius: 8px !important;
          }
          [data-baseweb="select"] span,
          [data-baseweb="select"] input,
          [data-baseweb="input"] input { color: var(--text) !important; }
          [data-baseweb="select"] svg { fill: var(--muted) !important; }
          div[role="listbox"] {
            background: #101f33 !important;
            border: 1px solid rgba(136,161,190,.32) !important;
          }
          div[role="option"] { background: #101f33 !important; color: var(--text) !important; }
          div[role="option"]:hover { background: #19304c !important; }
          .stButton button {
            background: #142943 !important;
            border: 1px solid rgba(85,183,255,.28) !important;
            color: var(--text) !important;
            border-radius: 8px !important;
          }
          h1, h2, h3 { letter-spacing: 0; }
          .topbar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px 4px 18px; border-bottom: 1px solid var(--line); margin-bottom: 12px;
          }
          .brand { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 20px; }
          .logo-mark {
            width: 30px; height: 30px; display: grid; place-items: center; border-radius: 8px;
            background: linear-gradient(135deg, #2384ff, #48d1ff); color: #06111e; font-weight: 900;
          }
          .live-pill, .status-pill {
            display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--line);
            background: rgba(255,255,255,0.04); border-radius: 6px; padding: 5px 9px; font-size: 12px;
          }
          .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 14px var(--green); }
          .hero-panel, .panel {
            border: 1px solid var(--line); background: rgba(12, 25, 40, 0.86);
            border-radius: 8px; box-shadow: 0 16px 50px rgba(0,0,0,.23);
          }
          .hero-panel { min-height: 330px; position: relative; overflow: hidden; padding: 14px; }
          .line-art {
            height: 292px; border-radius: 8px; position: relative;
            background:
              linear-gradient(150deg, rgba(85,183,255,.11), transparent 38%),
              linear-gradient(#15263a 1px, transparent 1px),
              linear-gradient(90deg, #15263a 1px, transparent 1px),
              #091523;
            background-size: auto, 46px 46px, 46px 46px, auto;
          }
          .belt { position:absolute; height: 20px; background:#293748; border:1px solid #657083; transform:skewX(-15deg); box-shadow: inset 0 2px 0 rgba(255,255,255,.08); }
          .belt.main { left:8%; right:11%; top:48%; }
          .belt.return { left:28%; right:22%; top:72%; }
          .machine {
            position:absolute; width:82px; height:78px; border:1px solid #8798ad; border-radius:6px;
            background: linear-gradient(145deg, #c8d2de, #657386 55%, #263445);
            box-shadow: 0 16px 28px rgba(0,0,0,.35);
          }
          .machine::after { content:""; position:absolute; inset:18px 22px 16px; border-radius:4px; background:rgba(3,20,32,.55); border:1px solid rgba(110,210,255,.38); }
          .station-label {
            position:absolute; transform: translateX(-50%); padding:5px 10px; min-width: 80px; text-align:center;
            border:1px solid var(--line); border-radius:6px; background:rgba(7,17,29,.86); color:#dceaff; font-size:12px; font-weight:700;
          }
          .station-label .mini-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--green); margin-right:6px; }
          .station-critical { outline: 2px solid var(--red); box-shadow: 0 0 32px rgba(255,82,82,.55); }
          .station-warning { outline: 2px solid var(--yellow); box-shadow: 0 0 26px rgba(245,182,66,.45); }
          .box { position:absolute; width:17px; height:14px; background:#d3a35f; border:1px solid #ffd48e; border-radius:2px; transform:skewX(-15deg); }
          .rail { position:absolute; left:4%; right:4%; top:30%; height:132px; border:3px solid #f97316; transform:skewX(-15deg); opacity:.82; }
          .status-callout {
            position:absolute; left:18px; bottom:18px; max-width:360px; padding:12px 14px; border-radius:7px;
            background:rgba(12,25,40,.92); border:1px solid var(--line); color:var(--muted); font-size:13px;
          }
          .status-callout strong { color: var(--text); }
          .metric-card {
            border: 1px solid var(--line); border-radius: 8px; padding: 16px; min-height: 112px;
            background: linear-gradient(145deg, rgba(20,38,58,.94), rgba(12,24,39,.94));
          }
          .metric-label { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
          .metric-value { color: var(--text); font-size: 30px; font-weight: 800; line-height: 1; }
          .sev-normal { border-color: rgba(70,212,131,.55)!important; color: var(--green)!important; }
          .sev-caution { border-color: rgba(245,182,66,.6)!important; color: var(--yellow)!important; }
          .sev-warning { border-color: rgba(255,139,61,.65)!important; color: var(--orange)!important; }
          .sev-critical { border-color: rgba(255,82,82,.72)!important; color: var(--red)!important; }
          .warning-card, .context-card, .evidence-card, .empty-ok {
            border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 10px;
            background: rgba(14,28,45,.9); color: var(--text);
          }
          .warning-top { display:flex; gap:10px; align-items:center; margin-bottom:6px; }
          .warning-top span { font-size:11px; font-weight:800; }
          .warning-card small, .context-card small, .evidence-card small { color: var(--muted); }
          .warning-list-item, .evidence-list-item {
            display: grid;
            grid-template-columns: 30px minmax(0, 1fr);
            gap: 10px;
            align-items: center;
            min-height: 54px;
            border: 1px solid rgba(136,161,190,.18);
            border-radius: 8px;
            padding: 9px 10px;
            margin-bottom: 8px;
            background: rgba(10, 22, 37, .72);
          }
          .warning-list-item.sev-critical {
            border-color: rgba(255,82,82,.42) !important;
            background: rgba(255,82,82,.07);
          }
          .warning-list-item.sev-warning, .warning-list-item.sev-caution {
            border-color: rgba(245,182,66,.35) !important;
            background: rgba(245,182,66,.06);
          }
          .warning-icon, .doc-icon {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            font-size: 14px;
            font-weight: 900;
            border: 2px solid currentColor;
          }
          .doc-icon {
            border-radius: 6px;
            border-width: 1px;
            color: #9fcfff;
            background: rgba(85,183,255,.09);
            font-size: 11px;
          }
          .warning-copy, .evidence-copy {
            min-width: 0;
          }
          .warning-copy strong, .evidence-copy strong {
            display: block;
            color: #e8f2ff;
            font-size: 12px;
            line-height: 1.25;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .warning-copy span, .evidence-copy span {
            display: block;
            margin-top: 3px;
            color: var(--muted);
            font-size: 11px;
            line-height: 1.25;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .context-title { color: #d9e8ff; font-weight:800; margin-bottom:6px; }
          .evidence-card {
            background: linear-gradient(145deg, rgba(18,35,56,.96), rgba(10,22,37,.96));
            border-color: rgba(85,183,255,.22);
          }
          .evidence-kicker {
            display:inline-flex; align-items:center; height:20px; padding:0 7px; margin-bottom:8px;
            border-radius:5px; background: rgba(85,183,255,.12); color:#8fd0ff;
            font-size:9px; font-weight:900; text-transform:uppercase; letter-spacing:.04em;
          }
          .evidence-topic {
            display:inline-flex; align-items:center; padding:3px 8px; margin-bottom:8px;
            border: 1px solid rgba(136,161,190,.22); border-radius:999px;
            color:#dceaff; font-size:11px; background:rgba(255,255,255,.04);
          }
          .evidence-card p { margin: 6px 0 8px; color:#dceaff; font-size:13px; line-height:1.45; }
          .empty-ok { color: var(--green); text-align:center; padding: 30px 12px; }
          .ok-icon {
            width: 52px; height: 52px; border-radius: 50%; display: grid; place-items:center;
            border: 2px solid var(--green); margin: 0 auto 12px; font-size: 32px;
            background: rgba(70,212,131,.12);
          }
          .ops-grid {
            border: 1px solid var(--line); border-radius: 8px; overflow-x: auto; overflow-y: hidden;
            background: rgba(7,17,29,.65);
          }
          .ops-head, .ops-row {
            display: grid; grid-template-columns: 1.05fr .85fr .85fr .65fr 1.12fr .88fr .78fr .62fr .68fr .55fr;
            gap: 0; align-items: center; min-width: 700px;
          }
          .ops-head {
            color: #c6d6e9; font-size: 11px; font-weight: 800;
            background: rgba(255,255,255,.035); border-bottom: 1px solid var(--line);
          }
          .ops-head div, .ops-row div { padding: 8px 8px; }
          .ops-row { color: #dceaff; font-size: 11px; border-bottom: 1px solid rgba(136,161,190,.13); }
          .ops-row:last-child { border-bottom: 0; }
          .ops-row .num { font-variant-numeric: tabular-nums; }
          .overview-head, .overview-row {
            display: grid; grid-template-columns: 1.08fr .85fr .85fr .55fr 1.08fr .85fr .72fr .62fr .55fr;
            align-items:center; min-width: 650px;
          }
          .overview-head {
            color: #c6d6e9; font-size: 10px; font-weight: 800; background: rgba(255,255,255,.045);
            border: 1px solid var(--line); border-bottom: 0; border-radius: 8px 8px 0 0;
          }
          .overview-row {
            color: #dceaff; font-size: 11px; background: rgba(7,17,29,.72);
            border-left: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid rgba(136,161,190,.14);
          }
          .overview-row:last-child { border-radius: 0 0 8px 8px; }
          .overview-head div, .overview-row div { padding: 8px 8px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
          .row-critical { background: rgba(255,82,82,.13); box-shadow: inset 3px 0 0 var(--red); }
          .row-warning { background: rgba(255,139,61,.10); box-shadow: inset 3px 0 0 var(--orange); }
          .row-caution { background: rgba(245,198,66,.10); box-shadow: inset 3px 0 0 var(--yellow); }
          .badge {
            display:inline-flex; align-items:center; border:1px solid var(--line); border-radius:5px;
            padding: 2px 6px; font-size: 9px; font-weight: 900; letter-spacing:0;
            background: rgba(255,255,255,.04);
          }
          .bar {
            display:inline-block; width: 40px; height: 5px; border-radius: 10px; margin-right: 5px;
            background: rgba(136,161,190,.2); vertical-align: middle; overflow:hidden;
          }
          .bar span { display:block; height: 100%; background: linear-gradient(90deg, var(--green), var(--yellow), var(--red)); border-radius: inherit; }
          .spark { width: 44px; height: 28px; display:block; }
          div[data-testid="stMetric"] { background: rgba(14,28,45,.75); border:1px solid var(--line); padding:12px; border-radius:8px; }
          [data-testid="stSidebar"] [data-testid="stSelectbox"] div { border-color: rgba(136,161,190,.22); }
          .stButton button {
            border-radius: 7px; border: 1px solid rgba(136,161,190,.25); background: rgba(24,43,65,.92);
          }
          .stTextInput input {
            background: rgba(14,28,45,.95); border-color: rgba(136,161,190,.22); color: var(--text);
          }

          /* Product dashboard density overrides */
          [data-testid="stAppViewContainer"] .main .block-container {
            max-width: 100%;
            padding: 1rem 1rem .8rem;
          }
          [data-testid="stSidebar"] {
            min-width: 250px !important;
            max-width: 250px !important;
          }
          [data-testid="stSidebar"] .stMarkdown h2 {
            font-size: 17px;
            margin: 0 0 1rem;
          }
          [data-testid="stSidebar"] label {
            font-size: 12px !important;
            color: #d7e4f5 !important;
          }
          [data-testid="stSidebar"] [data-testid="stSelectbox"] {
            margin-bottom: .55rem;
          }
          [data-testid="stVerticalBlock"] {
            gap: .44rem;
          }
          h3 {
            font-size: 14px !important;
            line-height: 1.2 !important;
            margin: 0 0 .48rem !important;
            color: #e8f2ff !important;
          }
          .topbar {
            padding: 0 4px 10px;
            margin-bottom: 10px;
          }
          .topbar h2 {
            font-size: 19px;
            line-height: 1.15;
          }
          .brand {
            font-size: 18px;
          }
          .metric-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
          }
          .metric-card {
            min-height: 100px;
            padding: 12px;
          }
          .metric-label {
            font-size: 11px;
            margin-bottom: 8px;
          }
          .metric-value {
            font-size: 24px;
          }
          .metric-card small {
            display: block;
            margin-top: 7px;
            color: var(--muted);
            font-size: 11px;
            line-height: 1.25;
          }
          .health-card {
            margin-top: 8px;
            min-height: 108px;
            display: flex;
            gap: 12px;
            align-items: center;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px;
            background: linear-gradient(145deg, rgba(20,38,58,.96), rgba(12,24,39,.96));
          }
          .health-icon {
            width: 42px;
            height: 42px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: rgba(245,182,66,.15);
            border: 1px solid rgba(245,182,66,.35);
            color: var(--yellow);
            font-size: 23px;
            font-weight: 900;
          }
          .health-title {
            font-size: 11px;
            color: var(--muted);
            margin-bottom: 4px;
          }
          .health-value {
            font-size: 18px;
            font-weight: 900;
            line-height: 1.1;
          }
          .health-copy {
            margin-top: 4px;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.35;
          }
          .compact-evidence {
            padding: 9px 10px;
            margin-bottom: 7px;
          }
          .compact-evidence .context-title {
            font-size: 12px;
            margin-bottom: 2px;
          }
          .compact-evidence .evidence-topic {
            font-size: 10px;
            padding: 2px 7px;
            margin-bottom: 5px;
          }
          .compact-evidence p {
            font-size: 11px;
            line-height: 1.35;
            margin: 4px 0;
          }
          .compact-evidence small {
            font-size: 10px;
          }
          .overview-head, .overview-row {
            min-width: 650px;
          }
          .element-container:has(.overview-head) {
            overflow-x: auto;
            border-radius: 8px;
          }
          .agent-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            height: 26px;
            padding: 0 10px;
            border-radius: 999px;
            border: 1px solid rgba(245,182,66,.32);
            color: #f5c542;
            background: rgba(245,182,66,.08);
            font-size: 11px;
            font-weight: 800;
          }
          .agent-status.online {
            border-color: rgba(70,212,131,.36);
            color: var(--green);
            background: rgba(70,212,131,.08);
          }
          .agent-answer {
            margin-top: 10px;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid rgba(136,161,190,.18);
            background: rgba(7,17,29,.68);
            color: #dceaff;
            font-size: 13px;
            line-height: 1.55;
          }
          .agent-answer p {
            margin: 0 0 10px;
          }
          .agent-answer p:last-child {
            margin-bottom: 0;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def cached_records(path: str) -> list[dict]:
    return load_predictions(path)


def cached_sections(_reload_token: int) -> list[dict]:
    return load_sections(KB_DIR)


def enrich_records(records: list[dict]) -> list[dict]:
    enriched = []
    for record in records:
        flags = get_flags(record)
        enriched_record = {**record, "flags": flags, "severity": calculate_severity(flags)}
        enriched.append(enriched_record)
    return sort_records_by_severity(enriched)


def render_digital_twin(selected: dict, line_records: list[dict]) -> None:
    by_name = {record["machine_name"]: record["severity"] for record in line_records}
    risk_stations = [
        {
            "machine_id": record["machine_id"],
            "name": record["machine_name"],
            "severity": record["severity"],
            "risk": round(record["failure_risk"], 2),
            "mode": record["predicted_failure_mode"].replace("_", " ").title(),
        }
        for record in line_records
        if record["severity"] in {"critical", "warning", "caution"}
    ]
    status = selected["severity"]
    status_label = STATUS_LABEL[status]
    alert_title = f"{selected['machine_id']} {selected['predicted_failure_mode'].replace('_', ' ').title()}"
    alert_copy = (
        f"Risk {selected['failure_risk']:.2f} over {selected['horizon_min']} min. "
        f"Queue {selected['queue_length']}/{selected['queue_capacity']}, "
        f"throughput {selected['predicted_throughput_units_per_hr']:.0f} uph."
    )

    def cls(name: str) -> str:
        sev = by_name.get(name, "normal")
        return "station-critical" if sev == "critical" else "station-warning" if sev in {"warning", "caution"} else ""

    if THREE_D_SCENE.exists():
        scene_html = THREE_D_SCENE.read_text(encoding="utf-8")
        risk_json = json.dumps(risk_stations)
        dashboard_css = f"""
        <style>
          .hud {{ left: 16px; top: 14px; max-width: 520px; }}
          .hud h1, .hud .lede, .metrics, .legend {{ display: none !important; }}
          .eyebrow {{
            height: 30px; border-radius: 8px; background: rgba(9, 20, 34, .82);
            border-color: rgba(139, 156, 184, .28); color: #e8f2ff;
          }}
          .dashboard-status {{
            position: fixed; right: 16px; top: 14px; z-index: 4;
            padding: 7px 12px; border-radius: 8px; font-size: 13px; font-weight: 900;
            border: 1px solid {"#ff5252" if status == "critical" else "#f5b642" if status in {"warning", "caution"} else "#46d483"};
            color: {"#ff6b6b" if status == "critical" else "#f5b642" if status in {"warning", "caution"} else "#46d483"};
            background: rgba(9, 20, 34, .88);
          }}
          .dashboard-alert {{
            position: fixed; left: 16px; bottom: 14px; z-index: 4;
            max-width: 420px; padding: 12px 14px; border-radius: 8px;
            background: rgba(9, 20, 34, .88); border: 1px solid rgba(255, 82, 82, .58);
            box-shadow: 0 18px 45px rgba(0,0,0,.28), 0 0 28px rgba(255,82,82,.14);
            color: #dbeafe; font-size: 13px; line-height: 1.45;
          }}
          .dashboard-alert strong {{ display:block; color:#ff6b6b; margin-bottom: 4px; }}
          .risk-legend {{
            position: fixed; left: 16px; top: 54px; z-index: 4;
            display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
            max-width: calc(100vw - 32px);
          }}
          .risk-chip {{
            display: inline-flex; align-items: center; gap: 7px; height: 28px;
            padding: 0 10px; border-radius: 999px;
            background: rgba(9, 20, 34, .82); border: 1px solid rgba(139, 156, 184, .24);
            color: #dbeafe; font-size: 11px; font-weight: 800;
          }}
          .risk-chip::before {{
            content: ""; width: 8px; height: 8px; border-radius: 50%;
            background: #46d483; box-shadow: 0 0 14px rgba(70,212,131,.7);
          }}
          .risk-chip.warn::before {{ background: #f5b642; box-shadow: 0 0 14px rgba(245,182,66,.8); }}
          .risk-chip.crit::before {{ background: #ff5252; box-shadow: 0 0 14px rgba(255,82,82,.9); }}
          .instructions {{
            right: 16px; bottom: 14px; width: auto; max-width: 330px; padding: 9px 11px;
            border-radius: 8px; font-size: 11px; background: rgba(9, 20, 34, .7);
          }}
          canvas {{ cursor: grab; }}
        </style>
        """
        if risk_stations:
            chip_html = "".join(
                f'<span class="risk-chip {"crit" if station["severity"] == "critical" else "warn"}">'
                f'{html.escape(station["machine_id"])} risk {station["risk"]:.2f}</span>'
                for station in risk_stations[:4]
            )
        else:
            chip_html = '<span class="risk-chip">All stations normal</span>'
        dashboard_overlay = f"""
        <div class="dashboard-status">{html.escape(status_label)}</div>
        <div class="risk-legend">{chip_html}</div>
        <div class="dashboard-alert">
          <strong>{html.escape(alert_title)}</strong>
          <span>{html.escape(alert_copy)}</span>
        </div>
        """
        risk_script = f"""
      const dashboardRiskStations = {risk_json};
      const riskStationPositions = {{
        Feeder: [-16.0, 0.04, 0],
        Filler: [-8.4, 0.04, 0],
        Sealer: [-2.1, 0.04, 0],
        Capper: [-2.1, 0.04, 0],
        Labeler: [4.2, 0.04, 0],
        Checker: [10.5, 0.04, 0],
        Packer: [6.3, 0.04, 7.2],
        Robot: [-5.8, 0.04, 7.2],
        Palletizer: [-9.2, 0.04, 7.2],
        Wrapper: [-13.0, 0.04, 7.2]
      }};
      const riskNameAliases = {{
        Feeder: ["feeder"],
        Filler: ["filler"],
        Sealer: ["capper", "sealer"],
        Capper: ["capper"],
        Labeler: ["labeler"],
        Checker: ["checker"],
        Packer: ["packer"],
        Robot: ["robot"],
        Palletizer: ["pallet", "palletizer"],
        Wrapper: ["wrapper"]
      }};
      const riskMarkers = [];

      function makeRiskLabel(text, severity) {{
        const canvas = document.createElement("canvas");
        canvas.width = 512;
        canvas.height = 160;
        const ctx = canvas.getContext("2d");
        const color = severity === "critical" ? "#ff5252" : "#f5b642";
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "rgba(9, 20, 34, 0.88)";
        ctx.strokeStyle = color;
        ctx.lineWidth = 5;
        roundRect(ctx, 12, 14, 488, 116, 18);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.font = "900 34px Inter, Segoe UI, Arial";
        ctx.fillText(severity === "critical" ? "CRITICAL" : "WARNING", 34, 58);
        ctx.fillStyle = "#e8f2ff";
        ctx.font = "800 28px Inter, Segoe UI, Arial";
        ctx.fillText(text.slice(0, 28), 34, 98);
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({{ map: texture, transparent: true, depthWrite: false }});
        const sprite = new THREE.Sprite(material);
        sprite.scale.set(4.6, 1.45, 1);
        return sprite;
      }}

      function applyRiskHighlight(station) {{
        const severity = station.severity;
        const baseColor = severity === "critical" ? 0xff5252 : 0xf5b642;
        const emissiveColor = severity === "critical" ? 0x8a1010 : 0x7a4a00;
        const stationName = station.name || "";
        const aliases = riskNameAliases[stationName] || [stationName.toLowerCase()];
        const position = riskStationPositions[stationName];
        const stationMaterial = new THREE.MeshStandardMaterial({{
          color: baseColor,
          roughness: 0.26,
          metalness: 0.16,
          emissive: emissiveColor,
          emissiveIntensity: severity === "critical" ? 0.78 : 0.45
        }});

        scene.traverse((object) => {{
          if (!object.isMesh || !object.name) return;
          const objectName = object.name.toLowerCase();
          if (aliases.some((alias) => objectName.includes(alias))) {{
            object.material = stationMaterial;
          }}
        }});

        if (!position) return;
        const group = new THREE.Group();
        group.position.set(position[0], position[1], position[2]);
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(1.95, 0.055, 12, 96),
          new THREE.MeshBasicMaterial({{ color: baseColor, transparent: true, opacity: 0.86 }})
        );
        ring.rotation.x = Math.PI / 2;
        const halo = new THREE.Mesh(
          new THREE.TorusGeometry(2.55, 0.035, 12, 96),
          new THREE.MeshBasicMaterial({{ color: baseColor, transparent: true, opacity: 0.32 }})
        );
        halo.rotation.x = Math.PI / 2;
        const pin = new THREE.Mesh(
          new THREE.ConeGeometry(0.42, 0.92, 3),
          new THREE.MeshBasicMaterial({{ color: baseColor }})
        );
        pin.position.set(0, 4.9, 0);
        pin.rotation.z = Math.PI;
        const light = new THREE.PointLight(baseColor, severity === "critical" ? 2.8 : 1.8, 7);
        light.position.set(0, 3.2, 0);
        const label = makeRiskLabel(`${{station.machine_id}}  ${{station.mode}}`, severity);
        label.position.set(0, 5.95, 0);
        group.add(ring, halo, pin, light, label);
        group.userData.severity = severity;
        riskMarkers.push(group);
        scene.add(group);
      }}

      dashboardRiskStations.forEach(applyRiskHighlight);
        """
        scene_html = scene_html.replace("</head>", f"{dashboard_css}</head>")
        scene_html = scene_html.replace('<div class="loading" id="loading">', f"{dashboard_overlay}<div class=\"loading\" id=\"loading\">")
        scene_html = scene_html.replace("      const clock = new THREE.Clock();", f"{risk_script}\n\n      const clock = new THREE.Clock();")
        scene_html = scene_html.replace(
            "        robot.rotation.y = Math.sin(time * 0.9) * 0.18;",
            """        robot.rotation.y = Math.sin(time * 0.9) * 0.18;
        riskMarkers.forEach((marker, index) => {
          const pulse = 1 + Math.sin(time * 3.4 + index) * 0.08;
          marker.scale.set(pulse, 1, pulse);
          marker.rotation.y = Math.sin(time * 0.9 + index) * 0.08;
          marker.children.forEach((child) => {
            if (child.isSprite) child.quaternion.copy(camera.quaternion);
          });
        });""",
        )
        components.html(scene_html, height=430, scrolling=False)
        return

    st.markdown(
        f"""
        <div class="hero-panel">
          <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
            <strong><span class="dot"></span> Live Digital Twin View</strong>
            <span class="status-pill {f"sev-{status}"}">{STATUS_LABEL[status]}</span>
          </div>
          <div class="line-art">
            <div class="rail"></div>
            <div class="belt main"></div><div class="belt return"></div>
            <div class="machine {cls("Filler")}" style="left:22%;top:28%;"></div>
            <div class="machine {cls("Sealer")}" style="left:36%;top:28%;"></div>
            <div class="machine {cls("Labeler")}" style="left:50%;top:28%;"></div>
            <div class="machine {cls("Checker")}" style="left:64%;top:28%;"></div>
            <div class="machine {cls("Packer")}" style="left:41%;top:57%;"></div>
            <div class="machine {cls("Palletizer")}" style="left:75%;top:58%;width:65px;height:65px;background:linear-gradient(145deg,#f97316,#89400d);"></div>
            <div class="station-label" style="left:10%;top:25%;"><span class="mini-dot"></span>Feeder</div>
            <div class="station-label" style="left:27%;top:18%;"><span class="mini-dot"></span>Filler</div>
            <div class="station-label" style="left:41%;top:18%;"><span class="mini-dot"></span>Sealing</div>
            <div class="station-label" style="left:55%;top:18%;"><span class="mini-dot"></span>Labeler</div>
            <div class="station-label" style="left:69%;top:18%;"><span class="mini-dot"></span>Checker</div>
            <div class="station-label" style="left:46%;top:51%;"><span class="mini-dot"></span>Packer</div>
            <div class="station-label" style="left:79%;top:51%;"><span class="mini-dot"></span>Palletizing</div>
            {''.join(f'<div class="box" style="left:{12 + i*5.3}%;top:{49 + (i%2)*2}%;"></div>' for i in range(13))}
            {''.join(f'<div class="box" style="left:{30 + i*4.8}%;top:{73 + (i%2)*2}%;"></div>' for i in range(10))}
            <div class="status-callout"><strong>Line Status: {STATUS_LABEL[status]}</strong><br>{selected["machine_id"]}: {selected["predicted_failure_mode"]}. Risk {selected["failure_risk"]:.2f}, queue {selected["queue_length"]}/{selected["queue_capacity"]}.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def set_agent_question(prompt: str) -> None:
    st.session_state.agent_question = prompt
    st.session_state.agent_run_requested = True
    st.session_state.pop("last_answer", None)
    st.session_state.pop("last_answer_scope", None)


def main() -> None:
    inject_css()
    data_files = sorted(DATA_DIR.glob("*.txt"))
    if "kb_reload_token" not in st.session_state:
        st.session_state.kb_reload_token = 0

    with st.sidebar:
        st.markdown("## TwinSentrix")
        st.caption("DATA & MODEL CONTROLS")
        data_file = st.selectbox("Prediction File", data_files, format_func=lambda p: p.name)
        OLLAMA_CLOUD_MODELS = [
            "gpt-oss:20b",
            "gpt-oss:120b",
            "qwen3-coder-next:cloud",
        ]

        model = st.selectbox(
            "Agent Reasoning Model",
            OLLAMA_CLOUD_MODELS,
            index=0,
        )
        
        use_llm = st.toggle("Use LLM reasoning", value=False)
        if st.button("Reload Knowledge Base", use_container_width=True):
            st.session_state.kb_reload_token += 1
        st.caption("Guidance library up to date.")

    records = cached_records(str(data_file))
    grouped = group_by_timestamp(records)
    timestamps = sorted(grouped.keys())

    with st.sidebar:
        timestamp = st.selectbox("Timestamp (from file)", timestamps, index=min(1, len(timestamps) - 1))
        line_records = enrich_records(grouped[timestamp])
        lines = sorted({record["line_id"] for record in line_records})
        selected_line = st.selectbox("Line", lines)
        line_records = [record for record in line_records if record["line_id"] == selected_line]
        machine_ids = [record["machine_id"] for record in line_records]
        selected_machine_id = st.selectbox("Machine", machine_ids)
        st.caption("Quick Links")
        st.write("Dashboard Home")
        st.write("Live Overview")
        st.write("Alerts & Events")
        st.write("Reports")

    selected = next(record for record in line_records if record["machine_id"] == selected_machine_id)
    all_flags = sort_flags([flag for record in line_records for flag in record["flags"]])
    selected_flags = selected["flags"]
    sections = cached_sections(st.session_state.kb_reload_token)

    st.markdown(
        """
        <div class="topbar">
          <div><h2 style="margin:0;">Manufacturing AI Agent Dashboard <span class="status-pill"><span class="dot"></span> System Monitor</span></h2></div>
          <div class="brand"><span class="live-pill">Live</span><span class="logo-mark">TS</span>TwinSentrix</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([3.15, 1.05])
    with left:
        render_digital_twin(selected, line_records)
    with right:
        avg_throughput = sum(record["predicted_throughput_units_per_hr"] for record in line_records) / len(line_records)
        reject_rate = 1.2 + max(record["failure_risk"] for record in line_records) * 4.8
        queue_total = sum(record["queue_length"] for record in line_records)
        worst = max(line_records, key=lambda record: SEVERITY_RANK[record["severity"]])
        health_label = STATUS_LABEL[worst["severity"]]
        health_copy = (
            "Immediate intervention recommended"
            if worst["severity"] == "critical"
            else "Model confidence reduced at one station"
            if worst["severity"] in {"warning", "caution"}
            else "No active issues detected"
        )
        st.markdown(
            f"""
            <div class="metric-grid">
              <div class="metric-card sev-normal">
                <div class="metric-label">Units per Hour</div>
                <div class="metric-value">{avg_throughput:,.0f}</div>
                <small>line average</small>
              </div>
              <div class="metric-card sev-{worst["severity"]}">
                <div class="metric-label">Reject Rate</div>
                <div class="metric-value">{reject_rate:.1f}%</div>
                <small>estimated from risk</small>
              </div>
              <div class="metric-card sev-{"warning" if queue_total > 60 else "normal"}">
                <div class="metric-label">Total Queue</div>
                <div class="metric-value">{queue_total}</div>
                <small>cases waiting</small>
              </div>
              <div class="metric-card sev-{worst["severity"]}">
                <div class="metric-label">Downtime Risk</div>
                <div class="metric-value">{health_label}</div>
                <small>{worst["machine_id"]} drives status</small>
              </div>
            </div>
            <div class="health-card sev-{worst["severity"]}">
              <div class="health-icon">!</div>
              <div>
                <div class="health-title">Overall Line Health</div>
                <div class="health-value">{health_label}</div>
                <div class="health-copy">{health_copy}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1, c2, c3, c4 = st.columns([2.7, 1.15, 1.15, 1.15])
    with c1:
        st.subheader("Line Overview")
        render_machine_overview(line_records)
    with c2:
        st.subheader("Active Warnings")
        render_warning_panel(all_flags)
    with c3:
        st.subheader(f"Machine Detail: {selected_machine_id}")
        st.markdown(f"**State:** {selected['machine_state']}")
        st.markdown(f"**Severity:** `{STATUS_LABEL[selected['severity']]}`")
        st.markdown(f"**Mode:** {selected['predicted_failure_mode']}")
        st.markdown(f"**Temperature:** {selected['temperature_c']:.1f} C")
        st.markdown(f"**Vibration:** {selected['vibration_rms']:.2f} RMS")
        st.markdown(f"**Power:** {selected['power_kw']:.1f} kW")
    with c4:
        st.subheader("Agent Evidence")
        preview_context = retrieve_context(sections, selected["machine_name"], selected["predicted_failure_mode"], selected_flags, "", limit=4)
        render_context_summary(preview_context)

    st.subheader("Machine Detail View")
    with st.expander("Open raw data, parsed prediction, and active flags", expanded=False):
        render_machine_detail(selected, selected_flags)

    st.subheader("Agentic Digital Twin Assistant")
    suggested = [
        "What happens if we keep running for 15 minutes?",
        "What if we reduce line speed by 20%?",
        "What if we stop this station for inspection?",
        "What if we clear the queue first?",
        "What maintenance action should happen next?",
    ]
    if "agent_question" not in st.session_state:
        st.session_state.agent_question = suggested[0]
    if "agent_run_requested" not in st.session_state:
        st.session_state.agent_run_requested = False

    st.caption("Scenario shortcuts")
    prompt_cols = st.columns(len(suggested))
    for idx, prompt in enumerate(suggested):
        prompt_cols[idx].button(
            prompt,
            key=f"scenario_prompt_{idx}",
            use_container_width=True,
            on_click=set_agent_question,
            args=(prompt,),
        )

    question = st.text_input(
        "Ask the local manufacturing agent",
        key="agent_question",
        placeholder="Ask a what-if question, e.g. what happens if we slow the line or keep running?",
    )
    contexts = retrieve_context(sections, selected["machine_name"], selected["predicted_failure_mode"], selected_flags, question, limit=6)
    ask = st.button("Ask Agent", type="primary")
    answer_scope = f"{timestamp}|{selected_machine_id}|{question}|{model}|llm={use_llm}"
    should_run_agent = (
        ask
        or st.session_state.get("agent_run_requested", False)
        or "last_answer" not in st.session_state
        or st.session_state.get("last_answer_scope") != answer_scope
    )
    if should_run_agent:
        if use_llm:
            answer, used_ollama = ask_ollama(selected, selected_flags, contexts, question, model=model, timeout=8)
        else:
            answer, used_ollama = fallback_answer(selected, selected_flags, contexts, question), False
        st.session_state.last_answer = answer
        st.session_state.used_ollama = used_ollama
        st.session_state.last_answer_scope = answer_scope
        st.session_state.agent_run_requested = False
    if st.session_state.used_ollama:
        status_html = '<span class="agent-status online"><span class="dot"></span> LLM reasoning active</span>'
    else:
        status_html = '<span class="agent-status">Fast scenario reasoning active</span>'
    answer_html = "".join(
        f"<p>{html.escape(part)}</p>"
        for part in str(st.session_state.last_answer).split("\n\n")
        if part.strip()
    )
    st.markdown(status_html, unsafe_allow_html=True)
    st.markdown(f'<div class="agent-answer">{answer_html}</div>', unsafe_allow_html=True)

    st.subheader("Evidence Used by the Agent")
    render_context_cards(contexts)


if __name__ == "__main__":
    main()
