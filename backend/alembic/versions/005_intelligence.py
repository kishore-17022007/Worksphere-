"""daily plans, activity timeline and workload intelligence"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "005_intelligence"
down_revision = "004_collaboration"
branch_labels = None
depends_on = None
U = postgresql.UUID(as_uuid=True)
def fk(name, ondelete="CASCADE"): return sa.ForeignKey(name, ondelete=ondelete)
def upgrade():
    op.add_column("tasks", sa.Column("estimated_minutes", sa.Integer, server_default="60", nullable=False))
    op.create_table("daily_plans", sa.Column("id", U, primary_key=True), sa.Column("user_id", U, fk("users.id"), nullable=False),
      sa.Column("plan_date", sa.Date, nullable=False), sa.Column("available_minutes", sa.Integer, server_default="480"),
      sa.Column("generated", sa.Boolean, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_daily_plans_user_date", "daily_plans", ["user_id", "plan_date"], unique=True)
    op.create_table("daily_plan_items", sa.Column("id", U, primary_key=True), sa.Column("plan_id", U, fk("daily_plans.id"), nullable=False),
      sa.Column("task_id", U, fk("tasks.id","SET NULL")), sa.Column("meeting_id", U, fk("meetings.id","SET NULL")), sa.Column("title", sa.String(300), nullable=False),
      sa.Column("item_type", sa.String(20), server_default="task"), sa.Column("position", sa.Integer, server_default="0"), sa.Column("start_minute", sa.Integer),
      sa.Column("duration_minutes", sa.Integer, server_default="30"), sa.Column("rationale", sa.Text), sa.Column("is_manual", sa.Boolean, server_default=sa.false()))
    op.create_table("activity_events", sa.Column("id", U, primary_key=True), sa.Column("company_id", U, fk("companies.id"), nullable=False),
      sa.Column("actor_id", U, fk("users.id"), nullable=False), sa.Column("event_type", sa.String(60), nullable=False), sa.Column("entity_type", sa.String(40), nullable=False),
      sa.Column("entity_id", U), sa.Column("payload", sa.JSON), sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_activity_events_company_occurred", "activity_events", ["company_id", "occurred_at"])
def downgrade():
    op.drop_table("activity_events"); op.drop_table("daily_plan_items"); op.drop_index("ix_daily_plans_user_date", table_name="daily_plans"); op.drop_table("daily_plans")
    op.drop_column("tasks", "estimated_minutes")
