"""Create initial admin from environment

Revision ID: c4d8e2b91f5a
Revises: 7b2f9a6d3c21
Create Date: 2026-05-16 17:30:00.000000

"""
from datetime import datetime

from alembic import op
from flask import current_app
import sqlalchemy as sa
from werkzeug.security import generate_password_hash


revision = "c4d8e2b91f5a"
down_revision = "7b2f9a6d3c21"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    existing_admin = bind.execute(sa.text("SELECT id FROM users WHERE role = :role LIMIT 1"), {"role": "Admin"}).first()
    if existing_admin:
        return

    admin = _initial_admin_config()
    now = datetime.utcnow()
    bind.execute(
        sa.text(
            """
            INSERT INTO users (
                employee_no, full_name, email, username, password_hash, role,
                is_active_user, last_login_at, created_at, updated_at, deactivated_at
            )
            VALUES (
                :employee_no, :full_name, :email, :username, :password_hash, :role,
                :is_active_user, :last_login_at, :created_at, :updated_at, :deactivated_at
            )
            """
        ),
        {
            "employee_no": admin["employee_no"],
            "full_name": admin["full_name"],
            "email": admin["email"],
            "username": admin["username"],
            "password_hash": generate_password_hash(admin["password"]),
            "role": "Admin",
            "is_active_user": True,
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
            "deactivated_at": None,
        },
    )


def downgrade():
    username = current_app.config.get("INITIAL_ADMIN_USERNAME")
    if username:
        op.get_bind().execute(
            sa.text("DELETE FROM users WHERE username = :username AND role = :role"),
            {"username": username, "role": "Admin"},
        )


def _initial_admin_config():
    required = {
        "employee_no": "INITIAL_ADMIN_EMPLOYEE_NO",
        "full_name": "INITIAL_ADMIN_FULL_NAME",
        "email": "INITIAL_ADMIN_EMAIL",
        "username": "INITIAL_ADMIN_USERNAME",
        "password": "INITIAL_ADMIN_PASSWORD",
    }
    values = {key: current_app.config.get(env_name) for key, env_name in required.items()}
    missing = [env_name for key, env_name in required.items() if not values[key]]
    if missing:
        raise RuntimeError(
            "Missing initial Admin environment variables required by migration: "
            + ", ".join(missing)
        )
    return values
