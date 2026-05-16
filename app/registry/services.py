from datetime import datetime

from sqlalchemy import func, or_

from app.extensions import db
from app.models.case_ascertainment import CaseAscertainment
from app.models.diagnosis_disposition import DiagnosisDisposition
from app.models.incident_detail import IncidentDetail
from app.models.psychiatric_history import PsychiatricHistory
from app.models.registry import Registry


def registry_query(include_deleted=False):
    query = Registry.query
    if not include_deleted:
        query = query.filter(Registry.deleted_at.is_(None))
    return query


def search_registries(q=None, risk_level=None, reporting_department=None, include_deleted=False):
    query = registry_query(include_deleted=include_deleted)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Registry.registry_code.ilike(like), Registry.patient_identifier.ilike(like)))
    if risk_level:
        query = query.filter(Registry.risk_level == risk_level)
    if reporting_department:
        query = query.filter(Registry.reporting_department == reporting_department)
    return query.order_by(Registry.date_of_presentation.desc(), Registry.created_at.desc())


def generate_registry_code():
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"SSASH-{today}-"
    latest = (
        Registry.query.filter(Registry.registry_code.like(f"{prefix}%"))
        .order_by(Registry.registry_code.desc())
        .first()
    )
    sequence = 1
    if latest:
        try:
            sequence = int(latest.registry_code.rsplit("-", 1)[1]) + 1
        except (IndexError, ValueError):
            sequence = 1
    return f"{prefix}{sequence:04d}"


def create_registry(form, user):
    registry = Registry(registry_code=generate_registry_code(), created_by=user.id)
    apply_registry_form(registry, form, user, is_create=True)
    db.session.add(registry)
    return registry


def update_registry(registry, form, user):
    apply_registry_form(registry, form, user, is_create=False)
    registry.updated_by = user.id
    return registry


