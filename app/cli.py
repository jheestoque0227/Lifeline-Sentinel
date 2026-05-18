from datetime import date, datetime, time, timedelta
import random

import click
from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import (
    CaseAscertainment,
    DiagnosisDisposition,
    PhilippineCityMunicipality,
    PhilippineProvince,
    PhilippineRegion,
    PsychiatricHistory,
    Registry,
    RegistryIncident,
    RegistryIncidentMethod,
    User,
)
from app.models.hospital import Hospital
from app.registry import options


def register_cli(app):
    app.cli.add_command(seed_registry_command)


@click.command("seed-registry")
@click.option("--count", default=100, show_default=True, type=int, help="Minimum number of dummy registry entries to keep available.")
def seed_registry_command(count):
    """Create or refresh synthetic registry records for local testing."""
    if count < 1:
        raise click.ClickException("Count must be at least 1.")

    actor = (
        User.query.filter(User.role.in_(["Admin", "Encoder"]), User.is_active_user.is_(True))
        .order_by(User.id.asc())
        .first()
    )
    if not actor:
        raise click.ClickException("No active Admin or Encoder user found. Create a user before seeding registry data.")

    hospital_code = _seed_hospital_code()
    rng = random.Random(20260518)

    locations = _location_choices()
    existing = (
        Registry.query.filter(Registry.registry_code.like("DUMMY-%"))
        .order_by(Registry.registry_code.asc())
        .all()
    )

    for index, registry in enumerate(existing, start=1):
        _apply_dummy_registry(registry, index, actor, hospital_code, rng, locations)

    missing = max(0, count - len(existing))
    latest_sequence = _latest_dummy_sequence()
    new_registries = []
    for offset in range(1, missing + 1):
        sequence = latest_sequence + offset
        registry = Registry(
            registry_code=f"DUMMY-{sequence:05d}",
            patient_identifier=f"DUMMY-HN-{sequence:05d}",
            created_by=actor.id,
            created_at=datetime.utcnow(),
        )
        _apply_dummy_registry(registry, len(existing) + offset, actor, hospital_code, rng, locations)
        new_registries.append(registry)

    db.session.add_all(new_registries)
    db.session.commit()
    click.echo(
        f"Refreshed {len(existing)} existing dummy registry entries and created {missing}; "
        f"{len(existing) + missing} dummy entries are available using hospital code {hospital_code}."
    )


def _apply_dummy_registry(registry, index, actor, hospital_code, rng, locations):
    presentation_date = date.today() - timedelta(days=rng.randint(0, 365))
    age = rng.randint(12, 82)
    has_past_incident = rng.choice([True, False])

    registry.data_steward_code = actor.employee_no
    registry.hospital_code = hospital_code
    registry.date_of_presentation = presentation_date
    registry.time_of_presentation = time(rng.randint(0, 23), rng.choice([0, 5, 10, 15, 20, 30, 45]))
    registry.reporting_department = rng.choice(["ER", "OPS"])
    registry.is_valid_registry_case = True
    registry.invalid_reason = None
    registry.risk_level = None
    registry.is_first_incident = rng.choice([True, False])
    registry.has_past_2_month_incident = has_past_incident
    registry.patient_identifier = registry.patient_identifier or f"DUMMY-HN-{index:05d}"
    registry.age = age
    registry.sex_at_birth = rng.choice(["Female", "Male"])
    registry.sexual_orientation = rng.choice(options.SEXUAL_ORIENTATIONS[:-1])
    registry.sexual_orientation_other = None
    registry.gender_identity = rng.choice(options.GENDER_IDENTITIES[:-1])
    registry.gender_identity_other = None
    registry.marital_status = rng.choice(options.MARITAL_STATUSES)
    registry.highest_educational_attainment = rng.choice(options.EDUCATIONAL_ATTAINMENTS)
    registry.employment_status = rng.choice(options.EMPLOYMENT_STATUSES)
    registry.nationality = "Filipino"
    registry.religion = rng.choice(options.RELIGIONS[:-1])
    registry.religion_other = None
    registry.deleted_at = None
    registry.deleted_by = None
    registry.deleted_remarks = None
    registry.updated_at = datetime.utcnow()

    registry.case_ascertainment = registry.case_ascertainment or CaseAscertainment(registry=registry)
    registry.case_ascertainment.intent = "Intentional"
    registry.case_ascertainment.infliction = "Self-inflicted"
    registry.case_ascertainment.type_of_consult = rng.choice(options.TYPE_OF_CONSULTS[:-1])
    registry.case_ascertainment.type_of_consult_other = None

    registry.incidents = [
        _build_dummy_incident(rng, locations, presentation_date, "Current synthetic incident")
    ]
    if has_past_incident:
        registry.incidents.append(
            _build_dummy_incident(rng, locations, presentation_date - timedelta(days=rng.randint(15, 55)), "Past 2-month synthetic incident")
        )

    substance_use = rng.choice([True, False])
    selected_substances = rng.sample(options.SUBSTANCES, rng.randint(1, min(3, len(options.SUBSTANCES)))) if substance_use else []
    registry.psychiatric_history = registry.psychiatric_history or PsychiatricHistory(registry=registry)
    registry.psychiatric_history.previous_consultation = rng.choice([True, False])
    registry.psychiatric_history.previous_consultation_notes = _optional_note(rng, "Previous consultation documented in synthetic data.")
    registry.psychiatric_history.family_history = rng.choice([True, False])
    registry.psychiatric_history.family_history_notes = _optional_note(rng, "Family history noted in synthetic data.")
    registry.psychiatric_history.friends_history = rng.choice([True, False])
    registry.psychiatric_history.friends_history_notes = _optional_note(rng, "Peer or colleague history noted in synthetic data.")
    registry.psychiatric_history.substance_use = substance_use
    registry.psychiatric_history.substances = selected_substances
    registry.psychiatric_history.substance_details = {
        substance: f"Synthetic {substance.lower()} type"
        for substance in selected_substances
    }
    registry.psychiatric_history.substance_notes = "Synthetic substance use remarks." if substance_use else None

    registry.diagnosis_disposition = registry.diagnosis_disposition or DiagnosisDisposition(registry=registry)
    registry.diagnosis_disposition.primary_diagnosis_code = rng.choice(["F32", "F33", "F41", "F43", "F60", None])
    registry.diagnosis_disposition.secondary_diagnosis_code = rng.choice(["F10", "F19", "F41", None])
    registry.diagnosis_disposition.disposition = rng.choice(options.DISPOSITIONS[:-1])
    registry.diagnosis_disposition.disposition_other = None
    registry.diagnosis_disposition.remarks = "Synthetic diagnosis/disposition note."


