"""add user session tracking

Revision ID: e8f4a1c2d9b7
Revises: c4d8e2b91f5a
Create Date: 2026-05-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e8f4a1c2d9b7"
down_revision = "c4d8e2b91f5a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("active_session_id", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("active_session_started_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("active_session_last_seen_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("users", "active_session_last_seen_at")
    op.drop_column("users", "active_session_started_at")
    op.drop_column("users", "active_session_id")
