from datetime import datetime

from app.extensions import db


class RegistryIncident(db.Model):
    __tablename__ = "registry_incidents"

    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey("registries.id"), nullable=False)
    incident_date = db.Column(db.Date, nullable=True)
    incident_day = db.Column(db.String(20), nullable=True)
    incident_time_range = db.Column(db.String(50), nullable=True)
    incident_place = db.Column(db.String(150), nullable=True)
    incident_place_other = db.Column(db.String(150), nullable=True)
    incident_region = db.Column(db.String(100), nullable=True)
    province_or_city = db.Column(db.String(100), nullable=True)
    municipality = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    methods = db.relationship(
        "RegistryIncidentMethod",
        backref="incident",
        cascade="all, delete-orphan",
        lazy=True,
    )


class RegistryIncidentMethod(db.Model):
    __tablename__ = "registry_incident_methods"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("registry_incidents.id"), nullable=False)
    icd10_code = db.Column(db.String(10), nullable=False)
    method_category = db.Column(db.String(50), nullable=False)
    method_description = db.Column(db.String(255), nullable=False)
    specify_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


IncidentDetail = RegistryIncident
