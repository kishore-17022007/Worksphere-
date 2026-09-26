from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from pwdlib import PasswordHash
from app.core.config import get_settings

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta},
                      get_settings().jwt_secret_key, algorithm=get_settings().jwt_algorithm)

def create_access_token(subject: str) -> str:
    return create_token(subject, "access", timedelta(minutes=get_settings().access_token_expire_minutes))

def create_refresh_token(subject: str) -> str:
    return create_token(subject, "refresh", timedelta(days=get_settings().refresh_token_expire_days))

def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=[get_settings().jwt_algorithm])
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise jwt.InvalidTokenError("invalid token type")
    return payload
