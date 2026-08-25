"""remove deleted by columns

Revision ID: b7e9d4c2a1f6
Revises: ac5b8d2e4f10
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7e9d4c2a1f6"
down_revision = "ac5b8d2e4f10"
branch_labels = None
depends_on = None


def upgrade():
    _drop_deleted_by("registries", None)
    _drop_deleted_by("hospitals", "fk_hospitals_deleted_by_users")
    _drop_deleted_by("users", "fk_users_deleted_by_users")


def downgrade():
    # Actor attribution for deletions belongs in audit_logs, not entity tables.
    pass


def _drop_deleted_by(table_name, named_constraint):
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "deleted_by" not in columns:
        return

    foreign_keys = inspector.get_foreign_keys(table_name)
    constraint_names = [
        key["name"]
        for key in foreign_keys
        if "deleted_by" in key.get("constrained_columns", []) and key.get("name")
    ]
    if named_constraint and named_constraint not in constraint_names:
        constraint_names.append(named_constraint)

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        for constraint_name in constraint_names:
            batch_op.drop_constraint(constraint_name, type_="foreignkey")
        batch_op.drop_column("deleted_by")
