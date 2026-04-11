import os
import time
import requests
from datetime import UTC, datetime

import jwt
import streamlit as st

from . import admin_cookies, api, ui

REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "30"))
_ADMIN_JWT_ALG = "HS256"
BACKEND_URL = os.getenv('BACKEND_API_URL')


def _remaining_seconds(token: str | None) -> int | None:
    if not token:
        return None
    try:
        decoded = jwt.decode(
            token,
            algorithms=[_ADMIN_JWT_ALG],
            options={"verify_signature": False, "verify_exp": False},
        )
        exp = decoded.get("exp")
        if exp is None:
            return None
        return max(0, int(exp - datetime.now(UTC).timestamp()))
    except jwt.InvalidTokenError:
        return None


def _safe_rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
        return
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def _token_still_valid(token: str | None) -> bool:
    """True if token parses and is not expired. Signature is checked by the API, not here."""
    if not token:
        return False
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.json().get('alive') == True:
            return True
        else:
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Backend unreachable: {e}")
        return False


def deduplicate_machines(machines):
    """Remove duplicate machines from the list"""
    seen_ids = set()
    seen_names = set()
    unique_machines = []
    
    for m in machines:
        # Try to use machine ID if available
        if hasattr(m, 'id') and m.id is not None:
            if m.id not in seen_ids:
                seen_ids.add(m.id)
                unique_machines.append(m)
        else:
            # Fall back to name + type combination
            key = f"{m.name}_{m.type}".lower()
            if key not in seen_names:
                seen_names.add(key)
                unique_machines.append(m)
    
    return unique_machines


