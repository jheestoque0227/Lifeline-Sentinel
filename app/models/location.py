from datetime import datetime

from app.extensions import db


class PhilippineRegion(db.Model):
    __tablename__ = "ph_regions"

    id = db.Column(db.Integer, primary_key=True)
    region_code = db.Column(db.String(20), unique=True, nullable=False)
    region_name = db.Column(db.String(150), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provinces = db.relationship("PhilippineProvince", backref="region", lazy=True)


class PhilippineProvince(db.Model):
    __tablename__ = "ph_provinces"

    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey("ph_regions.id"), nullable=False)
    province_code = db.Column(db.String(20), unique=True, nullable=False)
    province_name = db.Column(db.String(150), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cities_municipalities = db.relationship("PhilippineCityMunicipality", backref="province", lazy=True)


class PhilippineCityMunicipality(db.Model):
    __tablename__ = "ph_cities_municipalities"

    id = db.Column(db.Integer, primary_key=True)
    province_id = db.Column(db.Integer, db.ForeignKey("ph_provinces.id"), nullable=False)
    city_municipality_code = db.Column(db.String(20), unique=True, nullable=False)
    city_municipality_name = db.Column(db.String(150), nullable=False)
    is_city = db.Column(db.Boolean, nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
