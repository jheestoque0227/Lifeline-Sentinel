from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.models.diagnosis_disposition import DiagnosisDisposition
from app.models.incident_detail import RegistryIncident, RegistryIncidentMethod
from app.models.registry import Registry
from app.services.hospitals import get_user_hospital_code, hospital_filter_choices, user_has_all_hospitals


AGE_GROUPS = [
    ("0-14", 0, 14),
    ("15-24", 15, 24),
    ("25-44", 25, 44),
    ("45-64", 45, 64),
    ("65+", 65, None),
]

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def clean_filters(args):
    return {
        "date_from": _parse_date(args.get("date_from")),
        "date_to": _parse_date(args.get("date_to")),
        "hospital_code": _clean(args.get("hospital_code")),
        "region": _clean(args.get("region")),
        "province": _clean(args.get("province")),
        "city": _clean(args.get("city")),
        "sex": _clean(args.get("sex")),
        "age_group": _clean(args.get("age_group")),
        "method_category": _clean(args.get("method_category")),
        "incident_recurrence": _clean(args.get("incident_recurrence")),
        "department": _clean(args.get("department")),
        "disposition": _clean(args.get("disposition")),
        "forecast_frequency": _clean_choice(args.get("forecast_frequency"), {"monthly", "weekly"}, "monthly"),
    }


def descriptive_dashboard(user, filters):
    records = filtered_registry_query(user, filters).all()
    incidents = [incident for registry in records for incident in registry.incidents]
    methods = [method for incident in incidents for method in incident.methods]

    method_counts = Counter(_method_label(method) for method in methods)
    location_counts = Counter(_incident_location(incident) or "Unspecified" for incident in incidents)
    first_time = sum(1 for registry in records if registry.is_first_incident is True)
    repeated = sum(1 for registry in records if _is_repeated_incident(registry))

    charts = {
        "ageDistribution": _chart("bar", Counter(_age_group(registry.age) for registry in records), labels=[group[0] for group in AGE_GROUPS]),
        "sexDistribution": _chart("doughnut", Counter(registry.sex_at_birth or "Unspecified" for registry in records)),
        "genderIdentity": _chart("bar", Counter(_with_other(registry.gender_identity, registry.gender_identity_other) or "Unspecified" for registry in records)),
        "sexualOrientation": _chart("bar", Counter(_with_other(registry.sexual_orientation, registry.sexual_orientation_other) or "Unspecified" for registry in records)),
        "civilStatus": _chart("doughnut", Counter(registry.marital_status or "Unspecified" for registry in records)),
        "education": _chart("bar", Counter(registry.highest_educational_attainment or "Unspecified" for registry in records), index_axis="y"),
        "employment": _chart("bar", Counter(registry.employment_status or "Unspecified" for registry in records)),
        "nationality": _chart("bar", Counter(registry.nationality or "Unspecified" for registry in records), limit=10),
        "religion": _chart("bar", Counter(_with_other(registry.religion, registry.religion_other) or "Unspecified" for registry in records), limit=10),
        "methods": _chart("bar", method_counts, limit=12, index_axis="y"),
        "locations": _chart("bar", location_counts, limit=10),
        "incidentDays": _chart("bar", Counter(incident.incident_day or "Unspecified" for incident in incidents), labels=DAY_ORDER),
        "incidentTimes": _chart("bar", Counter(incident.incident_time_range or "Unspecified" for incident in incidents)),
        "monthlyTrends": _monthly_trend(records),
        "departments": _chart("bar", Counter(registry.reporting_department or "Unspecified" for registry in records)),
        "recurrence": _chart("doughnut", Counter({"First-time": first_time, "Repeated": repeated})),
        "previousConsultation": _boolean_chart(records, "previous_consultation"),
        "familyHistory": _boolean_chart(records, "family_history"),
        "substanceUse": _boolean_chart(records, "substance_use"),
        "commonSubstances": _chart("bar", Counter(substance for registry in records if registry.psychiatric_history for substance in (registry.psychiatric_history.substances or [])), limit=10, index_axis="y"),
        "diagnosis": _chart("bar", Counter(_diagnosis_label(registry) for registry in records), limit=12),
        "disposition": _chart("doughnut", Counter(_disposition_label(registry) for registry in records)),
    }

    return {
        "summary": {
            "total_cases": len(records),
            "total_incidents": len(incidents),
            "first_time_incidents": first_time,
            "repeated_incidents": repeated,
            "most_common_method": _top_label(method_counts),
            "most_common_location": _top_label(location_counts),
        },
        "charts": charts,
        "tables": {
            "nationality": _table_rows(Counter(registry.nationality or "Unspecified" for registry in records), limit=8),
            "religion": _table_rows(Counter(_with_other(registry.religion, registry.religion_other) or "Unspecified" for registry in records), limit=8),
            "diagnosis": _table_rows(Counter(_diagnosis_label(registry) for registry in records), limit=8),
            "disposition": _table_rows(Counter(_disposition_label(registry) for registry in records), limit=8),
        },
        "has_data": bool(records),
    }


