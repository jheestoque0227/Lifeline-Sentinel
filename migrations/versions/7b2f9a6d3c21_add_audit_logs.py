"""Add audit logs

Revision ID: 7b2f9a6d3c21
Revises: 184b7db038dc
Create Date: 2026-05-16 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7b2f9a6d3c21"
down_revision = "184b7db038dc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("event", sa.String(length=100), nullable=False),
        sa.Column("module", sa.String(length=100), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("audit_logs")
