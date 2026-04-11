import os
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from math import ceil

from . import models, schemas

MAX_MINUTES = int(os.getenv("LAUNDRY_MAX_MINUTES", 300))

def _normalize_machine_type(raw: str) -> str:
    t = (raw or "").strip().lower()
    if t in ("wash", "w"):
        return "Wash"
    if t in ("dry", "d"):
        return "Dry"
    raise ValueError("type must be wash or dry")


def _normalize_timestamp(report: models.Report) -> datetime:
    ts = report.timestamp
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def _busy_with_known_time(
    now: datetime,
    ts: datetime,
    report: models.Report,
) -> Tuple[str, int | None] | None:
    if report.status.lower() != "busy" or report.time_remaining is None:
        return None 
    
    time_raw = report.time_remaining

    # Fix overflow
    time_sanitized = min(report.time_remaining, MAX_MINUTES)
    end_time = ts + timedelta(minutes=time_sanitized)

    if now < end_time:
        remaining = (end_time - now).total_seconds() / 60
        return "Busy", ceil(remaining)
    return "Free", 0


def _busy_without_time(
    now: datetime,
    ts: datetime,
    report: models.Report,
) -> Tuple[str, int | None] | None:
    if report.status.lower() != "busy" or report.time_remaining is not None:
        return None

    if now < ts + timedelta(hours=4):
        return "Busy", None
    return "Probably_Free", None


def infer_status(report: models.Report) -> Tuple[str, int | None]:
    if not report:
        return "Free", None

    now = datetime.now(timezone.utc)
    ts = _normalize_timestamp(report)

    # 1. Unavailable
    if report.status.lower() == "unavailable":
        return "Unavailable", None

    known_time_result = _busy_with_known_time(now, ts, report)
    if known_time_result is not None:
        return known_time_result

    unknown_time_result = _busy_without_time(now, ts, report)
    if unknown_time_result is not None:
        return unknown_time_result

    # 4. Free
    if report.status.lower() == "free":
        return "Free", None

    return "Free", None


def get_all_machines(db: Session) -> List[schemas.MachineResponse]:

    subq = db.query(
        models.Report.machine_id,
        func.max(models.Report.timestamp).label("max_ts")
    ).group_by(models.Report.machine_id).subquery()

    rows = db.query(models.Machine, models.Report)\
        .outerjoin(subq, models.Machine.id == subq.c.machine_id)\
        .outerjoin(
            models.Report,
            (models.Report.machine_id == subq.c.machine_id) &
            (models.Report.timestamp == subq.c.max_ts)
        ).all()

    result = []

    for machine, report in rows:
        status, time_remaining = infer_status(report)

        result.append(schemas.MachineResponse(
            id=machine.id,
            name=machine.name,
            type=machine.type,
            status=status,
            time_remaining=time_remaining,
            last_report_timestamp=report.timestamp.isoformat()
            if report else None
        ))

    return result


def create_report(db: Session, report: schemas.Report):
    print(report)
    db_report = models.Report(
        machine_id=report.machine_id,
        timestamp=datetime.now(timezone.utc),
        status=report.status,
        time_remaining=report.time_remaining,
        reporter=report.reporter
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return db_report


def get_report_history(db: Session, machine_id: int):

    return db.query(models.Report)\
        .filter(models.Report.machine_id == machine_id)\
        .order_by(models.Report.timestamp.desc())\
        .limit(10).all()


def create_machine(db: Session, payload: schemas.MachineCreate) -> models.Machine:
    mtype = _normalize_machine_type(payload.type)
    db_machine = models.Machine(name=payload.name.strip(), type=mtype)
    db.add(db_machine)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_machine)
    return db_machine


def update_machine(
    db: Session,
    machine_id: int,
    payload: schemas.MachineUpdate,
) -> models.Machine | None:
    db_machine = (
        db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    )
    if not db_machine:
        return None
    mtype = _normalize_machine_type(payload.type)
    db_machine.name = payload.name.strip()
    db_machine.type = mtype
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_machine)
    return db_machine
