import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import (
    ActionItemSuggestion, CalendarEvent, Meeting, MeetingParticipant, MOM, Project,
    ProjectMember, Task, TaskComment, TaskHistory, User,
)
from app.models.workflow import SuggestionStatus, TaskStatus
from app.schemas import (
    CommentCreate, MeetingCreate, MOMCreate, ProjectCreate, ProjectMemberCreate,
    ProjectRead, SuggestionCreate, TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate,
)

router = APIRouter(prefix="/work", tags=["projects and workflows"])
ADMIN_ROLES = {"ADMIN", "SUPER_ADMIN", "HR"}

def is_admin(user: User) -> bool:
    return bool(user.role and user.role.name in ADMIN_ROLES)

async def project_or_404(db, project_id, user):
    project = await db.scalar(select(Project).where(Project.id == project_id, Project.company_id == user.company_id))
    if not project:
        raise HTTPException(404, "Project not found")
    member = await db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id))
    if not (is_admin(user) or project.owner_id == user.id or member):
        raise HTTPException(403, "Project access denied")
    return project, member

async def can_manage_project(db, project, user):
    member = await db.scalar(select(ProjectMember).where(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id))
    if not (is_admin(user) or project.owner_id == user.id or (member and member.is_lead)):
        raise HTTPException(403, "Project management permission required")

