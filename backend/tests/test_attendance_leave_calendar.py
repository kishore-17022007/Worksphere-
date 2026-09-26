from datetime import date, datetime, timedelta
import uuid

import pytest
from pydantic import ValidationError

from app.models import AttendanceStatus, LeaveStatus
from app.schemas import CalendarEventCreate, LeaveRequestCreate


def test_attendance_statuses_cover_required_states() -> None:
    assert {item.value for item in AttendanceStatus} == {
        "PRESENT", "LATE", "ABSENT", "HALF_DAY", "LEAVE", "HOLIDAY"
    }


def test_leave_workflow_statuses_are_explicit() -> None:
    assert LeaveStatus.APPROVED.value == "approved"
    assert LeaveStatus.REJECTED.value == "rejected"
    assert LeaveStatus.CANCELLED.value == "cancelled"


def test_leave_date_range_rejects_inverted_dates() -> None:
    with pytest.raises(ValidationError):
        LeaveRequestCreate(
            leave_type_id=uuid.uuid4(),
            start_date=date(2026, 5, 10),
            end_date=date(2026, 5, 9),
        )


def test_calendar_event_requires_positive_duration() -> None:
    starts_at = datetime(2026, 5, 10, 9)
    with pytest.raises(ValidationError):
        CalendarEventCreate(
            title="Training",
            starts_at=starts_at,
            ends_at=starts_at - timedelta(minutes=1),
        )
