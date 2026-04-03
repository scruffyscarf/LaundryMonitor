import os
import time

import streamlit as st

from . import api, ui

REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "30"))


def _safe_rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
        return
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def main():
    st.set_page_config(page_title="Laundry Monitor", layout="wide")

    left, right = st.columns([3, 1])

    with left:
        st.title("Laundry Monitor")

    with right:
        # controls inline to the right of the title
        c1, c2 = st.columns([1, 1])
        with c1:
            refresh_btn = st.button("Refresh")
        with c2:
            auto_refresh = st.checkbox(
                f"Auto-refresh ({REFRESH_SECONDS}s)",
                value=True,
            )

    try:
        machines, mocked = api.get_machines()
    except Exception as e:
        st.error(f"Failed to fetch machines: {e}")
        machines, mocked = [], False

    if mocked:
        st.warning("Backend unreachable — showing mock data.")

    # Filters (built-in Streamlit pills, strict mode)
    col1, col2 = st.columns(2)
    type_options = ["wash", "dry"]
    status_options = ["free", "busy", "probably_free", "unavailable"]

    with col1:
        types = st.pills(
            "Type",
            options=type_options,
            default=type_options,
            selection_mode="multi",
            key="types_filter",
            format_func=lambda v: "💧 Wash" if v == "wash" else "💨 Dry",
        )
    with col2:
        statuses = st.pills(
            "Status",
            options=status_options,
            default=status_options,
            selection_mode="multi",
            key="status_filter",
            format_func=lambda v: v.replace("_", " ").title(),
        )

    # strict: empty selection => show nothing
    types = types or []
    statuses = statuses or []

    # Normalize model values to lowercase/underscore so they match the
    # filter option strings (which are lowercase with underscores).
    filtered = [
        m
        for m in machines
        if (
            m.type.lower() in types
            and m.inferred_status().lower().replace(" ", "_") in statuses
        )
    ]

    # Grid of cards (3 columns)
    cols = st.columns(3)
    for i, m in enumerate(filtered):
        with cols[i % 3]:
            ui.card(m)

    # Sidebar: report form
    st.sidebar.header("Submit Report")

    machine_options = {m.name: m.id for m in machines}
    machine_name = st.sidebar.selectbox(
        "Machine *",
        options=list(machine_options.keys()) if machine_options else [],
    )
    status = st.sidebar.radio(
        "Status *",
        options=["free", "busy", "unavailable"],
        format_func=lambda s: s.title(),
    )
    time_remaining = st.sidebar.number_input(
        "Time remaining (minutes)",
        min_value=0,
        value=0,
    )
    reporter = st.sidebar.text_input("Reporter (optional)")

    if st.sidebar.button("Submit"):
        if not machine_options:
            st.sidebar.error("No machines available to report on.")
        else:
            mid = machine_options[machine_name]
            tr = int(time_remaining) if time_remaining > 0 else None
            try:
                api.post_report(
                    mid,
                    status,
                    time_remaining=tr,
                    reporter=reporter or None,
                )
                st.sidebar.success("Report submitted")
            except Exception as e:
                st.sidebar.error(f"Failed to submit report: {e}")

    # Handle refresh / auto-refresh
    filter_state = (tuple(types), tuple(statuses))
    prev_state = st.session_state.get("filter_state")
    st.session_state["filter_state"] = filter_state

    if refresh_btn:
        _safe_rerun()
        return

    if auto_refresh and prev_state == filter_state:
        time.sleep(REFRESH_SECONDS)
        _safe_rerun()
