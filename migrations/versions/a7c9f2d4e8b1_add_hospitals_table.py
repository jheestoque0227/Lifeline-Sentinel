"""add hospitals table

Revision ID: a7c9f2d4e8b1
Revises: 4c31ffb063fd
Create Date: 2026-05-18 00:00:00.000000

"""
from datetime import datetime

from alembic import op
from flask import current_app
import sqlalchemy as sa


revision = "a7c9f2d4e8b1"
down_revision = "4c31ffb063fd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hospitals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hospital_code", sa.String(length=50), nullable=False),
        sa.Column("hospital_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hospital_code"),
    )

    hospital = _initial_hospital_config()
    now = datetime.utcnow()
    op.get_bind().execute(
        sa.text(
            """
            INSERT INTO hospitals (hospital_code, hospital_name, created_at, updated_at)
            VALUES (:hospital_code, :hospital_name, :created_at, :updated_at)
            """
        ),
        {
            "hospital_code": hospital["hospital_code"],
            "hospital_name": hospital["hospital_name"],
            "created_at": now,
            "updated_at": now,
        },
    )


def downgrade():
    op.drop_table("hospitals")


def _initial_hospital_config():
    required = {
        "hospital_code": "INITIAL_HOSPITAL_CODE",
        "hospital_name": "INITIAL_HOSPITAL_NAME",
    }
    values = {key: current_app.config.get(env_name) for key, env_name in required.items()}
    missing = [env_name for key, env_name in required.items() if not values[key]]
    if missing:
        raise RuntimeError(
            "Missing initial Hospital environment variables required by migration: "
            + ", ".join(missing)
        )
    return values
