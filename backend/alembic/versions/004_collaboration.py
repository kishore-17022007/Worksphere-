"""workplace collaboration, files, notifications and knowledge
Revision ID: 004_collaboration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_collaboration"
down_revision = "003_project_task_meeting_workflows"
branch_labels = None
depends_on = None
U = postgresql.UUID(as_uuid=True)
def idcol(): return sa.Column("id", U, primary_key=True)
def fk(table, ondelete="CASCADE"): return sa.ForeignKey(table, ondelete=ondelete)

def upgrade():
    op.create_table("file_metadata", idcol(), sa.Column("company_id", U, fk("companies.id"), nullable=False),
      sa.Column("uploaded_by_id", U, fk("users.id","RESTRICT"), nullable=False), sa.Column("object_key",sa.String(500),unique=True,nullable=False),
      sa.Column("filename",sa.String(255),nullable=False), sa.Column("content_type",sa.String(200),nullable=False), sa.Column("size",sa.Integer,nullable=False),
      sa.Column("checksum",sa.String(128)), sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table("conversations", idcol(), sa.Column("company_id",U,fk("companies.id"),nullable=False), sa.Column("kind",sa.String(20),server_default="direct",nullable=False),
      sa.Column("title",sa.String(200)), sa.Column("team_id",U,fk("teams.id")), sa.Column("project_id",U,fk("projects.id")), sa.Column("meeting_id",U,fk("meetings.id")),
      sa.Column("created_by_id",U,fk("users.id","RESTRICT"),nullable=False), sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table("conversation_members",idcol(),sa.Column("conversation_id",U,fk("conversations.id"),nullable=False),sa.Column("user_id",U,fk("users.id"),nullable=False),
      sa.Column("role",sa.String(20),server_default="member",nullable=False),sa.Column("joined_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("conversation_id","user_id"))
    op.create_table("messages",idcol(),sa.Column("conversation_id",U,fk("conversations.id"),nullable=False),sa.Column("sender_id",U,fk("users.id"),nullable=False),
      sa.Column("body",sa.Text,nullable=False),sa.Column("reply_to_id",U,fk("messages.id","SET NULL")),sa.Column("mentions",sa.Text),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("edited_at",sa.DateTime(timezone=True)),sa.Column("deleted_at",sa.DateTime(timezone=True)))
    op.create_table("message_attachments",idcol(),sa.Column("message_id",U,fk("messages.id"),nullable=False),sa.Column("file_id",U,fk("file_metadata.id"),nullable=False))
    op.create_table("message_read_status",idcol(),sa.Column("message_id",U,fk("messages.id"),nullable=False),sa.Column("user_id",U,fk("users.id"),nullable=False),sa.Column("read_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("message_id","user_id"))
    op.create_table("notification_preferences",idcol(),sa.Column("user_id",U,fk("users.id"),nullable=False),sa.Column("event_type",sa.String(80),nullable=False),sa.Column("enabled",sa.Boolean,server_default=sa.true()),sa.Column("channel",sa.String(20),server_default="in_app"),sa.UniqueConstraint("user_id","event_type"))
    op.create_table("notifications",idcol(),sa.Column("user_id",U,fk("users.id"),nullable=False),sa.Column("event_type",sa.String(80),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("body",sa.Text,nullable=False),sa.Column("payload",sa.Text),sa.Column("read_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table("announcements",idcol(),sa.Column("company_id",U,fk("companies.id"),nullable=False),sa.Column("author_id",U,fk("users.id","RESTRICT"),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("body",sa.Text,nullable=False),sa.Column("publish_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.Column("expires_at",sa.DateTime(timezone=True)),sa.Column("requires_ack",sa.Boolean,server_default=sa.false()))
    op.create_table("announcement_acknowledgements",idcol(),sa.Column("announcement_id",U,fk("announcements.id"),nullable=False),sa.Column("user_id",U,fk("users.id"),nullable=False),sa.Column("acknowledged_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("announcement_id","user_id"))
    op.create_table("knowledge_categories",idcol(),sa.Column("company_id",U,fk("companies.id"),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("description",sa.Text))
    op.create_table("knowledge_documents",idcol(),sa.Column("company_id",U,fk("companies.id"),nullable=False),sa.Column("category_id",U,fk("knowledge_categories.id","SET NULL")),sa.Column("owner_id",U,fk("users.id","RESTRICT"),nullable=False),sa.Column("title",sa.String(250),nullable=False),sa.Column("description",sa.Text),sa.Column("is_published",sa.Boolean,server_default=sa.false()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table("document_versions",idcol(),sa.Column("document_id",U,fk("knowledge_documents.id"),nullable=False),sa.Column("version",sa.Integer,nullable=False),sa.Column("file_id",U,fk("file_metadata.id","SET NULL")),sa.Column("content",sa.Text),sa.Column("created_by_id",U,fk("users.id","RESTRICT"),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("document_id","version"))
    op.create_table("document_permissions",idcol(),sa.Column("document_id",U,fk("knowledge_documents.id"),nullable=False),sa.Column("user_id",U,fk("users.id"),nullable=False),sa.Column("can_read",sa.Boolean,server_default=sa.true()),sa.Column("can_edit",sa.Boolean,server_default=sa.false()),sa.UniqueConstraint("document_id","user_id"))

def downgrade():
    for name in ("document_permissions","document_versions","knowledge_documents","knowledge_categories","announcement_acknowledgements","announcements","notifications","notification_preferences","message_read_status","message_attachments","messages","conversation_members","conversations","file_metadata"):
        op.drop_table(name)
