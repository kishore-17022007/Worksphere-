from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import CalendarEvent, Holiday, LeaveRequest, LeaveStatus, User
from app.schemas import CalendarEventCreate, CalendarItem, HolidayCreate

router = APIRouter(prefix="/calendar", tags=["calendar"])
HR_ROLES = ("HR", "SUPER_ADMIN", "ADMIN")

@router.post("/events", response_model=CalendarItem, status_code=201)
async def create_event(data: CalendarEventCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = CalendarEvent(company_id=user.company_id, owner_id=user.id, **data.model_dump())
    db.add(row); await db.commit(); await db.refresh(row)
    return CalendarItem(kind="event", id=row.id, title=row.title, starts_at=row.starts_at, ends_at=row.ends_at, owner_id=row.owner_id)

@router.post("/holidays", status_code=201)
async def create_holiday(data: HolidayCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(*HR_ROLES))):
    row = Holiday(company_id=user.company_id, **data.model_dump())
    db.add(row); await db.commit(); await db.refresh(row)
    return row

@router.get("/events", response_model=list[CalendarItem])
async def calendar(start: date, end: date, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if end < start:
        raise HTTPException(422, "end must not precede start")
    start_dt, end_dt = datetime.combine(start, time.min), datetime.combine(end, time.max)
    events = await db.scalars(select(CalendarEvent).where(
        CalendarEvent.company_id == user.company_id,
        CalendarEvent.starts_at <= end_dt, CalendarEvent.ends_at >= start_dt,
        (CalendarEvent.is_private.is_(False) | (CalendarEvent.owner_id == user.id))))
    holidays = await db.scalars(select(Holiday).where(Holiday.company_id == user.company_id, Holiday.holiday_date.between(start, end)))
    leaves = await db.scalars(select(LeaveRequest).join(User, LeaveRequest.employee_id == User.id).where(
        User.company_id == user.company_id, LeaveRequest.status == LeaveStatus.APPROVED.value,
        LeaveRequest.start_date <= end, LeaveRequest.end_date >= start))
    items = [CalendarItem(kind="event", id=e.id, title=e.title, starts_at=e.starts_at, ends_at=e.ends_at, owner_id=e.owner_id) for e in events]
    items += [CalendarItem(kind="holiday", id=h.id, title=h.name, date=h.holiday_date) for h in holidays]
    items += [CalendarItem(kind="approved_leave", id=l.id, title="Approved leave", date=l.start_date, owner_id=l.employee_id) for l in leaves]
    return items
