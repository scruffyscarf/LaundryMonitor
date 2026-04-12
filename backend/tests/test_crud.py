from src import crud, models, schemas
from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError


def test_create_report(db):
    report_data = type("obj", (), {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 10,
        "reporter": "test"
    })

    result = crud.create_report(db, report_data)

    assert result.id is not None
    assert result.machine_id == 1
    assert result.status == "busy"
    assert result.time_remaining == 10
    assert result.reporter == "test"
    assert result.timestamp is not None


def test_create_report_without_time_remaining(db):
    report_data = type("obj", (), {
        "machine_id": 1,
        "status": "free",
        "time_remaining": None,
        "reporter": None
    })

    result = crud.create_report(db, report_data)

    assert result.id is not None
    assert result.time_remaining is None


def test_get_report_history(db):
    for i in range(15):
        report = models.Report(
            machine_id=1,
            status="free",
            timestamp=datetime.now(timezone.utc),
            time_remaining=None,
            reporter=f"test_{i}"
        )
        db.add(report)
    db.commit()

    history = crud.get_report_history(db, 1)

    assert len(history) == 10

    for i in range(len(history) - 1):
        assert history[i].timestamp >= history[i + 1].timestamp

    for report in history:
        assert report.machine_id == 1


def test_get_report_history_empty(db):
    history = crud.get_report_history(db, 999)
    assert history == []


def test_create_machine(db):
    payload = schemas.MachineCreate(name="Washer 3", type="wash")

    result = crud.create_machine(db, payload)

    assert result.id is not None
    assert result.name == "Washer 3"
    assert result.type == "Wash"


def test_create_machine_type_normalization(db):
    test_cases = [
        ("wash", "Wash"),
        ("w", "Wash"),
        ("WASH", "Wash"),
        ("dry", "Dry"),
        ("d", "Dry"),
        ("DRY", "Dry"),
    ]

    for input_type, expected in test_cases:
        payload = schemas.MachineCreate(name=f"Test {input_type}", type=input_type)
        result = crud.create_machine(db, payload)
        assert result.type == expected


def test_create_machine_invalid_type(db):
    payload = schemas.MachineCreate(name="Invalid", type="invalid")

    with pytest.raises(ValueError, match="type must be wash or dry"):
        crud.create_machine(db, payload)


def test_create_machine_duplicate_name(db):
    payload1 = schemas.MachineCreate(name="Unique Washer", type="wash")
    crud.create_machine(db, payload1)

    payload2 = schemas.MachineCreate(name="Unique Washer", type="dry")

    with pytest.raises(IntegrityError):
        crud.create_machine(db, payload2)


def test_update_machine(db):
    payload = schemas.MachineCreate(name="Old Name", type="wash")
    machine = crud.create_machine(db, payload)

    update_payload = schemas.MachineUpdate(name="New Name", type="dry")
    result = crud.update_machine(db, machine.id, update_payload)

    assert result is not None
    assert result.name == "New Name"
    assert result.type == "Dry"


def test_update_machine_not_found(db):
    update_payload = schemas.MachineUpdate(name="Ghost", type="wash")
    result = crud.update_machine(db, 999, update_payload)

    assert result is None


def test_update_machine_duplicate_name(db):
    crud.create_machine(db, schemas.MachineCreate(name="First", type="wash"))
    m2 = crud.create_machine(db, schemas.MachineCreate(name="Second", type="dry"))

    update_payload = schemas.MachineUpdate(name="First", type="dry")

    with pytest.raises(IntegrityError):
        crud.update_machine(db, m2.id, update_payload)


def test_get_all_machines(db):
    crud.create_machine(db, schemas.MachineCreate(name="M1", type="wash"))
    crud.create_machine(db, schemas.MachineCreate(name="M2", type="dry"))

    report_data = type("obj", (), {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 10,
        "reporter": None
    })
    crud.create_report(db, report_data)

    machines = crud.get_all_machines(db)

    assert len(machines) == 2
    for m in machines:
        assert hasattr(m, "status")
        assert hasattr(m, "time_remaining")
