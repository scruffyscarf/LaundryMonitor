from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from math import ceil

from . import models, schemas


def infer_status(report: models.Report) -> Tuple[str, int | None]:
    if not report:
        return "Free", None

    now = datetime.now(timezone.utc)
    ts = report.timestamp

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

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

    # 3. Busy without time
    if report.status.lower() == "busy" and report.time_remaining is None:
        if now < ts + timedelta(hours=4):
            return "Busy", None
        else:
            return "Probably_Free", None

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

    db_report = models.Report(
        machine_id=report.machine_id,
        timestamp=datetime.now(timezone.utc),
        status=report.status,
        time_remaining=report.time_remaining,
        reporter=report.reporter
    )

    print(vars(db_report))
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return db_report


def get_report_history(db: Session, machine_id: int):

    return db.query(models.Report)\
        .filter(models.Report.machine_id == machine_id)\
        .order_by(models.Report.timestamp.desc())\
        .limit(10).all()
