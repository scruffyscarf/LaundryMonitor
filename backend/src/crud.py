from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from math import ceil
from fastapi import HTTPException, status

from . import models, schemas

MAX_TIME_REMAINING = 300  # 5 hours in minutes


def result_unavailable_or_busy(
        report: models.Report,
        now: datetime,
        ts: datetime) -> Tuple[str, int | None]:
    # 1. Unavailable
    if report.status.lower() == "unavailable":
        return "Unavailable", None

    # 2. Busy + known time
    if report.status.lower() == "busy" and report.time_remaining is not None:
        end_time = ts + timedelta(minutes=report.time_remaining)

        if now < end_time:
            remaining = (end_time - now).total_seconds() / 60
            return "Busy", ceil(remaining)
        else:
            return "Free", 0


def result_busy_or_probably_free(
        report: models.Report,
        now: datetime,
        ts: datetime) -> Tuple[str, int | None]:
    # 3. Busy without time
    if report.status.lower() == "busy" and report.time_remaining is None:
        if now < ts + timedelta(hours=4):
            return "Busy", None
        else:
            return "Probably_Free", None

    # 4. Free
    if report.status.lower() == "free":
        return "Free", None


def infer_status(report: models.Report) -> Tuple[str, int | None]:
    if not report:
        return "Free", None

    now = datetime.now(timezone.utc)
    ts = report.timestamp

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    result = result_unavailable_or_busy(report, now, ts)
    if result is not None:
        return result

    result = result_busy_or_probably_free(report, now, ts)
    if result is not None:
        return result

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

    db_report = models.Report(
        machine_id=report.machine_id,
        timestamp=datetime.now(timezone.utc),
        status=report.status,
        time_remaining=report.time_remaining,
        reporter=report.reporter
    )

    if (report.time_remaining is
            not None) and (report.time_remaining > MAX_TIME_REMAINING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"time_remaining cannot exceed {MAX_TIME_REMAINING} minutes"
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
