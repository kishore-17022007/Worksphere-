from datetime import date
import calendar as calendar_lib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Attendance, AttendanceStatus, LeaveRequest, LeaveStatus, User
from app.schemas import AttendanceRead

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/check-in", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
async def check_in(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    on_leave = await db.scalar(select(LeaveRequest.id).where(
        LeaveRequest.employee_id == user.id, LeaveRequest.status == LeaveStatus.APPROVED.value,
        LeaveRequest.start_date <= today, LeaveRequest.end_date >= today))
    if on_leave:
        raise HTTPException(409, "Cannot check in while on approved leave")
    if await db.scalar(select(Attendance).where(Attendance.user_id == user.id, Attendance.attendance_date == today)):
        raise HTTPException(409, "Attendance already checked in today")
    row = Attendance(user_id=user.id, employee_id=user.id, attendance_date=today)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Attendance already checked in today")
    await db.refresh(row)
    return row

@router.post("/check-out", response_model=AttendanceRead)
async def check_out(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = await db.scalar(select(Attendance).where(Attendance.user_id == user.id, Attendance.attendance_date == date.today()))
    if not row:
        raise HTTPException(400, "Cannot check out without checking in")
    if row.check_out is not None:
        raise HTTPException(409, "Attendance already checked out")
    row.status = AttendanceStatus.PRESENT.value
    from sqlalchemy import func
    row.check_out = await db.scalar(select(func.now()))
    row.working_duration = int((row.check_out - row.check_in).total_seconds() / 60)
    await db.commit()
    await db.refresh(row)
    return row

@router.get("/me", response_model=list[AttendanceRead])
async def my_attendance(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return list((await db.scalars(select(Attendance).where(Attendance.user_id == user.id).order_by(Attendance.attendance_date.desc()))).all())

@router.get("/today", response_model=AttendanceRead | None)
async def today(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await db.scalar(select(Attendance).where(Attendance.user_id == user.id, Attendance.attendance_date == date.today()))

@router.get("/history", response_model=list[AttendanceRead])
async def history(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await my_attendance(db=db, user=user)

@router.get("/employees/{employee_id}", response_model=list[AttendanceRead])
async def employee_attendance(employee_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    target = await db.get(User, employee_id)
    if not target or target.company_id != user.company_id:
        raise HTTPException(404, "Employee not found")
    role = user.role.name if user.role else None
    if not (target.id == user.id or role in {"HR", "SUPER_ADMIN", "ADMIN"} or (role == "TEAM_LEAD" and target.team_id == user.team_id)):
        raise HTTPException(403, "Insufficient permissions")
    return list((await db.scalars(select(Attendance).where(Attendance.user_id == target.id).order_by(Attendance.attendance_date.desc()))).all())

@router.get("/team", response_model=list[AttendanceRead])
async def team_attendance(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    role = user.role.name if user.role else None
    if role not in {"TEAM_LEAD", "HR", "SUPER_ADMIN", "ADMIN"}:
        raise HTTPException(403, "Insufficient permissions")
    stmt = select(Attendance).join(User, Attendance.user_id == User.id).where(User.company_id == user.company_id)
    if role == "TEAM_LEAD":
        stmt = stmt.where(User.team_id == user.team_id)
    return list((await db.scalars(stmt.order_by(Attendance.attendance_date.desc()))).all())

@router.get("/reports/monthly", response_model=list[AttendanceRead])
async def monthly_report(year: int, month: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if month < 1 or month > 12:
        raise HTTPException(422, "month must be between 1 and 12")
    if not user.role or user.role.name not in {"HR", "SUPER_ADMIN", "ADMIN"}:
        raise HTTPException(403, "Insufficient permissions")
    start = date(year, month, 1)
    end = date(year, month, calendar_lib.monthrange(year, month)[1])
    stmt = select(Attendance).join(User, Attendance.user_id == User.id).where(
        User.company_id == user.company_id, Attendance.attendance_date.between(start, end)
    )
    return list((await db.scalars(stmt.order_by(Attendance.attendance_date))).all())
