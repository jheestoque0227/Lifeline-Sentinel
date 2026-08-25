"""add hospital reference crud fields

Revision ID: 9d4e2f7a6c15
Revises: f3a9c2d7e6b1
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9d4e2f7a6c15"
down_revision = "f3a9c2d7e6b1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("hospitals", schema=None) as batch_op:
        batch_op.add_column(sa.Column("deleted_remarks", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("hospital_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_users_hospital_id_hospitals", "hospitals", ["hospital_id"], ["id"])


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("fk_users_hospital_id_hospitals", type_="foreignkey")
        batch_op.drop_column("hospital_id")

    with op.batch_alter_table("hospitals", schema=None) as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("deleted_remarks")
