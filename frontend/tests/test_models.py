from datetime import UTC, datetime, timedelta

from frontend.src.models import Machine


def test_inferred_status_Busy_with_remaining():
    now = datetime.now(UTC)
    m = Machine(
        id=1,
        name="Washer 1",
        type="Wash",
        status="Busy",
        time_remaining=30,
        last_report_timestamp=now,
    )
    assert m.inferred_status(now) == "Busy"


def test_inferred_status_Busy_expired():
    now = datetime.now(UTC)
    past = now - timedelta(minutes=61)
    m = Machine(
        id=1,
        name="Washer 1",
        type="Wash",
        status="Busy",
        time_remaining=30,
        last_report_timestamp=past,
    )
    assert m.inferred_status(now) == "Free"


def test_inferred_status_Busy_unknown_then_Probably_Free():
    now = datetime.now(UTC)
    past = now - timedelta(hours=5)
    m = Machine(
        id=2,
        name="Dryer 1",
        type="Dry",
        status="Busy",
        time_remaining=None,
        last_report_timestamp=past,
    )
    assert m.inferred_status(now) == "Probably_Free"