def apply_registry_form(registry, form, user, is_create=False):
    registry.data_steward_code = form.data_steward_code.data
    registry.hospital_code = form.hospital_code.data
    registry.date_of_presentation = form.date_of_presentation.data
    registry.time_of_presentation = form.time_of_presentation.data
    registry.reporting_department = form.reporting_department.data
    registry.patient_identifier = form.patient_identifier.data
    registry.age = form.age.data
    registry.sex_at_birth = form.sex_at_birth.data
    registry.sexual_orientation = _empty_to_none(form.sexual_orientation.data)
    registry.sexual_orientation_other = _other_value(form.sexual_orientation.data, form.sexual_orientation_other.data)
    registry.gender_identity = _empty_to_none(form.gender_identity.data)
    registry.gender_identity_other = _other_value(form.gender_identity.data, form.gender_identity_other.data)
    registry.marital_status = _empty_to_none(form.marital_status.data)
    registry.highest_educational_attainment = _empty_to_none(form.highest_educational_attainment.data)
    registry.employment_status = _empty_to_none(form.employment_status.data)
    registry.nationality = _empty_to_none(form.nationality.data)
    registry.religion = _empty_to_none(form.religion.data)
    registry.religion_other = _other_value(form.religion.data, form.religion_other.data)
    registry.risk_level = _empty_to_none(form.risk_level.data) or "Low"
    registry.is_valid_registry_case = True
    registry.invalid_reason = None
    if is_create:
        registry.created_by = user.id

    case = registry.case_ascertainment or CaseAscertainment(registry=registry)
    case.intent = form.intent.data
    case.infliction = form.infliction.data
    case.type_of_consult = form.type_of_consult.data
    case.type_of_consult_other = _other_value(form.type_of_consult.data, form.type_of_consult_other.data)
    registry.case_ascertainment = case

    incident = registry.incident_details[0] if registry.incident_details else IncidentDetail(registry=registry)
    incident.is_first_incident = _to_bool(form.is_first_incident.data)
    incident.has_past_2_month_incident = _to_bool(form.has_past_2_month_incident.data)
    incident.incident_date = form.incident_date.data
    incident.incident_day = _empty_to_none(form.incident_day.data)
    incident.incident_time_period = _empty_to_none(form.incident_time_period.data)
    incident.incident_place = _empty_to_none(form.incident_place.data)
    incident.incident_place_other = _other_value(form.incident_place.data, form.incident_place_other.data)
    incident.incident_region = _empty_to_none(form.incident_region.data)
    incident.incident_province_city = _empty_to_none(form.incident_province_city.data)
    incident.incident_municipality = _empty_to_none(form.incident_municipality.data)
    incident.self_poisoning_methods = form.self_poisoning_methods.data or []
    incident.self_harm_methods = form.self_harm_methods.data or []
    incident.remarks = _empty_to_none(form.incident_remarks.data)
    if not registry.incident_details:
        registry.incident_details.append(incident)

    history = registry.psychiatric_history or PsychiatricHistory(registry=registry)
    history.previous_consultation = _to_bool(form.previous_consultation.data)
    history.previous_consultation_notes = _empty_to_none(form.previous_consultation_notes.data)
    history.family_history = _to_bool(form.family_history.data)
    history.family_history_notes = _empty_to_none(form.family_history_notes.data)
    history.friends_history = _to_bool(form.friends_history.data)
    history.friends_history_notes = _empty_to_none(form.friends_history_notes.data)
    history.substance_use = _to_bool(form.substance_use.data)
    selected_substances = form.substances.data or []
    if not history.substance_use:
        selected_substances = []
    detail_fields = {
        "Alcohol": form.alcohol_type.data,
        "Methamphetamine": form.methamphetamine_type.data,
        "Cannabinoids": form.cannabinoids_type.data,
        "Prescription drugs": form.prescription_drugs_type.data,
    }
    history.substances = selected_substances
    history.substance_details = {
        substance: _empty_to_none(detail_fields.get(substance))
        for substance in selected_substances
    }
    history.substance_notes = _empty_to_none(form.substance_notes.data)
    registry.psychiatric_history = history

    diagnosis = registry.diagnosis_disposition or DiagnosisDisposition(registry=registry)
    diagnosis.primary_diagnosis_code = _empty_to_none(form.primary_diagnosis_code.data)
    diagnosis.secondary_diagnosis_code = _empty_to_none(form.secondary_diagnosis_code.data)
    diagnosis.disposition = _empty_to_none(form.disposition.data)
    diagnosis.disposition_other = _other_value(form.disposition.data, form.disposition_other.data)
    diagnosis.remarks = _empty_to_none(form.diagnosis_remarks.data)
    registry.diagnosis_disposition = diagnosis


