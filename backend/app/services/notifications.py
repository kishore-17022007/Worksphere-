import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Notification, NotificationPreference

async def notify(db: AsyncSession, user_id, event_type: str, title: str, body: str, payload=None):
    pref = await db.scalar(select(NotificationPreference).where(
        NotificationPreference.user_id == user_id, NotificationPreference.event_type == event_type))
    if pref and not pref.enabled:
        return None
    row = Notification(user_id=user_id, event_type=event_type, title=title, body=body,
                       payload=json.dumps(payload) if payload is not None else None)
    db.add(row)
    return row
