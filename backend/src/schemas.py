from typing import Optional
from pydantic import BaseModel


class Report(BaseModel):
    machine_id: int
    status: str
    time_remaining: Optional[int] = None
    reporter: Optional[str] = None


class Machine(BaseModel):
    id: int
    name: str
    type: str


class MachineResponse(Machine):
    status: str = "Free"
    time_remaining: Optional[int] = None
    last_report_timestamp: Optional[str] = None
