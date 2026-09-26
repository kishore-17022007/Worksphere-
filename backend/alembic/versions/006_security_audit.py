"""security audit log and indexes"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_security_audit"
down_revision = "005_intelligence"
branch_labels = None
depends_on = None
U = postgresql.UUID(as_uuid=True)

def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", U, primary_key=True),
        sa.Column("company_id", U, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", U, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", U),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_company_created", "audit_logs", ["company_id", "created_at"])
    op.create_index("ix_audit_logs_actor_action", "audit_logs", ["actor_id", "action"])
    indexes = (
        ("ix_users_company_active", "users", ["company_id", "is_active"]),
        ("ix_attendance_employee_date", "attendance", ["employee_id", "attendance_date"]),
        ("ix_leave_requests_employee_status", "leave_requests", ["employee_id", "status"]),
        ("ix_tasks_project_status_due", "tasks", ["project_id", "status", "due_at"]),
        ("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"]),
        ("ix_notifications_user_read_created", "notifications", ["user_id", "read_at", "created_at"]),
        ("ix_calendar_events_company_start", "calendar_events", ["company_id", "starts_at"]),
    )
    for name, table, columns in indexes:
        op.create_index(name, table, columns)

def downgrade():
    for name, table in (
        ("ix_calendar_events_company_start", "calendar_events"),
        ("ix_notifications_user_read_created", "notifications"),
        ("ix_messages_conversation_created", "messages"),
        ("ix_tasks_project_status_due", "tasks"),
        ("ix_leave_requests_employee_status", "leave_requests"),
        ("ix_attendance_employee_date", "attendance"),
        ("ix_users_company_active", "users"),
    ):
        op.drop_index(name, table_name=table)
    op.drop_index("ix_audit_logs_actor_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_company_created", table_name="audit_logs")
    op.drop_table("audit_logs")