def populate_form(form, registry):
    incident = registry.incident_details[0] if registry.incident_details else None
    case = registry.case_ascertainment
    history = registry.psychiatric_history
    diagnosis = registry.diagnosis_disposition

    for field in [
        "data_steward_code",
        "hospital_code",
        "date_of_presentation",
        "time_of_presentation",
        "reporting_department",
        "patient_identifier",
        "age",
        "sex_at_birth",
        "sexual_orientation",
        "sexual_orientation_other",
        "gender_identity",
        "gender_identity_other",
        "marital_status",
        "highest_educational_attainment",
        "employment_status",
        "nationality",
        "religion",
        "religion_other",
        "risk_level",
    ]:
        getattr(form, field).data = getattr(registry, field)

    if case:
        form.intent.data = case.intent
        form.infliction.data = case.infliction
        form.type_of_consult.data = case.type_of_consult
        form.type_of_consult_other.data = case.type_of_consult_other
    if incident:
        form.is_first_incident.data = _from_bool(incident.is_first_incident)
        form.has_past_2_month_incident.data = _from_bool(incident.has_past_2_month_incident)
        form.incident_date.data = incident.incident_date
        form.incident_day.data = incident.incident_day
        form.incident_time_period.data = incident.incident_time_period
        form.incident_place.data = incident.incident_place
        form.incident_place_other.data = incident.incident_place_other
        form.incident_region.data = incident.incident_region
        form.incident_province_city.data = incident.incident_province_city
        form.incident_municipality.data = incident.incident_municipality
        form.self_poisoning_methods.data = incident.self_poisoning_methods or []
        form.self_harm_methods.data = incident.self_harm_methods or []
        form.incident_remarks.data = incident.remarks
    if history:
        form.previous_consultation.data = _from_bool(history.previous_consultation)
        form.previous_consultation_notes.data = history.previous_consultation_notes
        form.family_history.data = _from_bool(history.family_history)
        form.family_history_notes.data = history.family_history_notes
        form.friends_history.data = _from_bool(history.friends_history)
        form.friends_history_notes.data = history.friends_history_notes
        form.substance_use.data = _from_bool(history.substance_use)
        form.substances.data = history.substances or []
        substance_details = history.substance_details or {}
        form.alcohol_type.data = substance_details.get("Alcohol")
        form.methamphetamine_type.data = substance_details.get("Methamphetamine")
        form.cannabinoids_type.data = substance_details.get("Cannabinoids")
        form.prescription_drugs_type.data = substance_details.get("Prescription drugs")
        form.substance_notes.data = history.substance_notes
    if diagnosis:
        form.primary_diagnosis_code.data = diagnosis.primary_diagnosis_code
        form.secondary_diagnosis_code.data = diagnosis.secondary_diagnosis_code
        form.disposition.data = diagnosis.disposition
        form.disposition_other.data = diagnosis.disposition_other
        form.diagnosis_remarks.data = diagnosis.remarks


def soft_delete_registry(registry, user, remarks):
    registry.deleted_at = datetime.utcnow()
    registry.deleted_by = user.id
    registry.deleted_remarks = remarks
    registry.updated_by = user.id


def registry_snapshot(registry):
    incident = registry.incident_details[0] if registry.incident_details else None
    return {
        "id": registry.id,
        "registry_code": registry.registry_code,
        "patient_identifier": registry.patient_identifier,
        "date_of_presentation": _serialize(registry.date_of_presentation),
        "reporting_department": registry.reporting_department,
        "risk_level": registry.risk_level,
        "deleted_at": _serialize(registry.deleted_at),
        "case_ascertainment": _model_dict(registry.case_ascertainment, ["intent", "infliction", "type_of_consult"]),
        "incident": _model_dict(incident, ["incident_date", "self_poisoning_methods", "self_harm_methods"]),
        "diagnosis": _model_dict(registry.diagnosis_disposition, ["primary_diagnosis_code", "secondary_diagnosis_code", "disposition"]),
    }


def registry_statistics():
    active = Registry.query.filter(Registry.deleted_at.is_(None))
    total = active.count()
    deleted = Registry.query.filter(Registry.deleted_at.is_not(None)).count()
    high_risk = active.filter(Registry.risk_level == "High").count()
    by_risk = dict(
        active.with_entities(Registry.risk_level, func.count(Registry.id))
        .group_by(Registry.risk_level)
        .all()
    )
    by_department = dict(
        active.with_entities(Registry.reporting_department, func.count(Registry.id))
        .group_by(Registry.reporting_department)
        .all()
    )
    return {
        "total": total,
        "deleted": deleted,
        "high_risk": high_risk,
        "by_risk": by_risk,
        "by_department": by_department,
    }


def _empty_to_none(value):
    return value if value not in ("", None) else None


def _other_value(parent_value, other_value):
    if (parent_value or "").lower() != "other":
        return None
    return _empty_to_none(other_value)


def _to_bool(value):
    if value == "yes":
        return True
    if value == "no":
        return False
    return None


def _from_bool(value):
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return ""


def _serialize(value):
    return value.isoformat() if value else None


def _model_dict(model, fields):
    if not model:
        return {}
    return {field: _serialize(getattr(model, field)) if hasattr(getattr(model, field), "isoformat") else getattr(model, field) for field in fields}
