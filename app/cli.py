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
@click.option("--count", default=100, show_default=True, type=int, help="Number of dummy registry entries to create.")
def seed_registry_command(count):
    """Create synthetic registry records for local testing."""
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
    prefix = f"DUMMY-{datetime.utcnow().strftime('%Y%m%d')}-"
    latest_sequence = _latest_dummy_sequence(prefix)
    rng = random.Random(20260518)

    registries = []
    for index in range(1, count + 1):
        sequence = latest_sequence + index
        presentation_date = date.today() - timedelta(days=rng.randint(0, 180))
        age = rng.randint(12, 82)
        patient_number = f"DUMMY-HN-{sequence:05d}"

        registry = Registry(
            registry_code=f"{prefix}{sequence:05d}",
            data_steward_code=actor.employee_no,
            hospital_code=hospital_code,
            date_of_presentation=presentation_date,
            time_of_presentation=time(rng.randint(0, 23), rng.choice([0, 5, 10, 15, 20, 30, 45])),
            reporting_department=rng.choice(["ER", "OPS"]),
            is_valid_registry_case=True,
            invalid_reason=None,
            is_first_incident=rng.choice([True, False]),
            has_past_2_month_incident=rng.choice([True, False, None]),
            patient_identifier=patient_number,
            age=age,
            sex_at_birth=rng.choice(options.SEX_AT_BIRTH[:2]),
            sexual_orientation=rng.choice(options.SEXUAL_ORIENTATIONS[:-1]),
            gender_identity=rng.choice(options.GENDER_IDENTITIES[:-1]),
            marital_status=rng.choice(options.MARITAL_STATUSES),
            highest_educational_attainment=rng.choice(options.EDUCATIONAL_ATTAINMENTS),
            employment_status=rng.choice(options.EMPLOYMENT_STATUSES),
            nationality="Filipino",
            religion=rng.choice(options.RELIGIONS[:-1]),
            created_by=actor.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        registry.case_ascertainment = CaseAscertainment(
            intent="Intentional",
            infliction="Self-inflicted",
            type_of_consult=rng.choice(options.TYPE_OF_CONSULTS[:-1]),
        )

        poisoning_methods = rng.sample(options.SELF_POISONING_METHODS, rng.randint(0, 2))
        harm_methods = rng.sample(options.SELF_HARM_METHODS, rng.randint(0, 2))
        if not poisoning_methods and not harm_methods:
            harm_methods = [rng.choice(options.SELF_HARM_METHODS)]

        incident = RegistryIncident(
                incident_date=presentation_date - timedelta(days=rng.randint(0, 7)),
                incident_day=rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
                incident_time_range=rng.choice(options.INCIDENT_TIME_PERIODS),
                incident_place=rng.choice(options.INCIDENT_PLACES[:-1]),
                incident_region="Region XI",
                province_or_city=rng.choice(["Davao City", "Davao del Sur", "Davao del Norte"]),
                municipality=rng.choice(["Poblacion", "Buhangin", "Toril", "Calinan"]),
                remarks="Synthetic registry seed data for testing.",
            )
        for method in poisoning_methods:
            code, description = method.split(" ", 1)
            incident.methods.append(RegistryIncidentMethod(icd10_code=code, method_category="Self-poisoning", method_description=description, specify_notes="Synthetic method note"))
        for method in harm_methods:
            code, description = method.split(" ", 1)
            incident.methods.append(RegistryIncidentMethod(icd10_code=code, method_category="Self-harm", method_description=description, specify_notes="Synthetic method note"))
        registry.incidents.append(incident)

        substance_use = rng.choice([True, False])
        selected_substances = rng.sample(options.SUBSTANCES, rng.randint(1, 2)) if substance_use else []
        registry.psychiatric_history = PsychiatricHistory(
            previous_consultation=rng.choice([True, False]),
            previous_consultation_notes="Synthetic previous consultation note." if rng.choice([True, False]) else None,
            family_history=rng.choice([True, False]),
            family_history_notes="Synthetic family history note." if rng.choice([True, False]) else None,
            friends_history=rng.choice([True, False]),
            friends_history_notes="Synthetic peer history note." if rng.choice([True, False]) else None,
            substance_use=substance_use,
            substances=selected_substances,
            substance_details={substance: "Synthetic type" for substance in selected_substances},
            substance_notes="Synthetic substance note." if substance_use else None,
        )

        registry.diagnosis_disposition = DiagnosisDisposition(
            primary_diagnosis_code=rng.choice(["F32", "F33", "F41", "F43", "F60", None]),
            secondary_diagnosis_code=rng.choice(["F10", "F19", "F41", None]),
            disposition=rng.choice(options.DISPOSITIONS[:-1]),
            remarks="Synthetic diagnosis/disposition note.",
        )

        registries.append(registry)

    db.session.add_all(registries)
    db.session.commit()
    click.echo(f"Created {count} dummy registry entries using hospital code {hospital_code}.")


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


def _latest_dummy_sequence(prefix):
    latest_code = (
        db.session.query(func.max(Registry.registry_code))
        .filter(Registry.registry_code.like(f"{prefix}%"))
        .scalar()
    )
    if not latest_code:
        return 0
    try:
        return int(latest_code.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0
