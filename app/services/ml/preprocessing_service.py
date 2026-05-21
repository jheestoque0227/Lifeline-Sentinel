from collections import Counter

import pandas as pd


RISK_LABELS = ["Low", "Moderate", "High"]
IDENTIFIER_COLUMNS = {
    "id",
    "registry_code",
    "patient_identifier",
    "data_steward_code",
    "created_by",
    "updated_by",
    "deleted_by",
    "remarks",
    "incident_remarks",
    "notes",
}


CLASSIFICATION_FEATURES = [
    "age_group",
    "sex",
    "gender_identity",
    "civil_status",
    "education",
    "employment",
    "incident_method",
    "incident_location",
    "incident_time",
    "previous_consultation",
    "family_history",
    "substance_use",
    "psychiatric_diagnosis",
    "previous_repeated_incidents",
    "disposition",
]

CLUSTERING_FEATURES = CLASSIFICATION_FEATURES + [
    "age",
    "incident_count",
    "method_count",
    "substance_count",
    "has_high_lethality_method",
]


def build_registry_frame(records):
    rows = [_feature_row(registry) for registry in records]
    return pd.DataFrame(rows)


def classification_features(frame):
    return [column for column in CLASSIFICATION_FEATURES if column in frame.columns and column not in IDENTIFIER_COLUMNS]


def clustering_features(frame):
    return [column for column in CLUSTERING_FEATURES if column in frame.columns and column not in IDENTIFIER_COLUMNS]


def encoded_frame(frame, feature_columns):
    if frame.empty or not feature_columns:
        return pd.DataFrame()
    working = frame[feature_columns].copy()
    for column in working.columns:
        if pd.api.types.is_numeric_dtype(working[column]):
            working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0)
        else:
            working[column] = working[column].fillna("Unspecified").astype(str)
    return pd.get_dummies(working, dummy_na=False)


def readiness_summary(frame):
    total = int(len(frame))
    labeled = int(frame["risk_label"].notna().sum()) if "risk_label" in frame.columns else 0
    incident_dates = int(frame["first_incident_date"].notna().sum()) if "first_incident_date" in frame.columns else 0
    feature_columns = classification_features(frame)
    return {
        "total_records": total,
        "labeled_risk_records": labeled,
        "incident_date_records": incident_dates,
        "target_exists": "risk_label" in frame.columns,
        "feature_columns_present": bool(feature_columns),
        "identifier_fields_excluded": True,
        "missing_values_handled": True,
        "features_used": feature_columns,
        "excluded_fields": sorted(IDENTIFIER_COLUMNS),
    }


def risk_profile_rows(frame, predictions=None, probabilities=None, limit=10):
    rows = []
    if frame.empty:
        return rows
    for index, row in frame.head(limit).iterrows():
        probability = probabilities.get(index) if probabilities else None
        rows.append(
            {
                "registry_code": row.get("registry_code", "Masked"),
                "age_group": row.get("age_group", "Unspecified"),
                "sex": row.get("sex", "Unspecified"),
                "incident_count": int(row.get("incident_count") or 0),
                "substance_use": row.get("substance_use", "Unspecified"),
                "profile": predictions.loc[index] if hasattr(predictions, "loc") else row.get("risk_label", "Unspecified"),
                "probability": probability,
            }
        )
    return rows


def describe_cluster(group):
    repeated_rate = _rate((group["previous_repeated_incidents"] == "Repeated").sum(), len(group))
    substance_rate = _rate((group["substance_use"] == "Yes").sum(), len(group))
    home_rate = _rate(group["incident_location"].astype(str).str.contains("home|house|residence", case=False, na=False).sum(), len(group))
    median_age = float(group["age"].median()) if "age" in group and not group["age"].empty else 0

    if repeated_rate >= 50 or substance_rate >= 50:
        label = "Repeated incident with behavioral risk factors"
    elif home_rate >= 50:
        label = "Home-based self-harm pattern"
    elif median_age <= 24 and repeated_rate < 50:
        label = "Younger first-time incident profile"
    else:
        label = "Mixed demographic and incident profile"

    characteristics = [
        f"Most common sex: {_top(group['sex'])}",
        f"Common method category: {_top(group['incident_method'])}",
        f"Common location: {_top(group['incident_location'])}",
        f"Repeated incident share: {repeated_rate}%",
        f"Substance use share: {substance_rate}%",
    ]
    return label, characteristics


