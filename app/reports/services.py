from datetime import datetime

from sqlalchemy import or_

from app.models.incident_detail import RegistryIncident, RegistryIncidentMethod
from app.models.registry import Registry
from app.services.hospitals import get_configured_hospital_code


REPORT_TITLE = "Registry Entries Report"

AGE_GROUPS = [
    ("0-14", 0, 14),
    ("15-24", 15, 24),
    ("25-44", 25, 44),
    ("45-64", 45, 64),
    ("65+", 65, None),
]

REPORT_COLUMNS = [
    "Date encoded",
    "Case reference number",
    "Hospital code",
    "Data steward code",
    "Date of presentation",
    "Time of presentation",
    "Reporting department",
    "Patient identifier",
    "Age",
    "Sex",
    "Sexual orientation",
    "Gender identity",
    "Marital status",
    "Educational attainment",
    "Employment status",
    "Nationality",
    "Religion",
    "First incident",
    "Past 2-month incident",
    "Intent",
    "Infliction",
    "Type of consult",
    "Incident dates",
    "Incident places",
    "Incident times",
    "Incident locations",
    "ICD-10 methods",
    "Previous consultation",
    "Family history",
    "Friends history",
    "Substance use",
    "Substances",
    "Primary diagnosis",
    "Secondary diagnosis",
    "Disposition",
    "Last updated date",
]


def clean_filters(args):
    return {
        "date_from": _parse_date(args.get("date_from")),
        "date_to": _parse_date(args.get("date_to")),
        "hospital_code": _clean(args.get("hospital_code")),
        "data_steward_code": _clean(args.get("data_steward_code")),
        "region": _clean(args.get("region")),
        "province": _clean(args.get("province")),
        "city": _clean(args.get("city")),
        "sex": _clean(args.get("sex")),
        "age_group": _clean(args.get("age_group")),
        "method_category": _clean(args.get("method_category")),
    }


def build_report(user, filters):
    records = filtered_registry_query(user, filters).all()
    rows = [_registry_row(registry, user) for registry in records]
    return {
        "title": REPORT_TITLE,
        "summary": [{"label": "Registry entries", "value": len(rows)}],
        "columns": REPORT_COLUMNS,
        "rows": rows,
    }


def filtered_registry_query(user, filters):
    query = Registry.query.filter(Registry.deleted_at.is_(None))
    query = _apply_scope(query, user)
    query = _apply_registry_filters(query, filters)

    if _has_incident_filters(filters):
        query = query.join(RegistryIncident)
        if filters.get("method_category"):
            query = query.join(RegistryIncidentMethod)
        query = _apply_incident_filters(query, filters)

    return query.distinct().order_by(Registry.date_of_presentation.desc(), Registry.created_at.desc())


def filter_options(user):
    query = _scoped_registry_query(user)
    incidents = RegistryIncident.query.join(Registry)
    incidents = _apply_scope(incidents, user)
    methods = RegistryIncidentMethod.query.join(RegistryIncident).join(Registry)
    methods = _apply_scope(methods, user)
    return {
        "hospital_codes": _distinct_values(query, Registry.hospital_code),
        "data_steward_codes": _distinct_values(query, Registry.data_steward_code),
        "regions": _distinct_values(incidents, RegistryIncident.incident_region),
        "provinces": _distinct_values(incidents, RegistryIncident.province_or_city),
        "cities": _distinct_values(incidents, RegistryIncident.municipality),
        "sexes": _distinct_values(query, Registry.sex_at_birth),
        "method_categories": _distinct_values(methods, RegistryIncidentMethod.method_category),
        "age_groups": [group[0] for group in AGE_GROUPS],
    }


def applied_filter_labels(filters):
    labels = []
    for key, label in [
        ("date_from", "Date from"),
        ("date_to", "Date to"),
        ("hospital_code", "Hospital code"),
        ("data_steward_code", "Data steward code"),
        ("region", "Region"),
        ("province", "Province"),
        ("city", "City/Municipality"),
        ("sex", "Sex"),
        ("age_group", "Age group"),
        ("method_category", "Incident type / method category"),
    ]:
        value = filters.get(key)
        if value:
            labels.append((label, value.isoformat() if hasattr(value, "isoformat") else value))
    return labels


def export_rows(report):
    return [[row.get(column, "") for column in report["columns"]] for row in report["rows"]]


