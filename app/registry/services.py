from datetime import datetime

from flask import request
from sqlalchemy import func, or_

from app.extensions import db
from app.models.case_ascertainment import CaseAscertainment
from app.models.diagnosis_disposition import DiagnosisDisposition
from app.models.incident_detail import RegistryIncident, RegistryIncidentMethod
from app.models.psychiatric_history import PsychiatricHistory
from app.models.registry import Registry
from app.services.hospitals import get_configured_hospital_code, get_user_hospital_code, user_has_all_hospitals


def registry_query(include_deleted=False, user=None):
    query = Registry.query
    if not include_deleted:
        query = query.filter(Registry.deleted_at.is_(None))
    query = apply_user_hospital_scope(query, user)
    return query


def search_registries(q=None, reporting_department=None, hospital_code=None, include_deleted=False, user=None):
    query = registry_query(include_deleted=include_deleted, user=user)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Registry.registry_code.ilike(like), Registry.patient_identifier.ilike(like)))
    if reporting_department:
        query = query.filter(Registry.reporting_department == reporting_department)
    if hospital_code:
        query = query.filter(Registry.hospital_code == hospital_code)
    return query.order_by(Registry.date_of_presentation.desc(), Registry.created_at.desc())


def apply_user_hospital_scope(query, user):
    if not user or user.role == "Admin" or user_has_all_hospitals(user):
        return query
    hospital_code = get_user_hospital_code(user)
    if not hospital_code:
        return query.filter(False)
    return query.filter(Registry.hospital_code == hospital_code)


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
    if is_create or not registry.data_steward_code:
        registry.data_steward_code = user.employee_no
    if is_create or not registry.hospital_code:
        registry.hospital_code = get_configured_hospital_code(user)
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
    registry.is_valid_registry_case = True
    registry.invalid_reason = None
    registry.is_first_incident = _to_bool(form.is_first_incident.data)
    registry.has_past_2_month_incident = _to_bool(form.has_past_2_month_incident.data)
    if is_create:
        registry.created_by = user.id

    case = registry.case_ascertainment or CaseAscertainment(registry=registry)
    case.intent = form.intent.data
    case.infliction = form.infliction.data
    case.type_of_consult = form.type_of_consult.data
    case.type_of_consult_other = _other_value(form.type_of_consult.data, form.type_of_consult_other.data)
    registry.case_ascertainment = case

    registry.incidents = _build_incidents_from_request()

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
    ]:
        getattr(form, field).data = getattr(registry, field)
    form.is_first_incident.data = _from_bool(registry.is_first_incident)
    form.has_past_2_month_incident.data = _from_bool(registry.has_past_2_month_incident)

    if case:
        form.intent.data = case.intent
        form.infliction.data = case.infliction
        form.type_of_consult.data = case.type_of_consult
        form.type_of_consult_other.data = case.type_of_consult_other
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
    registry.deleted_remarks = remarks
    registry.updated_by = user.id


def registry_snapshot(registry):
    return {
        "id": registry.id,
        "registry_code": registry.registry_code,
        "patient_identifier": registry.patient_identifier,
        "date_of_presentation": _serialize(registry.date_of_presentation),
        "reporting_department": registry.reporting_department,
        "deleted_at": _serialize(registry.deleted_at),
        "case_ascertainment": _model_dict(registry.case_ascertainment, ["intent", "infliction", "type_of_consult"]),
        "incidents": [incident_snapshot(incident) for incident in registry.incidents],
        "diagnosis": _model_dict(registry.diagnosis_disposition, ["primary_diagnosis_code", "secondary_diagnosis_code", "disposition"]),
    }


def registry_statistics(user=None):
    active = apply_user_hospital_scope(Registry.query.filter(Registry.deleted_at.is_(None)), user)
    total = active.count()
    deleted = apply_user_hospital_scope(Registry.query.filter(Registry.deleted_at.is_not(None)), user).count()
    by_department = dict(
        active.with_entities(Registry.reporting_department, func.count(Registry.id))
        .group_by(Registry.reporting_department)
        .all()
    )
    return {
        "total": total,
        "deleted": deleted,
        "by_department": by_department,
    }


def _empty_to_none(value):
    return value if value not in ("", None) else None


def _other_value(parent_value, other_value):
    if (parent_value or "").lower() != "other":
        return None
    return _empty_to_none(other_value)


