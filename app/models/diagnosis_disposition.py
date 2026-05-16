from app.extensions import db

class DiagnosisDisposition(db.Model):
    __tablename__ = "diagnosis_dispositions"

    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey("registries.id"), nullable=False)

    primary_diagnosis_code = db.Column(db.String(20), nullable=True)
    secondary_diagnosis_code = db.Column(db.String(20), nullable=True)
    disposition = db.Column(db.String(150), nullable=True)
    disposition_other = db.Column(db.String(150), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
