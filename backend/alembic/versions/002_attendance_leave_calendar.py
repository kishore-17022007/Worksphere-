"""attendance, leave and calendar

Revision ID: 002_attendance_leave_calendar
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_attendance_leave_calendar"
down_revision = "001_auth_organization"
branch_labels = None
depends_on = None

def upgrade():
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table("attendance",
        sa.Column("id", uuid, primary_key=True), sa.Column("user_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("attendance_date", sa.Date, nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("check_out", sa.DateTime(timezone=True)), sa.Column("working_duration", sa.Integer),
        sa.Column("metadata", sa.JSON), sa.Column("status", sa.String(20), nullable=False, server_default="PRESENT"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "attendance_date", name="uq_attendance_user_date"))
    op.create_table("leave_types", sa.Column("id", uuid, primary_key=True), sa.Column("company_id", uuid, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False), sa.Column("description", sa.Text), sa.Column("annual_days", sa.Integer, nullable=False, server_default="0"), sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()))
    op.create_table("leave_requests", sa.Column("id", uuid, primary_key=True), sa.Column("employee_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type_id", uuid, sa.ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False), sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False), sa.Column("reason", sa.Text), sa.Column("status", sa.String(30), nullable=False, server_default="pending_team_lead"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("leave_approvals", sa.Column("id", uuid, primary_key=True), sa.Column("request_id", uuid, sa.ForeignKey("leave_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(30), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False), sa.Column("comment", sa.Text), sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("calendar_events", sa.Column("id", uuid, primary_key=True), sa.Column("company_id", uuid, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_private", sa.Boolean, nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("holidays", sa.Column("id", uuid, primary_key=True), sa.Column("company_id", uuid, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("holiday_date", sa.Date, nullable=False))

def downgrade():
    for table in ("holidays", "calendar_events", "leave_approvals", "leave_requests", "leave_types", "attendance"):
        op.drop_table(table)
