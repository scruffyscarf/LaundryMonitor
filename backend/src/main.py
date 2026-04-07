# src/main.py
import datetime

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from typing import List

from . import schemas, crud, models
from .database import get_db

app = FastAPI(title="LaundryMonitor Backend")


@asynccontextmanager
async def lifespan(app):
    db = next(get_db())
    now = datetime.datetime.now(datetime.timezone.utc)

    if db.query(models.Machine).count() == 0:
        machines = [
            models.Machine(id=1, name="Washer 1", type="Wash"),
            models.Machine(id=2, name="Washer 2", type="Wash"),
            models.Machine(id=3, name="Dryer 1", type="Dry"),
            models.Machine(id=4, name="Dryer 2", type="Dry"),
            models.Machine(id=5, name="Dryer 3", type="Dry"),
        ]
        reports = [
            models.Report(machine_id=1, timestamp=now, status="Free",
                          time_remaining=None, reporter="System Init Backend"),
            models.Report(machine_id=2, timestamp=now, status="Free",
                          time_remaining=None, reporter="System Init Backend"),
            models.Report(machine_id=3, timestamp=now, status="Free",
                          time_remaining=None, reporter="System Init Backend"),
            models.Report(machine_id=4, timestamp=now, status="Free",
                          time_remaining=None, reporter="System Init Backend"),
            models.Report(machine_id=5, timestamp=now, status="Free",
                          time_remaining=None, reporter="System Init Backend"),
        ]

        db.add_all(machines)
        db.add_all(reports)
        db.commit()


@app.get("/machines/", response_model=List[schemas.MachineResponse])
def read_machines(db: Session = Depends(get_db)):
    """
    GET list of all machines
    {
        [
            (id, name, type(wash/dry)),
            (id, name, type(wash/dry)),
            ...
            (id, name, type(wash/dry)),
        ]
    }
    """
    return crud.get_all_machines(db)


@app.post("/report/", response_model=schemas.Report)
def post_report(report: schemas.Report, db: Session = Depends(get_db)):
    """
    GET a report about a machine's status.
    The report includes
    {
        id,
        machine_id,
        timestamp,
        status(free/busy/unavailable),
        time_remaining(int, nullable)
    }
    """
    return crud.create_report(db, report)


@app.get("/machines/{machine_id}/history", response_model=List[schemas.Report])
def get_history(machine_id: int, db: Session = Depends(get_db)):
    """
    Return last few reports for a machine by its ID (optional, for debugging).

    Path parameter:
    - machine_id: int

    Response:
    -   List of reports for this machine,
        ordered by timestamp descending,
        limited to 10
    """
    reports = crud.get_report_history(db, machine_id)
    if not reports:
        raise HTTPException(status_code=404,
                            detail="Machine not found or no reports")
    return reports