def _build_dummy_incident(rng, locations, presentation_date, remarks):
    location = rng.choice(locations)
    incident_date = presentation_date - timedelta(days=rng.randint(0, 7))
    incident = RegistryIncident(
        incident_date=incident_date,
        incident_day=incident_date.strftime("%A"),
        incident_time_range=rng.choice(options.INCIDENT_TIME_PERIODS),
        incident_place=rng.choice(options.INCIDENT_PLACES[:-1]),
        incident_region=location["region"],
        province_or_city=location["province"],
        municipality=location["city_municipality"],
        remarks=remarks,
    )

    poisoning_methods = rng.sample(options.SELF_POISONING_METHODS, rng.randint(0, 2))
    harm_methods = rng.sample(options.SELF_HARM_METHODS, rng.randint(0, 2))
    if not poisoning_methods and not harm_methods:
        harm_methods = [rng.choice(options.SELF_HARM_METHODS)]

    for method in poisoning_methods:
        incident.methods.append(_dummy_incident_method(method, "Self-poisoning"))
    for method in harm_methods:
        incident.methods.append(_dummy_incident_method(method, "Self-harm"))
    return incident


def _dummy_incident_method(method, category):
    code, description = method.split(" ", 1)
    return RegistryIncidentMethod(
        icd10_code=code,
        method_category=category,
        method_description=description,
        specify_notes="Synthetic method note.",
    )


def _optional_note(rng, note):
    return note if rng.choice([True, False]) else None


def _location_choices():
    rows = (
        db.session.query(
            PhilippineRegion.region_name,
            PhilippineProvince.province_name,
            PhilippineCityMunicipality.city_municipality_name,
        )
        .join(PhilippineProvince, PhilippineProvince.region_id == PhilippineRegion.id)
        .join(PhilippineCityMunicipality, PhilippineCityMunicipality.province_id == PhilippineProvince.id)
        .all()
    )
    if rows:
        return [
            {"region": region, "province": province, "city_municipality": city_municipality}
            for region, province, city_municipality in rows
        ]
    return [
        {"region": "National Capital Region (NCR)", "province": "Metro Manila", "city_municipality": "Quezon City"},
        {"region": "Region XI (Davao Region)", "province": "Davao del Sur", "city_municipality": "City of Digos"},
    ]


def _seed_hospital_code():
    try:
        configured_code = current_app.config.get("INITIAL_HOSPITAL_CODE")
        if configured_code:
            hospital = Hospital.query.filter_by(hospital_code=configured_code).first()
            if hospital:
                return hospital.hospital_code

        hospital = Hospital.query.order_by(Hospital.id.asc()).first()
        if hospital:
            return hospital.hospital_code
    except SQLAlchemyError:
        db.session.rollback()

    return current_app.config.get("INITIAL_HOSPITAL_CODE") or "DUMMY-HOSP"


def _latest_dummy_sequence():
    latest_sequence = 0
    codes = (
        db.session.query(Registry.registry_code)
        .filter(Registry.registry_code.like("DUMMY-%"))
        .all()
    )
    for (code,) in codes:
        try:
            latest_sequence = max(latest_sequence, int(code.rsplit("-", 1)[1]))
        except (IndexError, ValueError, TypeError):
            continue
    return latest_sequence
