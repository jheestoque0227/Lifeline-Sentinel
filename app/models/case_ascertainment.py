from app.extensions import db

class CaseAscertainment(db.Model):
    __tablename__ = "case_ascertainments"

    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey("registries.id"), nullable=False)

    intent = db.Column(db.Enum("Intentional", "Accidental"), nullable=False)
    infliction = db.Column(db.Enum("Self-inflicted", "Inflicted by another"), nullable=False)
    type_of_consult = db.Column(db.String(100), nullable=False)
    type_of_consult_other = db.Column(db.String(150), nullable=True)