def mask_identifier(value):
    if not value:
        return ""
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def _registry_row(registry, user):
    case = registry.case_ascertainment
    history = registry.psychiatric_history
    diagnosis = registry.diagnosis_disposition
    incidents = registry.incidents or []
    return {
        "Date encoded": _datetime_label(registry.created_at),
        "Case reference number": registry.registry_code,
        "Hospital code": registry.hospital_code,
        "Data steward code": registry.data_steward_code,
        "Date of presentation": _date_label(registry.date_of_presentation),
        "Time of presentation": registry.time_of_presentation.strftime("%H:%M") if registry.time_of_presentation else "",
        "Reporting department": registry.reporting_department,
        "Patient identifier": registry.patient_identifier if user.role == "Admin" else mask_identifier(registry.patient_identifier),
        "Age": registry.age,
        "Sex": registry.sex_at_birth,
        "Sexual orientation": _with_other(registry.sexual_orientation, registry.sexual_orientation_other),
        "Gender identity": _with_other(registry.gender_identity, registry.gender_identity_other),
        "Marital status": registry.marital_status,
        "Educational attainment": registry.highest_educational_attainment,
        "Employment status": registry.employment_status,
        "Nationality": registry.nationality,
        "Religion": _with_other(registry.religion, registry.religion_other),
        "First incident": _bool_label(registry.is_first_incident),
        "Past 2-month incident": _bool_label(registry.has_past_2_month_incident),
        "Intent": case.intent if case else "",
        "Infliction": case.infliction if case else "",
        "Type of consult": _with_other(case.type_of_consult, case.type_of_consult_other) if case else "",
        "Incident dates": _join(_date_label(incident.incident_date) for incident in incidents),
        "Incident places": _join(_incident_place(incident) for incident in incidents),
        "Incident times": _join(incident.incident_time_range for incident in incidents),
        "Incident locations": _join(_incident_location(incident) for incident in incidents),
        "ICD-10 methods": _join(_method_label(method) for incident in incidents for method in incident.methods),
        "Previous consultation": _bool_label(history.previous_consultation) if history else "",
        "Family history": _bool_label(history.family_history) if history else "",
        "Friends history": _bool_label(history.friends_history) if history else "",
        "Substance use": _bool_label(history.substance_use) if history else "",
        "Substances": _join(history.substances or []) if history else "",
        "Primary diagnosis": diagnosis.primary_diagnosis_code if diagnosis else "",
        "Secondary diagnosis": diagnosis.secondary_diagnosis_code if diagnosis else "",
        "Disposition": _with_other(diagnosis.disposition, diagnosis.disposition_other) if diagnosis else "",
        "Last updated date": _datetime_label(registry.updated_at),
    }


def _scoped_registry_query(user):
    return _apply_scope(Registry.query.filter(Registry.deleted_at.is_(None)), user)


def _apply_scope(query, user):
    if user.role == "Encoder":
        hospital_code = get_configured_hospital_code()
        scope = [Registry.created_by == user.id, Registry.data_steward_code == user.employee_no]
        if hospital_code:
            scope.append(Registry.hospital_code == hospital_code)
        return query.filter(or_(*scope))
    return query


def _apply_registry_filters(query, filters):
    if filters.get("date_from"):
        query = query.filter(Registry.date_of_presentation >= filters["date_from"])
    if filters.get("date_to"):
        query = query.filter(Registry.date_of_presentation <= filters["date_to"])
    if filters.get("hospital_code"):
        query = query.filter(Registry.hospital_code == filters["hospital_code"])
    if filters.get("data_steward_code"):
        query = query.filter(Registry.data_steward_code == filters["data_steward_code"])
    if filters.get("sex"):
        query = query.filter(Registry.sex_at_birth == filters["sex"])
    if filters.get("age_group"):
        bounds = next((group for group in AGE_GROUPS if group[0] == filters["age_group"]), None)
        if bounds:
            _, start, end = bounds
            query = query.filter(Registry.age >= start)
            if end is not None:
                query = query.filter(Registry.age <= end)
    return query


def _apply_incident_filters(query, filters):
    if filters.get("region"):
        query = query.filter(RegistryIncident.incident_region == filters["region"])
    if filters.get("province"):
        query = query.filter(RegistryIncident.province_or_city == filters["province"])
    if filters.get("city"):
        query = query.filter(RegistryIncident.municipality == filters["city"])
    if filters.get("method_category"):
        query = query.filter(RegistryIncidentMethod.method_category == filters["method_category"])
    return query


def _has_incident_filters(filters):
    return any(filters.get(key) for key in ["region", "province", "city", "method_category"])


def _distinct_values(query, column):
    return [value for (value,) in query.with_entities(column).filter(column.is_not(None)).distinct().order_by(column).all() if value]


def _method_label(method):
    return f"{method.method_category}: {method.icd10_code} {method.method_description}".strip()


def _incident_location(incident):
    parts = [incident.incident_region, incident.province_or_city, incident.municipality]
    return " / ".join(part for part in parts if part)


def _incident_place(incident):
    if incident.incident_place == "Other" and incident.incident_place_other:
        return incident.incident_place_other
    return incident.incident_place


def _with_other(value, other):
    if (value or "").lower() == "other" and other:
        return other
    return value or ""


def _join(values):
    cleaned = [str(value) for value in values if value not in ("", None)]
    return "; ".join(cleaned)


def _bool_label(value):
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return ""


def _date_label(value):
    return value.isoformat() if value else ""


def _datetime_label(value):
    return value.strftime("%Y-%m-%d %H:%M") if value else ""


def _clean(value):
    value = (value or "").strip()
    return value or None


def _parse_date(value):
    value = _clean(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