def _feature_row(registry):
    history = registry.psychiatric_history
    diagnosis = registry.diagnosis_disposition
    incidents = list(registry.incidents or [])
    methods = [method for incident in incidents for method in incident.methods]
    first_incident = incidents[0] if incidents else None
    method_categories = [method.method_category for method in methods if method.method_category]
    method_codes = {method.icd10_code for method in methods if method.icd10_code}
    first_date = first_incident.incident_date if first_incident else registry.date_of_presentation
    return {
        "registry_code": registry.registry_code,
        "age": registry.age,
        "age_group": _age_group(registry.age),
        "sex": registry.sex_at_birth or "Unspecified",
        "gender_identity": _with_other(registry.gender_identity, registry.gender_identity_other),
        "civil_status": registry.marital_status or "Unspecified",
        "education": registry.highest_educational_attainment or "Unspecified",
        "employment": registry.employment_status or "Unspecified",
        "incident_method": _top(method_categories),
        "incident_location": _incident_location(first_incident),
        "incident_time": first_incident.incident_time_range if first_incident and first_incident.incident_time_range else "Unspecified",
        "previous_consultation": _bool_label(history.previous_consultation if history else None),
        "family_history": _bool_label(history.family_history if history else None),
        "substance_use": _bool_label(history.substance_use if history else None),
        "psychiatric_diagnosis": _diagnosis_label(diagnosis),
        "previous_repeated_incidents": "Repeated" if _is_repeated(registry) else "First-time",
        "disposition": _with_other(diagnosis.disposition, diagnosis.disposition_other) if diagnosis else "Unspecified",
        "incident_count": len(incidents),
        "method_count": len(methods),
        "substance_count": len(history.substances or []) if history else 0,
        "has_high_lethality_method": int(bool(method_codes.intersection({"X70", "X72", "X73", "X74", "X80", "X81", "X82"}))),
        "first_incident_date": first_date,
        "risk_label": _derived_risk_label(registry),
    }


def _derived_risk_label(registry):
    history = registry.psychiatric_history
    diagnosis = registry.diagnosis_disposition
    methods = [method for incident in (registry.incidents or []) for method in incident.methods]
    method_codes = {method.icd10_code for method in methods}
    score = 0
    score += 2 if registry.is_first_incident is False else 0
    score += 2 if registry.has_past_2_month_incident is True else 0
    score += 1 if len(registry.incidents or []) > 1 else 0
    score += 2 if method_codes.intersection({"X70", "X72", "X73", "X74", "X80", "X81", "X82"}) else 0
    score += 1 if history and history.previous_consultation is True else 0
    score += 1 if history and history.family_history is True else 0
    score += 1 if history and history.friends_history is True else 0
    score += 1 if history and history.substance_use is True else 0
    score += 1 if diagnosis and diagnosis.primary_diagnosis_code in {"F32", "F33", "F60"} else 0
    score += 2 if diagnosis and diagnosis.disposition in {"Admitted to hospital", "Died", "Transfer to another facility"} else 0
    if score >= 5:
        return "High"
    if score >= 2:
        return "Moderate"
    return "Low"


def _age_group(age):
    if age is None:
        return "Unspecified"
    if age <= 14:
        return "0-14"
    if age <= 24:
        return "15-24"
    if age <= 44:
        return "25-44"
    if age <= 64:
        return "45-64"
    return "65+"


def _is_repeated(registry):
    return registry.is_first_incident is False or registry.has_past_2_month_incident is True or len(registry.incidents or []) > 1


def _incident_location(incident):
    if not incident:
        return "Unspecified"
    place = _with_other(incident.incident_place, incident.incident_place_other)
    parts = [place, incident.incident_region, incident.province_or_city, incident.municipality]
    return " / ".join(part for part in parts if part and part != "Unspecified") or "Unspecified"


def _diagnosis_label(diagnosis):
    if not diagnosis:
        return "Unspecified"
    return diagnosis.primary_diagnosis_code or diagnosis.secondary_diagnosis_code or "Unspecified"


def _with_other(value, other):
    if (value or "").lower() in {"other", "others"} and other:
        return other
    return value or "Unspecified"


def _bool_label(value):
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "Unspecified"


def _top(values):
    values = [value for value in values if value]
    if hasattr(values, "tolist"):
        values = values.tolist()
    values = [str(value) for value in values if str(value)]
    return Counter(values).most_common(1)[0][0] if values else "Unspecified"


def _rate(numerator, denominator):
    if not denominator:
        return 0
    return int(round(float(numerator) / float(denominator) * 100))

