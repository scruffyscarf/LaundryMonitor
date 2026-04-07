import os
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Tuple

import requests

from .models import Machine


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # Repo root, then frontend/ (later overrides)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / ".env",
        here.parents[1] / ".env",
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=True)


_load_dotenv()

BASE = os.getenv("BACKEND_API_URL", "http://localhost:8000").rstrip("/")
LAST_BACKEND_ERROR: str | None = None


def get_backend_url() -> str:
    return BASE


def get_last_backend_error() -> str | None:
    return LAST_BACKEND_ERROR


def _parse_iso(s: str):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    except Exception:
        return None


def _mock_machines() -> List[Machine]:
    now = datetime.now(UTC)
    return [
        Machine(
            id=1,
            name="Washer 1",
            type="Wash",
            status="Free",
            time_remaining=None,
            last_report_timestamp=now,
        ),
        Machine(
            id=2,
            name="Washer 2",
            type="Wash",
            status="Busy",
            time_remaining=15,
            last_report_timestamp=now,
        ),
        Machine(
            id=3,
            name="Dryer 1",
            type="Dry",
            status="Busy",
            time_remaining=None,
            last_report_timestamp=now,
        ),
        Machine(
            id=4,
            name="Dryer 2",
            type="Dry",
            status="Unavailable",
            time_remaining=None,
            last_report_timestamp=now,
        ),
        Machine(
            id=5,
            name="Dryer 3",
            type="Dry",
            status="Probably_Free",
            time_remaining=None,
            last_report_timestamp=now,
        ),
    ]


def get_machines() -> Tuple[List[Machine], bool]:
    """Call GET /machines/ and return (machines, used_mock).

    If the backend is unreachable or returns an error, return mock data and
    used_mock=True.
    """
    global LAST_BACKEND_ERROR
    LAST_BACKEND_ERROR = None
    try:
        r = requests.get(f"{BASE}/machines/", timeout=5)
        r.raise_for_status()
        payload = r.json()
        machines = []
        for it in payload:
            ts = it.get("timestamp") or it.get("last_report_timestamp")
            name = it.get("name", f"Machine {it['id']}")
            machines.append(
                Machine(
                    id=it["id"],
                    name=name,
                    type=it.get("type", "Wash"),
                    status=it.get("status", "Free"),
                    time_remaining=it.get("time_remaining"),
                    last_report_timestamp=_parse_iso(ts),
                )
            )
        return machines, False
    except Exception as e:
        LAST_BACKEND_ERROR = f"{type(e).__name__}: {e}"
        return _mock_machines(), True


def post_report(
    machine_id: int,
    status: str,
    time_remaining: int = None,
    reporter: str = None,
):
    payload = {"machine_id": int(machine_id), "status": status}
    if time_remaining is not None:
        payload["time_remaining"] = int(time_remaining)
    if reporter:
        payload["reporter"] = reporter
    try:
        r = requests.post(f"{BASE}/report/", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"mock": True, "machine_id": machine_id, "status": status}


def login_admin(password: str) -> dict:
    r = requests.post(
        f"{BASE}/auth/login",
        json={"password": password},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def add_machine(name: str, machine_type: str, token: str) -> dict:
    r = requests.post(
        f"{BASE}/machines/",
        json={"name": name, "type": machine_type},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def update_machine(machine_id: int, name: str, machine_type: str, token: str) -> dict:
    r = requests.put(
        f"{BASE}/machines/{int(machine_id)}/",
        json={"name": name, "type": machine_type},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()