def filtered_registry_query(user, filters):
    query = (
        Registry.query.options(
            joinedload(Registry.case_ascertainment),
            joinedload(Registry.incidents).joinedload(RegistryIncident.methods),
            joinedload(Registry.psychiatric_history),
            joinedload(Registry.diagnosis_disposition),
        )
        .filter(Registry.deleted_at.is_(None))
    )
    query = _apply_scope(query, user)
    query = _apply_registry_filters(query, filters)

    if _has_incident_filters(filters):
        query = query.join(RegistryIncident)
        if filters.get("method_category"):
            query = query.join(RegistryIncidentMethod)
        query = _apply_incident_filters(query, filters)

    if filters.get("disposition"):
        query = query.join(DiagnosisDisposition).filter(DiagnosisDisposition.disposition == filters["disposition"])

    return query.distinct().order_by(Registry.date_of_presentation.desc(), Registry.created_at.desc())


def filter_options(user):
    registry_query = _apply_scope(Registry.query.filter(Registry.deleted_at.is_(None)), user)
    incident_query = _apply_scope(RegistryIncident.query.join(Registry).filter(Registry.deleted_at.is_(None)), user)
    method_query = _apply_scope(RegistryIncidentMethod.query.join(RegistryIncident).join(Registry).filter(Registry.deleted_at.is_(None)), user)
    disposition_query = _apply_scope(DiagnosisDisposition.query.join(Registry).filter(Registry.deleted_at.is_(None)), user)
    return {
        "hospital_codes": hospital_filter_choices(_distinct_values(registry_query, Registry.hospital_code)),
        "regions": _distinct_values(incident_query, RegistryIncident.incident_region),
        "provinces": _distinct_values(incident_query, RegistryIncident.province_or_city),
        "cities": _distinct_values(incident_query, RegistryIncident.municipality),
        "sexes": _distinct_values(registry_query, Registry.sex_at_birth),
        "age_groups": [group[0] for group in AGE_GROUPS],
        "method_categories": _distinct_values(method_query, RegistryIncidentMethod.method_category),
        "departments": _distinct_values(registry_query, Registry.reporting_department),
        "dispositions": _distinct_values(disposition_query, DiagnosisDisposition.disposition),
        "incident_recurrences": ["First-time", "Repeated"],
    }


def applied_filter_payload(filters):
    return {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in filters.items() if value}


def _apply_scope(query, user):
    if user.role in {"Encoder", "Analyst"} and not user_has_all_hospitals(user):
        hospital_code = get_user_hospital_code(user)
        if not hospital_code:
            return query.filter(False)
        return query.filter(Registry.hospital_code == hospital_code)
    return query


