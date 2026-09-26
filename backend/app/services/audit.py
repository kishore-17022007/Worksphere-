import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog, User

async def record_audit(
    db: AsyncSession,
    user: User | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    if user is None:
        return
    db.add(AuditLog(company_id=user.company_id, actor_id=user.id, action=action,
                    entity_type=entity_type, entity_id=entity_id, details=metadata))
