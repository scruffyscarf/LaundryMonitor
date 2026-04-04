from src import crud, models
from datetime import datetime, timezone


def test_create_report(db):
    report = type("obj", (), {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 10,
        "reporter": "test"
    })

    result = crud.create_report(db, report)

    assert result.id is not None
    assert result.machine_id == 1


def test_get_report_history(db):
    r1 = models.Report(
        machine_id=1,
        status="free",
        timestamp=datetime.now(timezone.utc)
    )

    db.add(r1)
    db.commit()

    history = crud.get_report_history(db, 1)

    assert len(history) >= 1
    assert history[0].machine_id == 1
