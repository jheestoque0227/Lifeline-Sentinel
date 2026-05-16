from datetime import datetime
from app.extensions import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    event = db.Column(db.String(100), nullable=False)
    module = db.Column(db.String(100), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
