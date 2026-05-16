from app.extensions import db

class IncidentDetail(db.Model):
    __tablename__ = "incident_details"

    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey("registries.id"), nullable=False)

    is_first_incident = db.Column(db.Boolean, nullable=False)
    has_past_2_month_incident = db.Column(db.Boolean, nullable=True)

    incident_date = db.Column(db.Date, nullable=True)
    incident_day = db.Column(db.String(20), nullable=True)
    incident_time_period = db.Column(db.String(50), nullable=True)
    incident_place = db.Column(db.String(150), nullable=True)
    incident_place_other = db.Column(db.String(150), nullable=True)
    incident_region = db.Column(db.String(100), nullable=True)
    incident_province_city = db.Column(db.String(100), nullable=True)
    incident_municipality = db.Column(db.String(100), nullable=True)

    self_poisoning_methods = db.Column(db.JSON, nullable=True)
    self_harm_methods = db.Column(db.JSON, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
