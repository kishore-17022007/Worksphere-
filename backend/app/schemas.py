import uuid
from datetime import date as DateType, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserRead"
class RefreshRequest(BaseModel):
    refresh_token: str
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    company_id: uuid.UUID
    department_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    reporting_manager_id: uuid.UUID | None = None
class UserUpdate(BaseModel):
    full_name: str | None = None
    department_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    reporting_manager_id: uuid.UUID | None = None
    is_active: bool | None = None
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    company_id: uuid.UUID
    department_id: uuid.UUID | None
    role_id: uuid.UUID | None
    team_id: uuid.UUID | None
    reporting_manager_id: uuid.UUID | None
    is_active: bool
    role: str | None = None
class CompanyCreate(BaseModel):
    name: str
class DepartmentCreate(BaseModel):
    name: str
    company_id: uuid.UUID
class TeamCreate(BaseModel):
    name: str
    department_id: uuid.UUID
class TeamMemberCreate(BaseModel):
    user_id: uuid.UUID
    is_lead: bool = False

class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    employee_id: uuid.UUID | None = None
    attendance_date: DateType
    check_in: datetime
    check_out: datetime | None
    working_duration: int | None = None
    status: str

class LeaveTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    annual_days: int = Field(ge=0)

class LeaveTypeRead(LeaveTypeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    is_active: bool

class LeaveRequestCreate(BaseModel):
    leave_type_id: uuid.UUID
    start_date: DateType
    end_date: DateType
    reason: str | None = None

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self

class LeaveDecision(BaseModel):
    comment: str | None = None

class LeaveRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type_id: uuid.UUID
    start_date: DateType
    end_date: DateType
    reason: str | None
    status: str
    created_at: datetime

class CalendarEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime
    is_private: bool = False

    @model_validator(mode="after")
    def valid_range(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self

class HolidayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    holiday_date: DateType

class CalendarItem(BaseModel):
    kind: str
    id: uuid.UUID | None = None
    title: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    date: Optional[DateType] = None
    owner_id: uuid.UUID | None = None

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    team_id: uuid.UUID | None = None
    priority: str = "MEDIUM"
    start_date: DateType | None = None
    target_date: DateType | None = None
class ProjectRead(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    created_at: datetime
class ProjectMemberCreate(BaseModel):
    user_id: uuid.UUID
    is_lead: bool = False
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    priority: str = "MEDIUM"
    due_at: datetime | None = None
    kanban_order: int = 0
    estimated_minutes: int = Field(default=60, ge=1)
class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    priority: str | None = None
    due_at: datetime | None = None
    kanban_order: int | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)
class TaskStatusUpdate(BaseModel):
    status: str
    note: str | None = None
class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    creator_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    progress: int = 0
class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
class MeetingCreate(BaseModel):
    project_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=200)
    agenda: str | None = None
    starts_at: datetime
    ends_at: datetime
    participant_ids: list[uuid.UUID] = []
class MOMCreate(BaseModel):
    notes: str = Field(min_length=1)
class SuggestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    assignee_id: uuid.UUID | None = None

class DailyPlanItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    item_type: str = "task"
    task_id: uuid.UUID | None = None
    meeting_id: uuid.UUID | None = None
    duration_minutes: int = Field(default=30, ge=1)
    position: int = Field(default=0, ge=0)
class DailyPlanItemUpdate(BaseModel):
    title: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    position: int | None = Field(default=None, ge=0)
class DailyPlanItemRead(DailyPlanItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    plan_id: uuid.UUID
    rationale: str | None = None
    is_manual: bool
class ActivityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    actor_id: uuid.UUID
    event_type: str
    entity_type: str
    entity_id: uuid.UUID | None
    payload: dict | None
    occurred_at: datetime
class ActivityEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=60)
    entity_type: str = Field(min_length=1, max_length=40)
    entity_id: uuid.UUID | None = None
    payload: dict | None = None
