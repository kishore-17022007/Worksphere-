import asyncio
import uuid

import pytest
from fastapi import HTTPException

from app.api.deps import require_roles
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Role, User


def test_passwords_are_hashed_and_verifiable() -> None:
    password = "Strong-password-123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_access_and_refresh_tokens_are_type_bound() -> None:
    subject = str(uuid.uuid4())
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    assert decode_token(access, "access")["sub"] == subject
    assert decode_token(refresh, "refresh")["sub"] == subject
    with pytest.raises(Exception):
        decode_token(access, "refresh")


def test_role_authorization_allows_matching_role() -> None:
    checker = require_roles("HR")
    user = User(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        email="hr@example.com",
        full_name="HR User",
        password_hash="not-used",
        role=Role(name="HR"),
        is_active=True,
    )
    assert asyncio.run(checker(user)) is user


def test_role_authorization_rejects_non_matching_role() -> None:
    checker = require_roles("SUPER_ADMIN")
    user = User(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        email="employee@example.com",
        full_name="Employee",
        password_hash="not-used",
        role=Role(name="EMPLOYEE"),
        is_active=True,
    )
    with pytest.raises(HTTPException) as error:
        asyncio.run(checker(user))
    assert error.value.status_code == 403
