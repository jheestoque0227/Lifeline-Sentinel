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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    registry_columns = {column["name"] for column in inspector.get_columns("registries")}
    if "risk_level" in registry_columns:
        with op.batch_alter_table("registries", schema=None) as batch_op:
            batch_op.drop_column("risk_level")


def downgrade():
    # risk_level belongs to ML analytics outputs and must not be restored
    # as a persisted registry field.
    pass