@router.post("/projects", response_model=ProjectRead, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = Project(company_id=user.company_id, owner_id=user.id, **data.model_dump())
    db.add(row)
    await db.flush()
    db.add(ProjectMember(project_id=row.id, user_id=user.id, is_lead=True))
    await db.commit(); await db.refresh(row)
    return row

@router.get("/projects", response_model=list[ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if is_admin(user):
        return list(await db.scalars(select(Project).where(Project.company_id == user.company_id)))
    return list(await db.scalars(select(Project).join(ProjectMember, ProjectMember.project_id == Project.id).where(
        Project.company_id == user.company_id, (Project.owner_id == user.id) | (ProjectMember.user_id == user.id))))

@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    project, _ = await project_or_404(db, project_id, user)
    return project

@router.get("/tasks", response_model=list[TaskRead])
async def list_my_tasks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return list(await db.scalars(select(Task).join(Project, Task.project_id == Project.id).where(
        Project.company_id == user.company_id,
        (Task.assignee_id == user.id) | (Task.creator_id == user.id)
    ).order_by(Task.kanban_order, Task.created_at)))

@router.get("/meetings")
async def list_meetings(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return list(await db.scalars(select(Meeting).where(Meeting.company_id == user.company_id).order_by(Meeting.starts_at)))

@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await meeting_access(db, meeting_id, user)

@router.post("/projects/{project_id}/members", status_code=201)
async def add_member(project_id: uuid.UUID, data: ProjectMemberCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    project, _ = await project_or_404(db, project_id, user); await can_manage_project(db, project, user)
    target = await db.scalar(select(User).where(User.id == data.user_id, User.company_id == user.company_id))
    if not target: raise HTTPException(404, "User not found")
    existing = await db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == data.user_id))
    if existing: raise HTTPException(409, "Already a member")
    row = ProjectMember(project_id=project_id, **data.model_dump()); db.add(row); await db.commit(); return row

@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=201)
async def create_task(project_id: uuid.UUID, data: TaskCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    project, member = await project_or_404(db, project_id, user)
    if not (is_admin(user) or project.owner_id == user.id or (member and member.is_lead)):
        raise HTTPException(403, "Only project leads can create tasks")
    if data.assignee_id:
        assigned = await db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == data.assignee_id))
        if not assigned: raise HTTPException(400, "Assignee must be a project member")
    row = Task(project_id=project_id, creator_id=user.id, **data.model_dump()); db.add(row); await db.commit(); await db.refresh(row); return row

@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def list_tasks(project_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await project_or_404(db, project_id, user)
    return list(await db.scalars(select(Task).where(Task.project_id == project_id).order_by(Task.kanban_order, Task.created_at)))

@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: uuid.UUID, data: TaskUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    task = await db.scalar(select(Task).join(Project, Task.project_id == Project.id).where(Task.id == task_id, Project.company_id == user.company_id))
    if not task: raise HTTPException(404, "Task not found")
    project, member = await project_or_404(db, task.project_id, user)
    if not (is_admin(user) or project.owner_id == user.id or task.creator_id == user.id or task.assignee_id == user.id or (member and member.is_lead)):
        raise HTTPException(403, "Task access denied")
    if data.assignee_id:
        if not await db.scalar(select(ProjectMember).where(ProjectMember.project_id == task.project_id, ProjectMember.user_id == data.assignee_id)):
            raise HTTPException(400, "Assignee must be a project member")
    for key, value in data.model_dump(exclude_unset=True).items(): setattr(task, key, value)
    await db.commit(); await db.refresh(task); return task

@router.post("/tasks/{task_id}/status", response_model=TaskRead)
async def transition_task(task_id: uuid.UUID, data: TaskStatusUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    task = await db.scalar(select(Task).join(Project, Task.project_id == Project.id).where(Task.id == task_id, Project.company_id == user.company_id))
    if not task: raise HTTPException(404, "Task not found")
    project, member = await project_or_404(db, task.project_id, user)
    if not (is_admin(user) or task.assignee_id == user.id or task.creator_id == user.id or project.owner_id == user.id or (member and member.is_lead)):
        raise HTTPException(403, "Task transition denied")
    allowed = {s.value for s in TaskStatus}
    if data.status not in allowed: raise HTTPException(422, "Invalid task status")
    transitions = {
        "BACKLOG": {"TODO"},
        "TODO": {"IN_PROGRESS", "BLOCKED"},
        "IN_PROGRESS": {"TODO", "IN_REVIEW", "BLOCKED"},
        "IN_REVIEW": {"IN_PROGRESS", "COMPLETED", "BLOCKED"},
        "BLOCKED": {"TODO", "IN_PROGRESS"},
        "COMPLETED": {"IN_PROGRESS"},
    }
    if data.status != task.status and data.status not in transitions.get(task.status, set()):
        raise HTTPException(409, f"Cannot transition from {task.status} to {data.status}")
    old = task.status; task.status = data.status
    db.add(TaskHistory(task_id=task.id, actor_id=user.id, from_status=old, to_status=data.status, note=data.note))
    await db.commit(); await db.refresh(task); return task

@router.post("/tasks/{task_id}/comments", status_code=201)
async def comment(task_id: uuid.UUID, data: CommentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task: raise HTTPException(404, "Task not found")
    await project_or_404(db, task.project_id, user)
    row = TaskComment(task_id=task_id, author_id=user.id, body=data.body); db.add(row); await db.commit(); await db.refresh(row); return row

@router.post("/meetings", status_code=201)
async def create_meeting(data: MeetingCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if data.ends_at <= data.starts_at: raise HTTPException(422, "ends_at must be after starts_at")
    if data.project_id:
        project, _ = await project_or_404(db, data.project_id, user)
    else:
        project = None
    event = CalendarEvent(company_id=user.company_id, owner_id=user.id, title=data.title, description=data.agenda, starts_at=data.starts_at, ends_at=data.ends_at)
    db.add(event); await db.flush()
    meeting = Meeting(company_id=user.company_id, organizer_id=user.id, project_id=project.id if project else None, calendar_event_id=event.id, title=data.title, agenda=data.agenda, starts_at=data.starts_at, ends_at=data.ends_at)
    db.add(meeting); await db.flush()
    ids = set(data.participant_ids) | {user.id}
    valid = list(await db.scalars(select(User.id).where(User.company_id == user.company_id, User.id.in_(ids))))
    if len(valid) != len(ids): raise HTTPException(400, "All participants must belong to the company")
    for uid in valid: db.add(MeetingParticipant(meeting_id=meeting.id, user_id=uid, can_edit=uid == user.id))
    await db.commit(); await db.refresh(meeting); return meeting

async def meeting_access(db, meeting_id, user, edit=False):
    meeting = await db.scalar(select(Meeting).where(Meeting.id == meeting_id, Meeting.company_id == user.company_id))
    if not meeting: raise HTTPException(404, "Meeting not found")
    participant = await db.scalar(select(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == user.id))
    if not (is_admin(user) or meeting.organizer_id == user.id or (participant and (not edit or participant.can_edit))):
        raise HTTPException(403, "Meeting access denied")
    return meeting

@router.post("/meetings/{meeting_id}/mom", status_code=201)
async def create_mom(meeting_id: uuid.UUID, data: MOMCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    meeting = await meeting_access(db, meeting_id, user)
    existing = await db.scalar(select(MOM).where(MOM.meeting_id == meeting_id))
    if existing: raise HTTPException(409, "MOM already exists")
    row = MOM(meeting_id=meeting_id, author_id=user.id, notes=data.notes); db.add(row); await db.commit(); await db.refresh(row); return row

@router.post("/meetings/{meeting_id}/suggestions", status_code=201)
async def suggest_action(meeting_id: uuid.UUID, data: SuggestionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await meeting_access(db, meeting_id, user)
    row = ActionItemSuggestion(meeting_id=meeting_id, suggested_by_id=user.id, **data.model_dump()); db.add(row); await db.commit(); await db.refresh(row); return row

@router.post("/suggestions/{suggestion_id}/approve", response_model=TaskRead)
async def approve_suggestion(suggestion_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    suggestion = await db.scalar(select(ActionItemSuggestion).join(Meeting, ActionItemSuggestion.meeting_id == Meeting.id).where(ActionItemSuggestion.id == suggestion_id, Meeting.company_id == user.company_id))
    if not suggestion: raise HTTPException(404, "Suggestion not found")
    meeting = await meeting_access(db, suggestion.meeting_id, user, edit=True)
    if suggestion.status != SuggestionStatus.PENDING.value: raise HTTPException(409, "Suggestion already decided")
    suggestion.status = SuggestionStatus.APPROVED.value
    project = await db.scalar(select(Project).where(Project.id == meeting.project_id, Project.company_id == user.company_id)) if meeting.project_id else await db.scalar(select(Project).where(Project.owner_id == meeting.organizer_id, Project.company_id == user.company_id))
    if not project: raise HTTPException(400, "Meeting organizer has no project")
    assignee = suggestion.assignee_id or meeting.organizer_id
    if not await db.scalar(select(ProjectMember).where(ProjectMember.project_id == project.id, ProjectMember.user_id == assignee)):
        db.add(ProjectMember(project_id=project.id, user_id=assignee))
    task = Task(project_id=project.id, creator_id=user.id, assignee_id=assignee, title=suggestion.title, description=suggestion.description)
    db.add(task); await db.flush(); suggestion.approved_task_id = task.id
    db.add(TaskHistory(task_id=task.id, actor_id=user.id, from_status=None, to_status=task.status, note="Created from approved action item"))
    await db.commit(); await db.refresh(task); return task
