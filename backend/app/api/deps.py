import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.redis import redis_client
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)

async def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """Fail closed for abusive callers while tolerating an unavailable limiter."""
    redis_key = f"rate:{key}"
    try:
        count = await redis_client.incr(redis_key)
        if count == 1:
            await redis_client.expire(redis_key, window_seconds)
        if count > limit:
            raise HTTPException(status_code=429, detail="Too many requests")
    except HTTPException:
        raise
    except Exception:
        return

async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                           db: AsyncSession = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        try:
            revoked = await redis_client.get(f"revoked:{credentials.credentials}")
        except Exception:
            revoked = None
        if revoked:
            raise ValueError
        user = await db.scalar(select(User).options(selectinload(User.role)).where(User.id == uuid.UUID(payload["sub"])))
    except Exception:
        user = None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

async def authenticate_token(token: str, db: AsyncSession) -> User:
    """Authenticate a raw bearer token for HTTP and WebSocket callers."""
    try:
        payload = decode_token(token)
        if await redis_client.get(f"revoked:{token}"):
            raise ValueError
        user = await db.scalar(select(User).options(selectinload(User.role)).where(
            User.id == uuid.UUID(payload["sub"])))
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError, UnicodeError):
        user = None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

def require_roles(*roles: str):
    async def checker(user: User = Depends(get_current_user)):
        if not user.role or user.role.name not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return checker

def require_any_role(*roles: str):
    return require_roles(*roles)
