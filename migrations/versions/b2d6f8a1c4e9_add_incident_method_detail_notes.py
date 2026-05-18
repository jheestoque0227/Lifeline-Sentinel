"""add incident method detail notes

Revision ID: b2d6f8a1c4e9
Revises: a7c9f2d4e8b1
Create Date: 2026-05-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2d6f8a1c4e9"
down_revision = "a7c9f2d4e8b1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("incident_details", schema=None) as batch_op:
        batch_op.add_column(sa.Column("self_poisoning_method_details", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("self_harm_method_details", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("incident_details", schema=None) as batch_op:
        batch_op.drop_column("self_harm_method_details")
        batch_op.drop_column("self_poisoning_method_details")
