"""authentication and organization hierarchy

Revision ID: 001_auth_organization
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_auth_organization"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table("companies", sa.Column("id", uuid, primary_key=True), sa.Column("name", sa.String(200), nullable=False, unique=True), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_table("departments", sa.Column("id", uuid, primary_key=True), sa.Column("company_id", uuid, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(200), nullable=False))
    op.create_table("teams", sa.Column("id", uuid, primary_key=True), sa.Column("department_id", uuid, sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(200), nullable=False))
    op.create_table("permissions", sa.Column("id", uuid, primary_key=True), sa.Column("name", sa.String(100), unique=True, nullable=False))
    op.create_table("roles", sa.Column("id", uuid, primary_key=True), sa.Column("name", sa.String(50), unique=True, nullable=False))
    op.create_table("role_permissions", sa.Column("role_id", uuid, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True), sa.Column("permission_id", uuid, sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("users", sa.Column("id", uuid, primary_key=True), sa.Column("company_id", uuid, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("department_id", uuid, sa.ForeignKey("departments.id", ondelete="SET NULL")), sa.Column("team_id", uuid, sa.ForeignKey("teams.id", ondelete="SET NULL")), sa.Column("reporting_manager_id", uuid, sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("email", sa.String(320), unique=True, nullable=False), sa.Column("full_name", sa.String(200), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role_id", uuid, sa.ForeignKey("roles.id", ondelete="SET NULL")), sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_table("team_members", sa.Column("id", uuid, primary_key=True), sa.Column("team_id", uuid, sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("is_lead", sa.Boolean, nullable=False, server_default=sa.false()), sa.UniqueConstraint("team_id", "user_id"))

def downgrade():
    for table in ("team_members", "users", "role_permissions", "roles", "permissions", "teams", "departments", "companies"):
        op.drop_table(table)
