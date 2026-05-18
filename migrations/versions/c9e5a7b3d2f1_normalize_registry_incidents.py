"""normalize registry incidents

Revision ID: c9e5a7b3d2f1
Revises: b2d6f8a1c4e9
Create Date: 2026-05-18 00:00:00.000000

"""
import json
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "c9e5a7b3d2f1"
down_revision = "b2d6f8a1c4e9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("registries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_first_incident", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("has_past_2_month_incident", sa.Boolean(), nullable=True))

    op.create_table(
        "registry_incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registry_id", sa.Integer(), nullable=False),
        sa.Column("incident_date", sa.Date(), nullable=True),
        sa.Column("incident_day", sa.String(length=20), nullable=True),
        sa.Column("incident_time_range", sa.String(length=50), nullable=True),
        sa.Column("incident_place", sa.String(length=150), nullable=True),
        sa.Column("incident_place_other", sa.String(length=150), nullable=True),
        sa.Column("incident_region", sa.String(length=100), nullable=True),
        sa.Column("province_or_city", sa.String(length=100), nullable=True),
        sa.Column("municipality", sa.String(length=100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["registry_id"], ["registries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "registry_incident_methods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("icd10_code", sa.String(length=10), nullable=False),
        sa.Column("method_category", sa.String(length=50), nullable=False),
        sa.Column("method_description", sa.String(length=255), nullable=False),
        sa.Column("specify_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["registry_incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    _migrate_old_incidents()
    op.drop_table("incident_details")


def downgrade():
    op.create_table(
        "incident_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registry_id", sa.Integer(), nullable=False),
        sa.Column("is_first_incident", sa.Boolean(), nullable=False),
        sa.Column("has_past_2_month_incident", sa.Boolean(), nullable=True),
        sa.Column("incident_date", sa.Date(), nullable=True),
        sa.Column("incident_day", sa.String(length=20), nullable=True),
        sa.Column("incident_time_period", sa.String(length=50), nullable=True),
        sa.Column("incident_place", sa.String(length=150), nullable=True),
        sa.Column("incident_place_other", sa.String(length=150), nullable=True),
        sa.Column("incident_region", sa.String(length=100), nullable=True),
        sa.Column("incident_province_city", sa.String(length=100), nullable=True),
        sa.Column("incident_municipality", sa.String(length=100), nullable=True),
        sa.Column("self_poisoning_methods", sa.JSON(), nullable=True),
        sa.Column("self_poisoning_method_details", sa.JSON(), nullable=True),
        sa.Column("self_harm_methods", sa.JSON(), nullable=True),
        sa.Column("self_harm_method_details", sa.JSON(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["registry_id"], ["registries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_table("registry_incident_methods")
    op.drop_table("registry_incidents")
    with op.batch_alter_table("registries", schema=None) as batch_op:
        batch_op.drop_column("has_past_2_month_incident")
        batch_op.drop_column("is_first_incident")


def _migrate_old_incidents():
    bind = op.get_bind()
    old_rows = bind.execute(sa.text("SELECT * FROM incident_details")).mappings().all()
    now = datetime.utcnow()
    for row in old_rows:
        bind.execute(
            sa.text(
                """
                UPDATE registries
                SET is_first_incident = :is_first_incident,
                    has_past_2_month_incident = :has_past_2_month_incident
                WHERE id = :registry_id
                """
            ),
            {
                "is_first_incident": row["is_first_incident"],
                "has_past_2_month_incident": row["has_past_2_month_incident"],
                "registry_id": row["registry_id"],
            },
        )
        result = bind.execute(
            sa.text(
                """
                INSERT INTO registry_incidents (
                    registry_id, incident_date, incident_day, incident_time_range,
                    incident_place, incident_place_other, incident_region,
                    province_or_city, municipality, remarks, created_at, updated_at
                )
                VALUES (
                    :registry_id, :incident_date, :incident_day, :incident_time_range,
                    :incident_place, :incident_place_other, :incident_region,
                    :province_or_city, :municipality, :remarks, :created_at, :updated_at
                )
                """
            ),
            {
                "registry_id": row["registry_id"],
                "incident_date": row["incident_date"],
                "incident_day": row["incident_day"],
                "incident_time_range": row["incident_time_period"],
                "incident_place": row["incident_place"],
                "incident_place_other": row["incident_place_other"],
                "incident_region": row["incident_region"],
                "province_or_city": row["incident_province_city"],
                "municipality": row["incident_municipality"],
                "remarks": row["remarks"],
                "created_at": now,
                "updated_at": now,
            },
        )
        incident_id = result.lastrowid
        _insert_methods(bind, incident_id, "Self-poisoning", _json(row.get("self_poisoning_methods")), _json(row.get("self_poisoning_method_details")), now)
        _insert_methods(bind, incident_id, "Self-harm", _json(row.get("self_harm_methods")), _json(row.get("self_harm_method_details")), now)


def _insert_methods(bind, incident_id, category, methods, details, now):
    for method in methods or []:
        code, description = _split_method(method)
        bind.execute(
            sa.text(
                """
                INSERT INTO registry_incident_methods (
                    incident_id, icd10_code, method_category, method_description,
                    specify_notes, created_at, updated_at
                )
                VALUES (
                    :incident_id, :icd10_code, :method_category, :method_description,
                    :specify_notes, :created_at, :updated_at
                )
                """
            ),
            {
                "incident_id": incident_id,
                "icd10_code": code,
                "method_category": category,
                "method_description": description,
                "specify_notes": (details or {}).get(method),
                "created_at": now,
                "updated_at": now,
            },
        )


def _json(value):
    if not value:
        return [] if value in (None, "") else value
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []


def _split_method(method):
    parts = (method or "").split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else method
