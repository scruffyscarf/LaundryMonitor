from typing import Optional
from pydantic import BaseModel, Field


class Report(BaseModel):
    machine_id: int = Field(gt=0)
    status: str
    time_remaining: Optional[int] = Field(default=None, ge=0)
    reporter: Optional[str] = None


class Machine(BaseModel):
    id: int
    name: str
    type: str


class MachineResponse(Machine):
    status: str = "Free"
    time_remaining: Optional[int] = None
    last_report_timestamp: Optional[str] = None
