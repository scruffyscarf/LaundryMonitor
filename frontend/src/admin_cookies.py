"""
Persist admin JWT token in localStorage
"""
from __future__ import annotations

import json

import streamlit as st

STORAGE_KEY = "laundry_monitor_admin_token"

try:
    from streamlit_js_eval import streamlit_js_eval as _js_eval
except ImportError:
    _js_eval = None


def _eval_expr(expr: str, key: str):
    if _js_eval is None:
        return None
    return _js_eval(js_expressions=expr, key=key)


def flush_pending_storage_writes() -> None:
    """Write token to localStorage after login (runs at script top, not inside button handlers)."""
    tok = st.session_state.pop("_pending_admin_ls_write", None)
    if not tok or _js_eval is None:
        return
    k = json.dumps(STORAGE_KEY)
    v = json.dumps(tok)
    expr = f"(() => {{ localStorage.setItem({k}, {v}); return true; }})()"
    _eval_expr(expr, "laundry_monitor_ls_put")


def restore_admin_token_from_cookie(is_valid) -> None:
    """If session has no token yet, copy a valid value from localStorage into session_state."""
    if st.session_state.get("admin_token"):
        return
    if _js_eval is None:
        return
    raw = _eval_expr(
        f"localStorage.getItem({json.dumps(STORAGE_KEY)})",
        "laundry_monitor_ls_get",
    )
    if raw is None and not st.session_state.get("_ls_hydrate_retry_done"):
        st.session_state["_ls_hydrate_retry_done"] = True
        st.rerun()
    if raw and isinstance(raw, str) and is_valid(raw):
        st.session_state["admin_token"] = raw
    elif raw and isinstance(raw, str):
        _eval_expr(
            f"localStorage.removeItem({json.dumps(STORAGE_KEY)})",
            "laundry_monitor_ls_del_stale",
        )


def save_admin_token_cookie(token: str) -> None:
    """Schedule a localStorage write; flushed on the next run via flush_pending_storage_writes."""
    if token:
        st.session_state["_pending_admin_ls_write"] = token


def clear_admin_token_cookie() -> None:
    if _js_eval is None:
        return
    _eval_expr(
        f"localStorage.removeItem({json.dumps(STORAGE_KEY)})",
        "laundry_monitor_ls_clear",
    )