def _apply_registry_filters(query, filters):
    if filters.get("date_from"):
        query = query.filter(Registry.date_of_presentation >= filters["date_from"])
    if filters.get("date_to"):
        query = query.filter(Registry.date_of_presentation <= filters["date_to"])
    if filters.get("hospital_code"):
        query = query.filter(Registry.hospital_code == filters["hospital_code"])
    if filters.get("sex"):
        query = query.filter(Registry.sex_at_birth == filters["sex"])
    if filters.get("department"):
        query = query.filter(Registry.reporting_department == filters["department"])
    if filters.get("age_group"):
        bounds = next((group for group in AGE_GROUPS if group[0] == filters["age_group"]), None)
        if bounds:
            _, start, end = bounds
            query = query.filter(Registry.age >= start)
            if end is not None:
                query = query.filter(Registry.age <= end)
    if filters.get("incident_recurrence") == "First-time":
        query = query.filter(Registry.is_first_incident.is_(True))
    if filters.get("incident_recurrence") == "Repeated":
        query = query.filter(or_(Registry.is_first_incident.is_(False), Registry.has_past_2_month_incident.is_(True)))
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


def _chart(chart_type, counter, labels=None, limit=None, index_axis=None):
    items = [(label, count) for label, count in counter.items() if label and count]
    if labels:
        items = [(label, counter.get(label, 0)) for label in labels if counter.get(label, 0)]
    else:
        items = sorted(items, key=lambda item: item[1], reverse=True)
    if limit:
        items = items[:limit]
    chart = {
        "type": chart_type,
        "labels": [label for label, _ in items],
        "values": [count for _, count in items],
    }
    if index_axis:
        chart["indexAxis"] = index_axis
    return chart


def _monthly_trend(records):
    counts = defaultdict(int)
    for registry in records:
        if registry.date_of_presentation:
            counts[registry.date_of_presentation.strftime("%Y-%m")] += 1
    labels = sorted(counts.keys())
    return {"type": "line", "labels": labels, "values": [counts[label] for label in labels]}


def _boolean_chart(records, field):
    counts = Counter()
    for registry in records:
        history = registry.psychiatric_history
        value = getattr(history, field, None) if history else None
        counts[_bool_label(value)] += 1
    return _chart("doughnut", counts)


def _table_rows(counter, limit=8):
    return [{"label": label, "count": count} for label, count in sorted(counter.items(), key=lambda item: item[1], reverse=True)[:limit] if label]


def _distinct_values(query, column):
    return [value for (value,) in query.with_entities(column).filter(column.is_not(None)).distinct().order_by(column).all() if value]


def _age_group(age):
    if age is None:
        return "Unspecified"
    for label, start, end in AGE_GROUPS:
        if age >= start and (end is None or age <= end):
            return label
    return "Unspecified"


def _is_repeated_incident(registry):
    return registry.is_first_incident is False or registry.has_past_2_month_incident is True or len(registry.incidents or []) > 1


def _method_label(method):
    return f"{method.icd10_code} {method.method_description}".strip() or method.method_category


def _incident_location(incident):
    parts = [incident.incident_region, incident.province_or_city, incident.municipality]
    return " / ".join(part for part in parts if part)


def _diagnosis_label(registry):
    diagnosis = registry.diagnosis_disposition
    if not diagnosis:
        return "Unspecified"
    return diagnosis.primary_diagnosis_code or diagnosis.secondary_diagnosis_code or "Unspecified"


def _disposition_label(registry):
    diagnosis = registry.diagnosis_disposition
    if not diagnosis:
        return "Unspecified"
    return _with_other(diagnosis.disposition, diagnosis.disposition_other) or "Unspecified"


def _with_other(value, other):
    if (value or "").lower() == "other" and other:
        return other
    return value or ""


def _bool_label(value):
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "Unspecified"


def _top_label(counter):
    if not counter:
        return "No data"
    return counter.most_common(1)[0][0] or "No data"


def _clean(value):
    value = (value or "").strip()
    return value or None


def _clean_choice(value, choices, default):
    value = (value or "").strip().lower()
    return value if value in choices else default


def _parse_date(value):
    value = _clean(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
