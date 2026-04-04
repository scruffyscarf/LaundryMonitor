import os
from datetime import UTC, datetime
from typing import List, Tuple

import requests

from .models import Machine

BASE = os.getenv("BACKEND_API_URL", "http://localhost:8000").rstrip("/")


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
    """Call GET /machines and return (machines, used_mock).

    If the backend is unreachable or returns an error, return mock data and
    used_mock=True.
    """
    try:
        r = requests.get(f"{BASE}/machines", timeout=5)
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
    except Exception:
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
        r = requests.post(f"{BASE}/report", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"mock": True, "machine_id": machine_id, "status": status}
