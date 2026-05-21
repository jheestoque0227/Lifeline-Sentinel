from datetime import datetime
from app.extensions import db

class Registry(db.Model):
    __tablename__ = "registries"

    id = db.Column(db.Integer, primary_key=True)
    registry_code = db.Column(db.String(50), unique=True, nullable=False)

    data_steward_code = db.Column(db.String(50), nullable=False)
    hospital_code = db.Column(db.String(50), nullable=False)
    date_of_presentation = db.Column(db.Date, nullable=False)
    time_of_presentation = db.Column(db.Time, nullable=True)
    reporting_department = db.Column(db.Enum("ER", "OPS"), nullable=False)
    is_valid_registry_case = db.Column(db.Boolean, nullable=False, default=True)
    invalid_reason = db.Column(db.String(255), nullable=True)
    is_first_incident = db.Column(db.Boolean, nullable=True)
    has_past_2_month_incident = db.Column(db.Boolean, nullable=True)

    patient_identifier = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex_at_birth = db.Column(db.String(50), nullable=False)
    sexual_orientation = db.Column(db.String(100), nullable=True)
    sexual_orientation_other = db.Column(db.String(150), nullable=True)
    gender_identity = db.Column(db.String(100), nullable=True)
    gender_identity_other = db.Column(db.String(150), nullable=True)
    marital_status = db.Column(db.String(100), nullable=True)
    highest_educational_attainment = db.Column(db.String(150), nullable=True)
    employment_status = db.Column(db.String(100), nullable=True)
    nationality = db.Column(db.String(100), nullable=True)
    religion = db.Column(db.String(100), nullable=True)
    religion_other = db.Column(db.String(150), nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_remarks = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    case_ascertainment = db.relationship(
        "CaseAscertainment",
        backref="registry",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    incidents = db.relationship(
        "RegistryIncident",
        backref="registry",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="RegistryIncident.id",
    )
    psychiatric_history = db.relationship(
        "PsychiatricHistory",
        backref="registry",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    diagnosis_disposition = db.relationship(
        "DiagnosisDisposition",
        backref="registry",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
