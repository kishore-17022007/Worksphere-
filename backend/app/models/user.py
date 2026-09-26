import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    reporting_manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    role: Mapped["Role"] = relationship(back_populates="users")
    memberships: Mapped[list["TeamMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reporting_manager: Mapped["User | None"] = relationship(remote_side=[id], foreign_keys=[reporting_manager_id])


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    team: Mapped["Team"] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")
