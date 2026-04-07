# src/main.py
import datetime
import os

from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .auth import create_access_token, get_current_admin
from .database import Base, SessionLocal, engine, get_db

DEV = os.getenv("DEV", "false").lower() in ("1", "true", "yes")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def _seed_dev_data(db: Session) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    machines = [
        models.Machine(id=1, name="Washer 1", type="Wash"),
        models.Machine(id=2, name="Washer 2", type="Wash"),
        models.Machine(id=3, name="Dryer 1", type="Dry"),
        models.Machine(id=4, name="Dryer 2", type="Dry"),
        models.Machine(id=5, name="Dryer 3", type="Dry"),
    ]
    reports = [
        models.Report(
            machine_id=1,
            timestamp=now,
            status="Free",
            time_remaining=None,
            reporter="System Init Backend",
        ),
        models.Report(
            machine_id=2,
            timestamp=now,
            status="Free",
            time_remaining=None,
            reporter="System Init Backend",
        ),
        models.Report(
            machine_id=3,
            timestamp=now,
            status="Free",
            time_remaining=None,
            reporter="System Init Backend",
        ),
        models.Report(
            machine_id=4,
            timestamp=now,
            status="Free",
            time_remaining=None,
            reporter="System Init Backend",
        ),
        models.Report(
            machine_id=5,
            timestamp=now,
            status="Free",
            time_remaining=None,
            reporter="System Init Backend",
        ),
    ]
    db.add_all(machines)
    db.add_all(reports)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pytest sets TESTING=1 in conftest so we do not touch ./data/laundry.db.
    if os.getenv("TESTING") == "1":
        yield
        return

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if DEV and db.query(models.Machine).count() == 0:
            _seed_dev_data(db)
    finally:
        db.close()

    yield


app = FastAPI(title="LaundryMonitor Backend", lifespan=lifespan)


@app.post("/auth/login", response_model=schemas.TokenResponse)
def admin_login(body: schemas.LoginRequest):
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    return schemas.TokenResponse(access_token=create_access_token())


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


@app.post(
    "/machines/",
    response_model=schemas.Machine,
    dependencies=[Depends(get_current_admin)],
)
def create_machine(
    payload: schemas.MachineCreate,
    db: Session = Depends(get_db),
):
    try:
        m = crud.create_machine(db, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="A machine with this name already exists",
        ) from None
    return schemas.Machine(id=m.id, name=m.name, type=m.type)


@app.put(
    "/machines/{machine_id}/",
    response_model=schemas.Machine,
    dependencies=[Depends(get_current_admin)],
)
def update_machine(
    machine_id: int,
    payload: schemas.MachineUpdate,
    db: Session = Depends(get_db),
):
    try:
        m = crud.update_machine(db, machine_id, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="A machine with this name already exists",
        ) from None
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")
    return schemas.Machine(id=m.id, name=m.name, type=m.type)


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
