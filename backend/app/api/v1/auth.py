from datetime import timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import enforce_rate_limit, get_current_user, bearer
from app.core.redis import redis_client
from app.core.security import (create_access_token, create_refresh_token, decode_token,
                               hash_password, verify_password)
from app.db.session import get_db
from app.models import User
from app.services.audit import record_audit
from app.schemas import (ForgotPasswordRequest, LoginRequest, PasswordChange,
                         RefreshRequest, ResetPasswordRequest, TokenResponse, UserRead)

router = APIRouter(prefix="/auth", tags=["auth"])

def user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id, email=user.email, full_name=user.full_name, company_id=user.company_id,
        department_id=user.department_id, team_id=user.team_id,
        reporting_manager_id=user.reporting_manager_id, role_id=user.role_id,
        is_active=user.is_active, role=user.role.name if user.role else None,
    )

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    await enforce_rate_limit(f"login:{data.email.lower()}", 10, 300)
    user = await db.scalar(select(User).options(selectinload(User.role)).where(User.email == data.email.lower()))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    await record_audit(db, user, "LOGIN", "user", user.id)
    await db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)), user=user_read(user))

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token, "refresh")
        if await redis_client.get(f"revoked:{data.refresh_token}"):
            raise ValueError
        user = await db.scalar(select(User).options(selectinload(User.role)).where(User.id == payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        user = None
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid refresh token")
    return TokenResponse(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)), user=user_read(user))

@router.post("/logout")
async def logout(data: RefreshRequest, credentials=Depends(bearer), current: User = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    tokens = [credentials.credentials]
    try:
        payload = decode_token(data.refresh_token, "refresh")
        ttl = max(1, int(payload["exp"] - payload["iat"]))
        await redis_client.setex(f"revoked:{data.refresh_token}", ttl, "1")
        tokens.append(data.refresh_token)
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        ttl = 60
    for token in tokens:
        try:
            token_payload = decode_token(token, "refresh" if token == data.refresh_token else "access")
            token_ttl = max(1, int(token_payload["exp"] - token_payload["iat"]))
            await redis_client.setex(f"revoked:{token}", token_ttl, "1")
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            continue
    await record_audit(db, current, "LOGOUT", "user", current.id)
    await db.commit()
    return {"message": "Logged out"}

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user_read(user)

@router.post("/change-password")
async def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    await record_audit(db, user, "PASSWORD_CHANGED", "user", user.id)
    await db.commit()
    return {"message": "Password changed"}

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await enforce_rate_limit(f"reset:{data.email.lower()}", 5, 900)
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user:
        token = secrets.token_urlsafe(32)
        await redis_client.setex(f"reset:{token}", 900, str(user.id))
    return {"message": "If the account exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        user_id = await redis_client.get(f"reset:{data.token}")
        if not user_id:
            raise ValueError
        user = await db.get(User, user_id)
        await redis_client.delete(f"reset:{data.token}")
    except Exception:
        user = None
    if not user:
        raise HTTPException(400, "Invalid or expired reset token")
    user.password_hash = hash_password(data.new_password)
    await record_audit(db, user, "PASSWORD_RESET", "user", user.id)
    await db.commit()
    return {"message": "Password reset"}