def _build_incidents_from_request():
    incident_indexes = sorted(
        {
            key.split("[", 1)[1].split("]", 1)[0]
            for key in request.form.keys()
            if key.startswith("incidents[") and "][" in key
        },
        key=lambda value: int(value) if value.isdigit() else value,
    )
    incidents = []
    for index in incident_indexes:
        prefix = f"incidents[{index}]"
        if request.form.get(f"{prefix}[remove]") == "1":
            continue
        incident_date = _parse_date(request.form.get(f"{prefix}[incident_date]"))
        incident_day = _empty_to_none(request.form.get(f"{prefix}[incident_day]"))
        incident_time_range = _empty_to_none(request.form.get(f"{prefix}[incident_time_range]"))
        incident_place = _empty_to_none(request.form.get(f"{prefix}[incident_place]"))
        province_or_city = _empty_to_none(request.form.get(f"{prefix}[province_or_city]"))
        municipality = _empty_to_none(request.form.get(f"{prefix}[municipality]"))
        selected_poisoning = request.form.getlist(f"{prefix}[self_poisoning_methods]")
        selected_harm = request.form.getlist(f"{prefix}[self_harm_methods]")

        if not any([incident_date, incident_day, incident_time_range, incident_place, province_or_city, municipality, selected_poisoning, selected_harm]):
            continue

        incident = RegistryIncident(
            incident_date=incident_date,
            incident_day=incident_day,
            incident_time_range=incident_time_range,
            incident_place=incident_place,
            incident_place_other=_other_value(incident_place, request.form.get(f"{prefix}[incident_place_other]")),
            incident_region=_empty_to_none(request.form.get(f"{prefix}[incident_region]")),
            province_or_city=province_or_city,
            municipality=municipality,
            remarks=_empty_to_none(request.form.get(f"{prefix}[remarks]")),
        )
        incident.methods = _build_incident_methods(prefix, selected_poisoning, "Self-poisoning") + _build_incident_methods(prefix, selected_harm, "Self-harm")
        incidents.append(incident)

    if not incidents:
        incidents.append(RegistryIncident())
    return incidents


def _build_incident_methods(prefix, selected_methods, category):
    methods = []
    for method in selected_methods:
        code, description = _split_method(method)
        methods.append(
            RegistryIncidentMethod(
                icd10_code=code,
                method_category=category,
                method_description=description,
                specify_notes=_empty_to_none(request.form.get(f"{prefix}[method_notes][{method}]")),
            )
        )
    return methods


def _split_method(method):
    parts = (method or "").split(" ", 1)
    code = parts[0]
    description = parts[1] if len(parts) > 1 else method
    return code, description


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def incident_payloads(registry):
    payloads = []
    for incident in registry.incidents:
        poisoning_methods = [
            _method_value(method)
            for method in incident.methods
            if method.method_category == "Self-poisoning"
        ]
        harm_methods = [
            _method_value(method)
            for method in incident.methods
            if method.method_category == "Self-harm"
        ]
        notes = {_method_value(method): method.specify_notes or "" for method in incident.methods}
        payloads.append(
            {
                "incident_date": incident.incident_date.isoformat() if incident.incident_date else "",
                "incident_day": incident.incident_day or "",
                "incident_time_range": incident.incident_time_range or "",
                "incident_place": incident.incident_place or "",
                "incident_place_other": incident.incident_place_other or "",
                "incident_region": incident.incident_region or "",
                "province_or_city": incident.province_or_city or "",
                "municipality": incident.municipality or "",
                "self_poisoning_methods": poisoning_methods,
                "self_harm_methods": harm_methods,
                "method_notes": notes,
                "remarks": incident.remarks or "",
            }
        )
    return payloads or [{}]


def incident_snapshot(incident):
    return {
        "incident_date": _serialize(incident.incident_date),
        "incident_day": incident.incident_day,
        "incident_time_range": incident.incident_time_range,
        "incident_place": incident.incident_place,
        "province_or_city": incident.province_or_city,
        "municipality": incident.municipality,
        "methods": [_model_dict(method, ["icd10_code", "method_category", "method_description", "specify_notes"]) for method in incident.methods],
    }


def _method_value(method):
    return f"{method.icd10_code} {method.method_description}".strip()


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
