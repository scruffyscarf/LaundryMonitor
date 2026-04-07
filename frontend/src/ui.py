import streamlit as st

from .models import Machine


STATUS_COLORS = {
    "free": "#16a34a",
    "busy": "#dc2626",
    "probably_free": "#f59e0b",
    "unavailable": "#6b7280",
}


def _status_color(status: str) -> str:
    key = (status or "").strip().lower()
    return STATUS_COLORS.get(key, "#9CA3AF")


def card(m: Machine) -> None:
    status = m.inferred_status()
    color = _status_color(status)
    remaining = f"{m.time_remaining} min left" if m.time_remaining else ""
    icon = "💧" if m.type.lower().startswith("wash") else "💨"
    status_label = status.replace("_", " ").title()

    html = f"""
    <div style="padding:12px 16px;border-radius:8px;min-height:100px;
                background-color:{color}1a;margin-bottom:16px;">
      <div style="display:flex;justify-content:space-between;
                  align-items:center;">
        <div style="font-weight:600">{icon} {m.name}</div>
        <div style="color:{color};font-weight:700">{status_label}</div>
      </div>
      <div style="color:#6b7280;font-size:13px;margin-top:6px;">
        {remaining}
      </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
