from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models import AuditLog, Role, User
from app.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/employees", tags=["employees"])
admin_hr = require_roles("admin", "hr", "ADMIN", "HR")

@router.get("", response_model=list[UserRead])
async def list_employees(q: str | None = Query(None), department_id: str | None = None,
                         db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    stmt = select(User)
    role = current.role.name if current.role else None
    if role not in {"SUPER_ADMIN", "HR"}:
        if role != "TEAM_LEAD" or current.team_id is None:
            raise HTTPException(403, "Insufficient permissions")
        stmt = stmt.where(User.team_id == current.team_id)
    if q:
        stmt = stmt.where(or_(User.email.ilike(f"%{q}%"), User.full_name.ilike(f"%{q}%")))
    if department_id:
        stmt = stmt.where(User.department_id == department_id)
    return list((await db.scalars(stmt)).all())

@router.post("", response_model=UserRead, status_code=201)
async def create_employee(data: UserCreate, db: AsyncSession = Depends(get_db), _=Depends(admin_hr)):
    if data.role_id:
        role = await db.get(Role, data.role_id)
        if role and role.name == "SUPER_ADMIN":
            raise HTTPException(403, "Only super admins may create super admins")
    if await db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already exists")
    user = User(**data.model_dump(exclude={"password"}), email=data.email.lower(), password_hash=hash_password(data.password))
    db.add(user); await db.commit(); await db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=UserRead)
async def update_employee(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db), _=Depends(admin_hr)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "Employee not found")
    if data.role_id:
        role = await db.get(Role, data.role_id)
        if role and role.name == "SUPER_ADMIN":
            raise HTTPException(403, "Only super admins may assign super admins")
    for key, value in data.model_dump(exclude_unset=True).items(): setattr(user, key, value)
    await db.commit(); await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_employee(user_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_roles("admin", "ADMIN"))):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "Employee not found")
    user.is_active = False
    await db.commit()

@router.get("/audit-logs", dependencies=[Depends(require_roles("SUPER_ADMIN", "HR"))])
async def audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    rows = await db.scalars(
        select(AuditLog)
        .where(AuditLog.company_id == current.company_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(rows)
