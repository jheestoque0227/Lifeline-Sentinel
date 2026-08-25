"""add user soft delete fields

Revision ID: ac5b8d2e4f10
Revises: 9d4e2f7a6c15
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "ac5b8d2e4f10"
down_revision = "9d4e2f7a6c15"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("deleted_remarks", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("deleted_remarks")
