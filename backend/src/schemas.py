from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str = Field(min_length=1)


class LogoutResponse(BaseModel):
    message: str = "poka poka"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenAliveResponse(BaseModel):
    alive: bool


class Report(BaseModel):
    machine_id: int
    status: str
    time_remaining: Optional[int] = None
    reporter: Optional[str] = None


class Machine(BaseModel):
    id: int
    name: str
    type: str


class MachineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)


class MachineUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)


class MachineResponse(Machine):
    status: str = "Free"
    time_remaining: Optional[int] = None
    last_report_timestamp: Optional[str] = None
