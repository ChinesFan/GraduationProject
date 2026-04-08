"""add task progress fields

Revision ID: 1c950302d66f
Revises: b06e2b4e31c4
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1c950302d66f"
down_revision = "b06e2b4e31c4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tasks",
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tasks",
        sa.Column("current_stage", sa.String(length=64), nullable=False, server_default="pending"),
    )
    op.add_column(
        "tasks",
        sa.Column("stage_message", sa.String(length=255), nullable=True),
    )

    # 去掉 server_default，避免以后数据库层默认值和模型不一致
    op.alter_column("tasks", "progress", server_default=None)
    op.alter_column("tasks", "current_stage", server_default=None)


def downgrade():
    op.drop_column("tasks", "stage_message")
    op.drop_column("tasks", "current_stage")
    op.drop_column("tasks", "progress")