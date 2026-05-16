from app.extensions import db

class PsychiatricHistory(db.Model):
    __tablename__ = "psychiatric_histories"

    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey("registries.id"), nullable=False)

    previous_consultation = db.Column(db.Boolean, nullable=True)
    previous_consultation_notes = db.Column(db.Text, nullable=True)
    family_history = db.Column(db.Boolean, nullable=True)
    family_history_notes = db.Column(db.Text, nullable=True)
    friends_history = db.Column(db.Boolean, nullable=True)
    friends_history_notes = db.Column(db.Text, nullable=True)
    substance_use = db.Column(db.Boolean, nullable=True)
    substances = db.Column(db.JSON, nullable=True)
    substance_details = db.Column(db.JSON, nullable=True)
    substance_notes = db.Column(db.Text, nullable=True)