def main():
    st.set_page_config(page_title="Laundry Monitor", layout="wide")

    if "admin_token" not in st.session_state:
        st.session_state["admin_token"] = None
    
    # Initialize session state for machines cache
    if "machines_cache" not in st.session_state:
        st.session_state["machines_cache"] = None
    if "last_update" not in st.session_state:
        st.session_state["last_update"] = 0

    admin_cookies.flush_pending_storage_writes()
    admin_cookies.restore_admin_token_from_cookie(_token_still_valid)

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

    # Fetch machines only if needed
    current_time = time.time()
    should_refresh = (
        refresh_btn or 
        st.session_state["machines_cache"] is None or
        (auto_refresh and current_time - st.session_state["last_update"] >= REFRESH_SECONDS)
    )
    
    if should_refresh:
        try:
            machines, mocked = api.get_machines()
            # Remove duplicates BEFORE any processing
            machines = deduplicate_machines(machines)
            st.session_state["machines_cache"] = machines
            st.session_state["last_update"] = current_time
            st.session_state["mocked"] = mocked
        except Exception as e:
            st.error(f"Failed to fetch machines: {e}")
            if st.session_state["machines_cache"] is None:
                st.session_state["machines_cache"] = []
            st.session_state["mocked"] = False
    else:
        machines = st.session_state["machines_cache"]
        mocked = st.session_state.get("mocked", False)

    if mocked:
        err = api.get_last_backend_error() or "unknown error"
        st.warning(
            f"Backend unreachable at **{api.get_backend_url()}** — showing mock data. "
            f"Last error: {err}. "
            "Set `BACKEND_API_URL` in `frontend/.env` (or repo root `.env`) and ensure "
            "uvicorn is running (e.g. `cd backend && python run.py`)."
        )

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

    # Clear and recreate grid of cards - use empty container approach
    # Create a placeholder for the machines grid
    machines_container = st.container()
    
    with machines_container:
        # Create columns for the grid
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
        key="machine_select"
    )
    status = st.sidebar.radio(
        "Status *",
        options=["free", "busy", "unavailable"],
        format_func=lambda s: s.title(),
        key="status_radio"
    )
    
    time_remaining = 0
    if status == "busy":
        time_remaining = st.sidebar.number_input(
            "Time remaining (minutes)",
            min_value=0,
            value=0,
            key="time_remaining"
        )
    reporter = st.sidebar.text_input("Reporter (optional)", key="reporter_input")

    if st.sidebar.button("Submit", key="submit_report"):
        if not machine_options:
            st.sidebar.error("No machines available to report on.")
        else:
            mid = machine_options[machine_name]
            tr = int(time_remaining) if status == "busy" and time_remaining > 0 else None
            try:
                api.post_report(
                    mid,
                    status,
                    time_remaining=tr,
                    reporter=reporter or None,
                )
                st.sidebar.success("Report submitted")
                # Clear cache to force refresh
                st.session_state["machines_cache"] = None
                time.sleep(0.5)
                _safe_rerun()
                return
            except Exception as e:
                st.sidebar.error(f"Failed to submit report: {e}")

    st.sidebar.divider()
    st.sidebar.header("Admin")

    token = st.session_state.get("admin_token")
    admin_ok = _token_still_valid(token)

    if token and not admin_ok:
        st.session_state["admin_token"] = None
        admin_cookies.clear_admin_token_cookie()
        st.sidebar.info("Admin session expired. Please sign in again.")

    if not admin_ok:
        admin_pw = st.sidebar.text_input(
            "Admin password",
            type="password",
            key="admin_password_input",
        )
        if st.sidebar.button("Sign in", key="sign_in"):
            try:
                data = api.login_admin(admin_pw)
                tok = data.get("access_token")
                st.session_state["admin_token"] = tok
                admin_cookies.save_admin_token_cookie(tok or "")
                st.sidebar.success("Signed in")
                _safe_rerun()
                return
            except Exception:
                st.sidebar.error("Invalid password or backend unreachable.")
    else:
        if st.sidebar.button("Sign out", key="sign_out"):
            st.session_state["admin_token"] = None
            admin_cookies.clear_admin_token_cookie()
            api.admin_logout(token)
            _safe_rerun()
            return

        rem = _remaining_seconds(token)
        if rem is not None:
            st.sidebar.caption(
                f"Admin session expires in {rem // 60} min {rem % 60} s."
            )

        # Add machine section
        with st.sidebar.expander("➕ Add machine", expanded=False):
            with st.form("add_machine_form", clear_on_submit=True):
                new_name = st.text_input("Machine name")
                new_type = st.selectbox("Machine type", options=["Wash", "Dry"])
                add_submit = st.form_submit_button("Add machine")
                if add_submit:
                    if not new_name.strip():
                        st.error("Machine name is required.")
                    else:
                        try:
                            api.add_machine(
                                new_name.strip(),
                                new_type.lower(),
                                token,
                            )
                            st.success("Machine added")
                            st.session_state["machines_cache"] = None  # Clear cache
                            _safe_rerun()
                            return
                        except Exception as e:
                            st.error(f"Failed to add machine: {e}")

        # Edit machine section - only ONE instance
        with st.sidebar.expander("✏️ Edit machine", expanded=False):
            edit_options = {f"{m.id} - {m.name}": m for m in machines}
            if not edit_options:
                st.info("No machines available.")
            else:
                selected_label = st.selectbox(
                    "Select machine",
                    options=list(edit_options.keys()),
                    key="edit_machine_select",
                )
                selected_machine = edit_options[selected_label]
                with st.form("edit_machine_form"):
                    edit_name = st.text_input(
                        "Machine name",
                        value=selected_machine.name,
                        key="edit_name"
                    )
                    edit_type = st.selectbox(
                        "Machine type",
                        options=["Wash", "Dry"],
                        index=0
                        if selected_machine.type.lower().startswith("wash")
                        else 1,
                        key="edit_type"
                    )
                    edit_submit = st.form_submit_button("💾 Save changes")
                    if edit_submit:
                        if not edit_name.strip():
                            st.error("Machine name is required.")
                        else:
                            try:
                                api.update_machine(
                                    selected_machine.id,
                                    edit_name.strip(),
                                    edit_type.lower(),
                                    token,
                                )
                                st.success("Machine updated")
                                st.session_state["machines_cache"] = None  # Clear cache
                                _safe_rerun()
                                return
                            except Exception as e:
                                st.error(f"Failed to update machine: {e}")
