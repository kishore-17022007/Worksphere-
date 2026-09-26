import json
import os
import re
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import authenticate_token, get_current_user, require_roles
from app.db.session import AsyncSessionLocal, get_db
from app.models import (Announcement, AnnouncementAcknowledgement, Conversation, ConversationMember,
    DocumentPermission, DocumentVersion, FileMetadata, KnowledgeCategory, KnowledgeDocument,
    Message, MessageReadStatus, Notification, User)
from app.services.storage import S3Storage, object_key
from app.services.notifications import notify
from app.services.audit import record_audit

ALLOWED_FILES = {
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg", "image/png", "image/gif", "application/zip",
}
MAX_FILE_SIZE = 25 * 1024 * 1024

router = APIRouter(tags=["collaboration"])
ADMIN = ("ADMIN", "SUPER_ADMIN", "HR")

async def member(db, conversation_id, user):
    row = await db.scalar(select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user.id))
    if not row and not (user.role and user.role.name in ADMIN):
        raise HTTPException(403, "Conversation access denied")
    return row

@router.post("/conversations", status_code=201)
async def create_conversation(data: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kind = data.get("kind", "direct")
    if kind not in {"direct", "team", "project", "meeting"}: raise HTTPException(422, "Invalid conversation type")
    row = Conversation(company_id=user.company_id, created_by_id=user.id, kind=kind, title=data.get("title"),
                       team_id=data.get("team_id"), project_id=data.get("project_id"), meeting_id=data.get("meeting_id"))
    db.add(row); await db.flush()
    ids = set(data.get("member_ids", [])) | {str(user.id)}
    for uid in ids: db.add(ConversationMember(conversation_id=row.id, user_id=uuid.UUID(str(uid))))
    await db.commit()
    return {"id": row.id, "kind": row.kind, "title": row.title}

@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return list(await db.scalars(select(Conversation).join(ConversationMember).where(
        Conversation.company_id == user.company_id, ConversationMember.user_id == user.id)))

@router.get("/conversations/{conversation_id}/messages")
async def list_messages(conversation_id: uuid.UUID, before: datetime | None = None,
                         limit: int = Query(50, ge=1, le=100), search: str | None = None,
                         db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await member(db, conversation_id, user)
    q = select(Message).where(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
    if before: q = q.where(Message.created_at < before)
    if search: q = q.where(Message.body.ilike(f"%{search}%"))
    return list((await db.scalars(q.order_by(Message.created_at.desc()).limit(limit))).all())

@router.post("/conversations/{conversation_id}/messages", status_code=201)
async def send_message(conversation_id: uuid.UUID, data: dict, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    await member(db, conversation_id, user)
    row = Message(conversation_id=conversation_id, sender_id=user.id, body=data.get("body", ""),
                  reply_to_id=data.get("reply_to_id"), mentions=json.dumps(data.get("mentions", [])))
    db.add(row); await db.commit(); await db.refresh(row)
    return row

@router.post("/messages/{message_id}/read")
async def read_message(message_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    message = await db.get(Message, message_id)
    if not message: raise HTTPException(404, "Message not found")
    await member(db, message.conversation_id, user)
    status = await db.scalar(select(MessageReadStatus).where(MessageReadStatus.message_id == message_id,
                                                              MessageReadStatus.user_id == user.id))
    if status: status.read_at = datetime.utcnow()
    else: db.add(MessageReadStatus(message_id=message_id, user_id=user.id))
    await db.commit(); return {"read": True}

@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_socket(websocket: WebSocket, conversation_id: uuid.UUID):
    token = websocket.query_params.get("access_token")
    authorization = websocket.headers.get("authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        await websocket.close(code=4401)
        return
    async with AsyncSessionLocal() as db:
        try:
            user = await authenticate_token(token, db)
            await member(db, conversation_id, user)
        except HTTPException:
            await websocket.close(code=4403)
            return
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            # Stateless transport; clients receive typing/read/reply/mention events.
            await websocket.send_json({"conversation_id": str(conversation_id), **payload})
    except WebSocketDisconnect:
        return

@router.post("/files", status_code=201)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_FILES:
        raise HTTPException(415, "Unsupported file type")
    filename = os.path.basename(file.filename or "upload")
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)[:255] or "upload"
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds the 25 MB limit")
    storage = S3Storage("worksphere")
    key = object_key(user.company_id, filename)
    from io import BytesIO
    stored = await storage.put(BytesIO(content), key=key, content_type=content_type)
    row = FileMetadata(company_id=user.company_id, uploaded_by_id=user.id, object_key=key,
                       filename=filename, content_type=stored.content_type, size=stored.size)
    db.add(row)
    await record_audit(db, user, "FILE_UPLOADED", "file", row.id, {"filename": filename})
    await db.commit(); await db.refresh(row)
    return {"id": row.id, "filename": row.filename, "size": row.size, "download_url": storage.download_url(key)}

@router.get("/files/{file_id}/download")
async def download_file(file_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = await db.scalar(select(FileMetadata).where(FileMetadata.id == file_id, FileMetadata.company_id == user.company_id))
    if not row: raise HTTPException(404, "File not found")
    return {"url": S3Storage("worksphere").download_url(row.object_key)}

@router.get("/notifications")
async def notifications(unread: bool = False, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Notification).where(Notification.user_id == user.id)
    if unread: q = q.where(Notification.read_at.is_(None))
    return list(await db.scalars(q.order_by(Notification.created_at.desc())))

@router.post("/notifications/{notification_id}/read")
async def read_notification(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = await db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not row: raise HTTPException(404, "Notification not found")
    row.read_at = datetime.utcnow(); await db.commit(); return {"read": True}

@router.post("/announcements", status_code=201, dependencies=[Depends(require_roles(*ADMIN))])
async def create_announcement(data: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = Announcement(company_id=user.company_id, author_id=user.id, **{k: v for k, v in data.items()
        if k in {"title", "body", "publish_at", "expires_at", "requires_ack"}})
    db.add(row); await db.commit(); await db.refresh(row); return row

@router.get("/announcements")
async def announcements(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    return list(await db.scalars(select(Announcement).where(Announcement.company_id == user.company_id,
        Announcement.publish_at <= now, or_(Announcement.expires_at.is_(None), Announcement.expires_at >= now))))

@router.post("/announcements/{announcement_id}/ack")
async def acknowledge(announcement_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = await db.scalar(select(Announcement).where(Announcement.id == announcement_id, Announcement.company_id == user.company_id))
    if not row: raise HTTPException(404, "Announcement not found")
    if not await db.scalar(select(AnnouncementAcknowledgement).where(
        AnnouncementAcknowledgement.announcement_id == announcement_id, AnnouncementAcknowledgement.user_id == user.id)):
        db.add(AnnouncementAcknowledgement(announcement_id=announcement_id, user_id=user.id)); await db.commit()
    return {"acknowledged": True}

@router.get("/knowledge/search")
async def knowledge_search(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db),
                           user: User = Depends(get_current_user)):
    docs = await db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.company_id == user.company_id,
        KnowledgeDocument.is_published.is_(True), or_(KnowledgeDocument.title.ilike(f"%{q}%"),
        KnowledgeDocument.description.ilike(f"%{q}%"))))
    return list(docs)

@router.get("/knowledge/{document_id}")
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    doc = await db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id,
                                                            KnowledgeDocument.company_id == user.company_id))
    if not doc: raise HTTPException(404, "Document not found")
    permitted = doc.owner_id == user.id or doc.is_published or bool(await db.scalar(select(DocumentPermission).where(
        DocumentPermission.document_id == document_id, DocumentPermission.user_id == user.id,
        DocumentPermission.can_read.is_(True))))
    if not permitted and not (user.role and user.role.name in ADMIN):
        raise HTTPException(403, "Document access denied")
    await record_audit(db, user, "DOCUMENT_ACCESSED", "knowledge_document", doc.id)
    await db.commit()
    return doc
