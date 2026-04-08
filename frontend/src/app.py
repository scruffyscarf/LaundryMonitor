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
        
        if response.json()['alive'] == True:
            print("normik")
            return True
        else:
            print("Токен сдох")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"aliБэк не отвечает: {e}")
        return False


def main():
    st.set_page_config(page_title="Laundry Monitor", layout="wide")

    if "admin_token" not in st.session_state:
        st.session_state["admin_token"] = None

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

    try:
        machines, mocked = api.get_machines()
    except Exception as e:
        st.error(f"Failed to fetch machines: {e}")
        machines, mocked = [], False

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
        if st.sidebar.button("Sign in"):
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
        if st.sidebar.button("Sign out"):
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

        with st.sidebar.expander("Add machine", expanded=False):
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
                            _safe_rerun()
                            return
                        except Exception as e:
                            st.error(f"Failed to add machine: {e}")

        with st.sidebar.expander("Edit machine", expanded=False):
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
                    )
                    edit_type = st.selectbox(
                        "Machine type",
                        options=["Wash", "Dry"],
                        index=0
                        if selected_machine.type.lower().startswith("wash")
                        else 1,
                    )
                    edit_submit = st.form_submit_button("Save changes")
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
                                _safe_rerun()
                                return
                            except Exception as e:
                                st.error(f"Failed to update machine: {e}")

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
