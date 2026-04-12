from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)

    reports = relationship("Report", back_populates="machine")

    @property
    def last_report_timestamp(self):
        if self.reports:
            return max(r.timestamp for r in self.reports)
        return None


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, nullable=False)
    time_remaining = Column(Integer, nullable=True)

    reporter = Column(String, nullable=True)
    machine = relationship("Machine", back_populates="reports")
