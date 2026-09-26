from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Company, Department, Team, TeamMember, User
from app.schemas import CompanyCreate, DepartmentCreate, TeamCreate, TeamMemberCreate

router = APIRouter(tags=["organization"])
management = require_roles("admin", "hr", "ADMIN", "HR")

@router.post("/companies", status_code=201)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles("admin", "ADMIN"))):
    company = Company(name=data.name); db.add(company); await db.commit(); await db.refresh(company)
    return {"id": company.id, "name": company.name}

@router.post("/departments", status_code=201)
async def create_department(data: DepartmentCreate, db: AsyncSession = Depends(get_db), _=Depends(management)):
    department = Department(**data.model_dump()); db.add(department); await db.commit(); await db.refresh(department)
    return {"id": department.id, "name": department.name, "company_id": department.company_id}

@router.get("/departments")
async def list_departments(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Department).where(Department.company_id == user.company_id))
    return list(rows.all())

@router.post("/teams", status_code=201)
async def create_team(data: TeamCreate, db: AsyncSession = Depends(get_db), _=Depends(management)):
    team = Team(**data.model_dump()); db.add(team); await db.commit(); await db.refresh(team)
    return {"id": team.id, "name": team.name, "department_id": team.department_id}

@router.get("/teams")
async def list_teams(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Team).join(Department).where(Department.company_id == user.company_id))
    return list(rows.all())

@router.post("/teams/{team_id}/members", status_code=201)
async def add_member(team_id: str, data: TeamMemberCreate, db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    allowed = user.role and user.role.name in {"admin", "hr", "ADMIN", "HR"}
    if not allowed:
        membership = await db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user.id, TeamMember.is_lead.is_(True)))
        allowed = membership is not None
    if not allowed: raise HTTPException(403, "Only HR, admins, or team leads may manage members")
    member = TeamMember(team_id=team_id, **data.model_dump()); db.add(member); await db.commit(); await db.refresh(member)
    return {"id": member.id, "team_id": member.team_id, "user_id": member.user_id, "is_lead": member.is_lead}
