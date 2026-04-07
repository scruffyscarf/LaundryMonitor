from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Optional


@dataclass
class Machine:
    id: int
    name: str
    type: str  # 'Wash' or 'Dry'
    status: str  # latest reported status: 'Free'|'Busy'|'Unavailable'
    time_remaining: Optional[int] = None  # minutes
    last_report_timestamp: Optional[datetime] = None

    def inferred_status(self, now: datetime = None) -> str:
        """Apply the project's inference rules locally.

        Mirrors the rules described in the README. Returns one of:
        'Free', 'Busy', 'Probably_Free', 'Unavailable'
        """
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        last_report = self.last_report_timestamp
        if last_report is not None and last_report.tzinfo is None:
            last_report = last_report.replace(tzinfo=UTC)

        status = (self.status or "").strip().lower()

        if status == "unavailable":
            return "Unavailable"

        if status == "free":
            return "Free"

        # status == 'Busy'
        if (
            status == "busy"
            and self.time_remaining is not None
            and last_report is not None
        ):
            end_time = last_report + timedelta(
                minutes=int(self.time_remaining)
            )
            if now < end_time:
                return "Busy"
            else:
                return "Free"

        # Busy with unknown end time
        if status == "busy" and last_report is not None:
            if now < last_report + timedelta(hours=4):
                return "Busy"
            else:
                return "Probably_Free"

        # fallback
        return self.status
