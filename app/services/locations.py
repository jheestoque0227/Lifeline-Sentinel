from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.location import PhilippineCityMunicipality, PhilippineProvince, PhilippineRegion
from app.registry import options


def get_regions():
    try:
        rows = (
            PhilippineRegion.query.order_by(PhilippineRegion.sort_order, PhilippineRegion.region_name)
            .all()
        )
        if rows:
            return [{"id": row.region_name, "text": row.region_name} for row in rows]
    except SQLAlchemyError:
        db.session.rollback()
        pass
    return [{"id": region, "text": region} for region in options.LOCATION_OPTIONS.keys()]


def get_provinces(region_code):
    if not region_code:
        return []
    try:
        rows = (
            PhilippineProvince.query.join(PhilippineRegion)
            .filter(
                (PhilippineRegion.region_code == region_code)
                | (PhilippineRegion.region_name == region_code)
            )
            .order_by(PhilippineProvince.sort_order, PhilippineProvince.province_name)
            .all()
        )
        if rows:
            return [{"id": row.province_name, "text": row.province_name} for row in rows]
    except SQLAlchemyError:
        db.session.rollback()
        pass
    return [{"id": value, "text": value} for value in options.LOCATION_OPTIONS.get(region_code, {}).keys()]


def get_cities_municipalities(province_code):
    if not province_code:
        return []
    try:
        rows = (
            PhilippineCityMunicipality.query.join(PhilippineProvince)
            .filter(
                (PhilippineProvince.province_code == province_code)
                | (PhilippineProvince.province_name == province_code)
            )
            .order_by(
                PhilippineCityMunicipality.sort_order,
                PhilippineCityMunicipality.city_municipality_name,
            )
            .all()
        )
        if rows:
            return [{"id": row.city_municipality_name, "text": row.city_municipality_name} for row in rows]
    except SQLAlchemyError:
        db.session.rollback()
        pass

    for provinces in options.LOCATION_OPTIONS.values():
        if province_code in provinces:
            return [{"id": value, "text": value} for value in provinces[province_code]]
    return []


def resolve_region_name(region_code):
    if not region_code:
        return None
    try:
        row = PhilippineRegion.query.filter_by(region_code=region_code).first()
        if row:
            return row.region_name
    except SQLAlchemyError:
        db.session.rollback()
        pass
    return region_code


def resolve_province_name(province_code):
    if not province_code:
        return None
    try:
        row = PhilippineProvince.query.filter_by(province_code=province_code).first()
        if row:
            return row.province_name
    except SQLAlchemyError:
        db.session.rollback()
        pass
    return province_code


def resolve_city_municipality_name(city_municipality_code):
    if not city_municipality_code:
        return None
    try:
        row = PhilippineCityMunicipality.query.filter_by(city_municipality_code=city_municipality_code).first()
        if row:
            return row.city_municipality_name
    except SQLAlchemyError:
        db.session.rollback()
        pass
    return city_municipality_code
