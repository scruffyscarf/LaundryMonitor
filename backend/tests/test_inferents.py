from datetime import datetime, timedelta, timezone
from src.crud import infer_status
from src.models import Report


def make_report(status, minutes=None, delta_minutes=0):
    return Report(
        status=status,
        time_remaining=minutes,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=delta_minutes)
    )


def test_unavailable():
    r = make_report("unavailable")
    status, _ = infer_status(r)
    assert status == "Unavailable"


def test_busy_with_time_active():
    r = make_report("busy", minutes=10, delta_minutes=5)
    status, remaining = infer_status(r)

    assert status == "Busy"
    assert remaining > 0


def test_busy_with_time_finished():
    r = make_report("busy", minutes=10, delta_minutes=15)
    status, remaining = infer_status(r)

    assert status == "Free"
    assert remaining == 0


def test_busy_without_time_recent():
    r = make_report("busy", minutes=None, delta_minutes=60)
    status, _ = infer_status(r)

    assert status == "Busy"


def test_busy_without_time_old():
    r = make_report("busy", minutes=None, delta_minutes=300)
    status, _ = infer_status(r)

    assert status == "Probably_Free"


def test_free():
    r = make_report("free")
    status, _ = infer_status(r)

    assert status == "Free"
