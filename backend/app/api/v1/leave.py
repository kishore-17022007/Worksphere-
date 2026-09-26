from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import LeaveApproval, LeaveRequest, LeaveStatus, LeaveType, TeamMember, User
from app.schemas import LeaveDecision, LeaveRequestCreate, LeaveRequestRead, LeaveTypeCreate, LeaveTypeRead

router = APIRouter(prefix="/leave", tags=["leave"])
HR_ROLES = ("HR", "SUPER_ADMIN", "ADMIN")

@router.post("/types", response_model=LeaveTypeRead, status_code=201)
async def create_leave_type(data: LeaveTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(*HR_ROLES))):
    row = LeaveType(company_id=user.company_id, **data.model_dump())
    db.add(row); await db.commit(); await db.refresh(row)
    return row

@router.get("/types", response_model=list[LeaveTypeRead])
async def list_leave_types(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return list((await db.scalars(select(LeaveType).where(LeaveType.company_id == user.company_id, LeaveType.is_active.is_(True)))).all())

@router.post("/requests", response_model=LeaveRequestRead, status_code=201)
async def request_leave(data: LeaveRequestCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    leave_type = await db.scalar(select(LeaveType).where(LeaveType.id == data.leave_type_id, LeaveType.company_id == user.company_id, LeaveType.is_active.is_(True)))
    if not leave_type:
        raise HTTPException(404, "Leave type not found")
    overlap = await db.scalar(select(LeaveRequest.id).where(
        LeaveRequest.employee_id == user.id,
        LeaveRequest.status.in_([LeaveStatus.PENDING_TEAM_LEAD.value, LeaveStatus.PENDING_HR.value, LeaveStatus.APPROVED.value]),
        LeaveRequest.start_date <= data.end_date, LeaveRequest.end_date >= data.start_date))
    if overlap:
        raise HTTPException(409, "Leave dates overlap an existing request")
    row = LeaveRequest(employee_id=user.id, **data.model_dump())
    db.add(row); await db.commit(); await db.refresh(row)
    return row

@router.get("/requests", response_model=list[LeaveRequestRead])
async def list_requests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role and user.role.name in HR_ROLES:
        stmt = select(LeaveRequest).join(User, LeaveRequest.employee_id == User.id).where(User.company_id == user.company_id)
    else:
        stmt = select(LeaveRequest).where(LeaveRequest.employee_id == user.id)
    return list((await db.scalars(stmt.order_by(LeaveRequest.created_at.desc()))).all())

async def _decision(request_id, decision, comment, db, user):
    row = await db.scalar(select(LeaveRequest).join(User, LeaveRequest.employee_id == User.id).where(LeaveRequest.id == request_id, User.company_id == user.company_id))
    if not row:
        raise HTTPException(404, "Leave request not found")
    employee_team_id = await db.scalar(select(User.team_id).where(User.id == row.employee_id))
    team_lead = await db.scalar(select(TeamMember).where(
        TeamMember.team_id == employee_team_id, TeamMember.user_id == user.id,
        TeamMember.is_lead.is_(True))) if employee_team_id else None
    is_hr = user.role and user.role.name in HR_ROLES
    if row.status == LeaveStatus.PENDING_TEAM_LEAD.value:
        if not team_lead or row.employee_id == user.id:
            raise HTTPException(403, "Only the employee's team lead can decide this request")
        next_status = LeaveStatus.PENDING_HR.value if decision == "approved" else LeaveStatus.REJECTED.value
        role = "TEAM_LEAD"
    elif row.status == LeaveStatus.PENDING_HR.value:
        if not is_hr:
            raise HTTPException(403, "Only HR can decide this request")
        next_status = LeaveStatus.APPROVED.value if decision == "approved" else LeaveStatus.REJECTED.value
        role = "HR"
    else:
        raise HTTPException(409, "Leave request is no longer awaiting approval")
    row.status = next_status
    db.add(LeaveApproval(request_id=row.id, approver_id=user.id, role=role, decision=decision, comment=comment))
    await db.commit(); await db.refresh(row)
    return row

@router.post("/requests/{request_id}/approve", response_model=LeaveRequestRead)
async def approve(request_id: str, data: LeaveDecision = LeaveDecision(), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _decision(request_id, "approved", data.comment, db, user)

@router.post("/requests/{request_id}/reject", response_model=LeaveRequestRead)
async def reject(request_id: str, data: LeaveDecision = LeaveDecision(), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _decision(request_id, "rejected", data.comment, db, user)
