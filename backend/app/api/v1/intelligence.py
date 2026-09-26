import uuid
from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import (ActivityEvent, Attendance, DailyPlan, DailyPlanItem, LeaveRequest,
                        Meeting, MeetingParticipant, Project, Task, User)
from app.models.leave import LeaveStatus
from app.schemas import DailyPlanItemCreate, DailyPlanItemRead, DailyPlanItemUpdate, ActivityEventRead, ActivityEventCreate
from app.services.intelligence import calculate_daily_plan, aggregate_workload, weekly_summary

router = APIRouter(tags=["workplace intelligence"])
MANAGEMENT = ("admin", "ADMIN", "hr", "HR", "manager", "MANAGER", "team_lead", "TEAM_LEAD")

async def _today_data(db, user, day):
    tasks = (await db.scalars(select(Task).where(Task.assignee_id == user.id))).all()
    meetings = (await db.scalars(select(Meeting).where(Meeting.company_id == user.company_id,
        Meeting.starts_at < datetime.combine(day + timedelta(days=1), time.min),
        Meeting.ends_at >= datetime.combine(day, time.min),
        or_(Meeting.organizer_id == user.id, Meeting.id.in_(select(MeetingParticipant.meeting_id).where(MeetingParticipant.user_id == user.id)))))).all()
    leave = await db.scalar(select(LeaveRequest.id).where(LeaveRequest.employee_id == user.id, LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.start_date <= day, LeaveRequest.end_date >= day))
    return tasks, meetings, bool(leave)

@router.get("/daily-plan", response_model=list[DailyPlanItemRead])
async def get_daily_plan(day: date = Query(default=None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    day = day or date.today()
    plan = await db.scalar(select(DailyPlan).where(DailyPlan.user_id == user.id, DailyPlan.plan_date == day))
    if not plan:
        tasks, meetings, on_leave = await _today_data(db, user, day)
        plan = DailyPlan(user_id=user.id, plan_date=day, available_minutes=0 if on_leave else 480)
        db.add(plan); await db.flush()
        for pos, item in enumerate(calculate_daily_plan(tasks, meetings, day, plan.available_minutes, on_leave)):
            db.add(DailyPlanItem(plan_id=plan.id, position=pos, **item))
        await db.commit()
    return (await db.scalars(select(DailyPlanItem).where(DailyPlanItem.plan_id == plan.id).order_by(DailyPlanItem.position))).all()

@router.post("/daily-plan/items", response_model=DailyPlanItemRead)
async def add_plan_item(data: DailyPlanItemCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    plan = await db.scalar(select(DailyPlan).where(DailyPlan.user_id == user.id, DailyPlan.plan_date == date.today()))
    if not plan: raise HTTPException(404, "Generate today's plan first")
    item = DailyPlanItem(plan_id=plan.id, is_manual=True, **data.model_dump())
    db.add(item); await db.commit(); await db.refresh(item); return item

@router.patch("/daily-plan/items/{item_id}", response_model=DailyPlanItemRead)
async def edit_plan_item(item_id: uuid.UUID, data: DailyPlanItemUpdate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    item = await db.scalar(select(DailyPlanItem).join(DailyPlan).where(
        DailyPlanItem.id == item_id, DailyPlan.user_id == user.id))
    if not item: raise HTTPException(404, "Plan item not found")
    for key, value in data.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    item.is_manual = True
    await db.commit(); await db.refresh(item); return item

@router.get("/activity-events", response_model=list[ActivityEventRead])
async def activity_timeline(limit: int = Query(50, le=200), event_type: str | None = None,
                            db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(ActivityEvent).where(ActivityEvent.company_id == user.company_id)
    if event_type: q = q.where(ActivityEvent.event_type == event_type)
    return (await db.scalars(q.order_by(ActivityEvent.occurred_at.desc()).limit(limit))).all()

@router.post("/activity-events", response_model=ActivityEventRead, status_code=201)
async def record_activity(data: ActivityEventCreate, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    event = ActivityEvent(company_id=user.company_id, actor_id=user.id, **data.model_dump())
    db.add(event); await db.commit(); await db.refresh(event); return event

@router.get("/workload/team")
async def team_workload(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(*MANAGEMENT))):
    users = (await db.scalars(select(User).where(User.company_id == user.company_id, User.is_active.is_(True)))).all()
    out = []
    for member in users:
        tasks = (await db.scalars(select(Task).where(Task.assignee_id == member.id))).all()
        out.append({"user_id": member.id, "name": member.full_name, **aggregate_workload(tasks)})
    return out

@router.get("/weekly-summary")
async def weekly_report(start: date | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    start = start or (date.today() - timedelta(days=date.today().weekday())); end = start + timedelta(days=7)
    attendance = (await db.scalars(select(Attendance).where(Attendance.user_id == user.id, Attendance.attendance_date >= start, Attendance.attendance_date < end))).all()
    tasks = (await db.scalars(select(Task).where(Task.assignee_id == user.id))).all()
    meetings = (await db.scalars(select(Meeting).where(Meeting.organizer_id == user.id, Meeting.starts_at >= datetime.combine(start,time.min), Meeting.starts_at < datetime.combine(end,time.min)))).all()
    projects = (await db.scalars(select(Project).where(Project.owner_id == user.id))).all()
    leave = (await db.scalars(select(LeaveRequest).where(LeaveRequest.employee_id == user.id, LeaveRequest.status == LeaveStatus.APPROVED, LeaveRequest.start_date < end, LeaveRequest.end_date >= start))).all()
    return weekly_summary(attendance, tasks, meetings, projects, leave, start)

@router.get("/reports/{report_type}")
async def report(report_type: str, start: date | None = None, end: date | None = None,
                 db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if report_type not in {"hr", "team", "project", "task", "attendance", "meeting"}: raise HTTPException(400, "Unknown report")
    role_name = user.role.name if user.role else ""
    if report_type in {"hr", "team"} and role_name not in MANAGEMENT:
        raise HTTPException(403, "Insufficient permissions")
    if report_type == "team": return await team_workload(db, user)
    if start and end and end < start: raise HTTPException(400, "end must not precede start")
    if report_type == "attendance":
        q = select(Attendance).where(Attendance.user_id == user.id)
        if start: q = q.where(Attendance.attendance_date >= start)
        if end: q = q.where(Attendance.attendance_date <= end)
        rows = (await db.scalars(q)).all()
    elif report_type == "task":
        rows = (await db.scalars(select(Task).where(Task.assignee_id == user.id))).all()
    elif report_type == "project":
        rows = (await db.scalars(select(Project).where(Project.owner_id == user.id))).all()
    elif report_type == "meeting":
        q = select(Meeting).where(Meeting.organizer_id == user.id)
        if start: q = q.where(Meeting.starts_at >= datetime.combine(start, time.min))
        if end: q = q.where(Meeting.starts_at < datetime.combine(end + timedelta(days=1), time.min))
        rows = (await db.scalars(q)).all()
    else:
        rows = (await db.scalars(select(User).where(User.company_id == user.company_id))).all()
    return rows
