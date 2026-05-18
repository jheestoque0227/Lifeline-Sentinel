"""seed full ph locations

Revision ID: e7b9c1d4a6f2
Revises: d8a4f6b2c9e1
Create Date: 2026-05-18 00:00:00.000000

"""
import json
from datetime import datetime
from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "e7b9c1d4a6f2"
down_revision = "d8a4f6b2c9e1"
branch_labels = None
depends_on = None


def _seed_path():
    return Path(__file__).resolve().parents[1] / "data" / "ph_locations.json"


def _load_seed():
    return json.loads(_seed_path().read_text(encoding="utf-8"))


def _chunks(items, size=500):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _clear_tables(connection):
    connection.execute(sa.text("DELETE FROM ph_cities_municipalities"))
    connection.execute(sa.text("DELETE FROM ph_provinces"))
    connection.execute(sa.text("DELETE FROM ph_regions"))


def upgrade():
    seed = _load_seed()
    now = datetime.utcnow()
    connection = op.get_bind()
    _clear_tables(connection)

    region_table = sa.table(
        "ph_regions",
        sa.column("id", sa.Integer()),
        sa.column("region_code", sa.String()),
        sa.column("region_name", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    province_table = sa.table(
        "ph_provinces",
        sa.column("id", sa.Integer()),
        sa.column("region_id", sa.Integer()),
        sa.column("province_code", sa.String()),
        sa.column("province_name", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    city_table = sa.table(
        "ph_cities_municipalities",
        sa.column("province_id", sa.Integer()),
        sa.column("city_municipality_code", sa.String()),
        sa.column("city_municipality_name", sa.String()),
        sa.column("is_city", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    region_ids = {}
    region_rows = []
    for index, region in enumerate(seed["regions"], start=1):
        region_ids[region["code"]] = index
        region_rows.append(
            {
                "id": index,
                "region_code": region["code"],
                "region_name": region["name"],
                "sort_order": region.get("id") or index,
                "created_at": now,
                "updated_at": now,
            }
        )
    op.bulk_insert(region_table, region_rows)

    province_ids = {}
    province_rows = []
    for index, province in enumerate(seed["provinces"], start=1):
        province_ids[province["code"]] = index
        province_rows.append(
            {
                "id": index,
                "region_id": region_ids[province["region_code"]],
                "province_code": province["code"],
                "province_name": province["name"],
                "sort_order": province.get("id") or index,
                "created_at": now,
                "updated_at": now,
            }
        )
    for rows in _chunks(province_rows):
        op.bulk_insert(province_table, rows)

    city_rows = []
    for index, city in enumerate(seed["cities_municipalities"], start=1):
        city_rows.append(
            {
                "province_id": province_ids[city["province_code"]],
                "city_municipality_code": city["code"],
                "city_municipality_name": city["name"],
                "is_city": bool(city.get("is_city")),
                "sort_order": city.get("id") or index,
                "created_at": now,
                "updated_at": now,
            }
        )
    for rows in _chunks(city_rows):
        op.bulk_insert(city_table, rows)


def downgrade():
    _clear_tables(op.get_bind())
