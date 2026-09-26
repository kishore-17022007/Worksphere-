from contextlib import asynccontextmanager
import logging
import jwt

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as employee_router
from app.api.v1.organization import router as organization_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.leave import router as leave_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.workflow import router as workflow_router
from app.api.v1.collaboration import router as collaboration_router
from app.api.v1.intelligence import router as intelligence_router
from app.core.config import get_settings
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models import User
from app.services.audit import record_audit
from sqlalchemy import select
import uuid

logger = logging.getLogger("worksphere")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    application = FastAPI(title="WorkSphere API", version="1.0.0", lifespan=lifespan)

    @application.middleware("http")
    async def audit_sensitive_requests(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        is_sensitive = request.method in {"POST", "PUT", "PATCH", "DELETE"} or any(
            segment in path for segment in ("/files/", "/knowledge/")
        )
        if response.status_code < 400 and is_sensitive and path != "/api/v1/auth/login":
            authorization = request.headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                try:
                    payload = decode_token(authorization[7:].strip())
                    async with AsyncSessionLocal() as db:
                        user = await db.scalar(select(User).where(User.id == uuid.UUID(payload["sub"])))
                        if user:
                            await record_audit(
                                db, user, f"{request.method}_{path.rsplit('/', 1)[-1].upper()}",
                                path.split("/")[3] if len(path.split("/")) > 3 else "api",
                            )
                            await db.commit()
                except (jwt.InvalidTokenError, ValueError, KeyError, TypeError, UnicodeError) as exc:
                    logger.warning("Unable to audit request %s: %s", path, exc)
        return response
    if settings.allowed_hosts != "*":
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )
    application.include_router(health_router, prefix="/api/v1")
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(employee_router, prefix="/api/v1")
    application.include_router(organization_router, prefix="/api/v1")
    application.include_router(attendance_router, prefix="/api/v1")
    application.include_router(leave_router, prefix="/api/v1")
    application.include_router(calendar_router, prefix="/api/v1")
    application.include_router(workflow_router, prefix="/api/v1")
    application.include_router(collaboration_router, prefix="/api/v1")
    application.include_router(intelligence_router, prefix="/api/v1")
    return application


app = create_app()
