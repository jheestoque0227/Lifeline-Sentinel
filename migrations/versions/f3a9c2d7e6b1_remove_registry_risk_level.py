"""remove registry risk level

Revision ID: f3a9c2d7e6b1
Revises: e7b9c1d4a6f2
Create Date: 2026-05-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f3a9c2d7e6b1"
down_revision = "e7b9c1d4a6f2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("registries", schema=None) as batch_op:
        batch_op.drop_column("risk_level")


def downgrade():
    with op.batch_alter_table("registries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("risk_level", sa.Enum("Low", "Moderate", "High"), nullable=True))
