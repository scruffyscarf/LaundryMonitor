import datetime
import os
from contextlib import asynccontextmanager
from typing import List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .auth import create_access_token, get_current_admin, check_token_alive, REVOKED_TOKENS
from .database import Base, SessionLocal, engine, get_db

DEV = os.getenv("DEV", "false").lower() in ("1", "true", "yes")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
MAX_TIME = int(os.getenv("LAUNDRY_MAX_MINUTES", 300))
security = HTTPBearer()

Base.metadata.create_all(bind=engine)


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
    if os.getenv("TESTING") == "1":
        yield
        return

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.Machine).count() == 0:
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


@app.get("/auth/logout", response_model=schemas.LogoutResponse)
def admin_logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    REVOKED_TOKENS.add(token)
    return schemas.LogoutResponse(message="Logged out")


@app.get("/auth/verify", response_model=schemas.TokenAliveResponse)
def admin_verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return schemas.TokenAliveResponse(alive=check_token_alive(token))


@app.get("/machines/", response_model=List[schemas.MachineResponse])
def read_machines(db: Session = Depends(get_db)):
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
    print(report)

    if report.time_remaining is not None:
        if not isinstance(report.time_remaining, int):
            raise HTTPException(status_code=403, detail="Time should be a valid integer")
        elif report.time_remaining <= 0:
            raise HTTPException(status_code=403, detail="Time cannot be leq 0")
        elif report.time_remaining > MAX_TIME:
            raise HTTPException(status_code=403, detail="Time cannot exceed 300 minutes")

    return crud.create_report(db, report)


@app.get("/machines/{machine_id}/history", response_model=List[schemas.Report])
def get_history(machine_id: int, db: Session = Depends(get_db)):
    reports = crud.get_report_history(db, machine_id)
    if not reports:
        raise HTTPException(status_code=404,
                            detail="Machine not found or no reports")
    return reports
