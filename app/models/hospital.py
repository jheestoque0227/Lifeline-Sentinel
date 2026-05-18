from datetime import datetime

from app.extensions import db


class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    hospital_code = db.Column(db.String(50), unique=True, nullable=False)
    hospital_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
