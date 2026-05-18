"""add ph location lookup tables

Revision ID: d8a4f6b2c9e1
Revises: c9e5a7b3d2f1
Create Date: 2026-05-18 00:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "d8a4f6b2c9e1"
down_revision = "c9e5a7b3d2f1"
branch_labels = None
depends_on = None


REGIONS = [
    ("NCR", "National Capital Region", 1),
    ("REGION_XI", "Region XI", 2),
]

PROVINCES = [
    ("NCR", "NCR_MM", "Metro Manila", 1),
    ("REGION_XI", "DAVAO_CITY", "Davao City", 1),
    ("REGION_XI", "DAVAO_DE_ORO", "Davao de Oro", 2),
    ("REGION_XI", "DAVAO_DEL_NORTE", "Davao del Norte", 3),
    ("REGION_XI", "DAVAO_DEL_SUR", "Davao del Sur", 4),
    ("REGION_XI", "DAVAO_ORIENTAL", "Davao Oriental", 5),
]

CITIES_MUNICIPALITIES = [
    ("NCR_MM", "NCR_CALOOCAN", "Caloocan", True, 1),
    ("NCR_MM", "NCR_LAS_PINAS", "Las Pinas", True, 2),
    ("NCR_MM", "NCR_MAKATI", "Makati", True, 3),
    ("NCR_MM", "NCR_MALABON", "Malabon", True, 4),
    ("NCR_MM", "NCR_MANDALUYONG", "Mandaluyong", True, 5),
    ("NCR_MM", "NCR_MANILA", "Manila", True, 6),
    ("NCR_MM", "NCR_MARIKINA", "Marikina", True, 7),
    ("NCR_MM", "NCR_MUNTINLUPA", "Muntinlupa", True, 8),
    ("NCR_MM", "NCR_NAVOTAS", "Navotas", True, 9),
    ("NCR_MM", "NCR_PARANAQUE", "Paranaque", True, 10),
    ("NCR_MM", "NCR_PASAY", "Pasay", True, 11),
    ("NCR_MM", "NCR_PASIG", "Pasig", True, 12),
    ("NCR_MM", "NCR_PATEROS", "Pateros", False, 13),
    ("NCR_MM", "NCR_QUEZON_CITY", "Quezon City", True, 14),
    ("NCR_MM", "NCR_SAN_JUAN", "San Juan", True, 15),
    ("NCR_MM", "NCR_TAGUIG", "Taguig", True, 16),
    ("NCR_MM", "NCR_VALENZUELA", "Valenzuela", True, 17),
    ("DAVAO_CITY", "DAVAO_CITY_AGDAO", "Agdao", False, 1),
    ("DAVAO_CITY", "DAVAO_CITY_BUHANGIN", "Buhangin", False, 2),
    ("DAVAO_CITY", "DAVAO_CITY_CALINAN", "Calinan", False, 3),
    ("DAVAO_CITY", "DAVAO_CITY_POBLACION", "Poblacion", False, 4),
    ("DAVAO_CITY", "DAVAO_CITY_TALOMO", "Talomo", False, 5),
    ("DAVAO_CITY", "DAVAO_CITY_TORIL", "Toril", False, 6),
    ("DAVAO_DE_ORO", "DAO_COMPOSTELA", "Compostela", False, 1),
    ("DAVAO_DE_ORO", "DAO_MAWAB", "Mawab", False, 2),
    ("DAVAO_DE_ORO", "DAO_MONKAYO", "Monkayo", False, 3),
    ("DAVAO_DE_ORO", "DAO_NABUNTURAN", "Nabunturan", False, 4),
    ("DAVAO_DEL_NORTE", "DDN_PANABO", "Panabo", True, 1),
    ("DAVAO_DEL_NORTE", "DDN_SAMAL", "Samal", True, 2),
    ("DAVAO_DEL_NORTE", "DDN_TAGUM", "Tagum", True, 3),
    ("DAVAO_DEL_SUR", "DDS_DIGOS", "Digos", True, 1),
    ("DAVAO_DEL_SUR", "DDS_HAGONOY", "Hagonoy", False, 2),
    ("DAVAO_DEL_SUR", "DDS_SANTA_CRUZ", "Santa Cruz", False, 3),
    ("DAVAO_ORIENTAL", "DOR_BAGANGA", "Baganga", False, 1),
    ("DAVAO_ORIENTAL", "DOR_LUPON", "Lupon", False, 2),
    ("DAVAO_ORIENTAL", "DOR_MATI", "Mati", True, 3),
]


def upgrade():
    op.create_table(
        "ph_regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_code", sa.String(length=20), nullable=False),
        sa.Column("region_name", sa.String(length=150), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_code"),
    )
    op.create_table(
        "ph_provinces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("province_code", sa.String(length=20), nullable=False),
        sa.Column("province_name", sa.String(length=150), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["region_id"], ["ph_regions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("province_code"),
    )
    op.create_table(
        "ph_cities_municipalities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("province_id", sa.Integer(), nullable=False),
        sa.Column("city_municipality_code", sa.String(length=20), nullable=False),
        sa.Column("city_municipality_name", sa.String(length=150), nullable=False),
        sa.Column("is_city", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["province_id"], ["ph_provinces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_municipality_code"),
    )

    now = datetime.utcnow()
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
    for idx, (code, name, sort_order) in enumerate(REGIONS, start=1):
        region_ids[code] = idx
        op.bulk_insert(
            region_table,
            [{"id": idx, "region_code": code, "region_name": name, "sort_order": sort_order, "created_at": now, "updated_at": now}],
        )

    province_ids = {}
    for idx, (region_code, code, name, sort_order) in enumerate(PROVINCES, start=1):
        province_ids[code] = idx
        op.bulk_insert(
            province_table,
            [{
                "id": idx,
                "region_id": region_ids[region_code],
                "province_code": code,
                "province_name": name,
                "sort_order": sort_order,
                "created_at": now,
                "updated_at": now,
            }],
        )

    op.bulk_insert(
        city_table,
        [
            {
                "province_id": province_ids[province_code],
                "city_municipality_code": code,
                "city_municipality_name": name,
                "is_city": is_city,
                "sort_order": sort_order,
                "created_at": now,
                "updated_at": now,
            }
            for province_code, code, name, is_city, sort_order in CITIES_MUNICIPALITIES
        ],
    )


def downgrade():
    op.drop_table("ph_cities_municipalities")
    op.drop_table("ph_provinces")
    op.drop_table("ph_regions")
