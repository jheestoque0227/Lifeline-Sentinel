from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models.hospital import Hospital


def active_hospitals():
    return Hospital.query.filter(Hospital.deleted_at.is_(None)).order_by(Hospital.hospital_name.asc()).all()


def hospital_display_label(hospital_code):
    if not hospital_code:
        return ""
    hospital = Hospital.query.filter(Hospital.hospital_code == hospital_code).first()
    if not hospital:
        return hospital_code
    return f"{hospital.hospital_code} - {hospital.hospital_name}"


def hospital_filter_choices(hospital_codes):
    codes = [code for code in hospital_codes if code]
    if not codes:
        return []

    hospitals = Hospital.query.filter(Hospital.hospital_code.in_(codes)).all()
    labels = {
        hospital.hospital_code: f"{hospital.hospital_code} - {hospital.hospital_name}"
        for hospital in hospitals
    }
    return [(code, labels.get(code, code)) for code in codes]


def user_has_all_hospitals(user):
    return not getattr(user, "hospital_id", None)


def get_user_hospital_code(user):
    if user_has_all_hospitals(user):
        return None
    hospital = getattr(user, "hospital", None)
    if hospital and not hospital.deleted_at:
        return hospital.hospital_code
    return None


def get_hospital_or_404(hospital_id, include_deleted=False):
    query = Hospital.query
    if not include_deleted:
        query = query.filter(Hospital.deleted_at.is_(None))
    return query.filter(Hospital.id == hospital_id).first_or_404()


def create_hospital_from_form(form):
    hospital = Hospital()
    update_hospital_from_form(hospital, form)
    db.session.add(hospital)
    return hospital


def update_hospital_from_form(hospital, form):
    hospital_code = (form.get("hospital_code") or "").strip().upper()
    hospital_name = (form.get("hospital_name") or "").strip()
    if not hospital_code:
        raise ValueError("Hospital code is required.")
    if not hospital_name:
        raise ValueError("Hospital name is required.")
    duplicate = (
        Hospital.query.filter(Hospital.hospital_code == hospital_code)
        .filter(Hospital.id != (hospital.id or 0))
        .first()
    )
    if duplicate:
        raise ValueError("Hospital code is already in use.")
    hospital.hospital_code = hospital_code
    hospital.hospital_name = hospital_name
    return hospital


def soft_delete_hospital(hospital, user, remarks=None):
    hospital.deleted_at = datetime.utcnow()
    hospital.deleted_remarks = (remarks or "").strip() or None
    return hospital


def get_configured_hospital(user=None):
    if user is not None and not user_has_all_hospitals(user) and getattr(user, "hospital", None) and not user.hospital.deleted_at:
        return user.hospital

    hospital_code = current_app.config.get("INITIAL_HOSPITAL_CODE")
    if hospital_code:
        hospital = Hospital.query.filter_by(hospital_code=hospital_code, deleted_at=None).first()
        if hospital:
            return hospital

    return Hospital.query.filter(Hospital.deleted_at.is_(None)).order_by(Hospital.id.asc()).first()


def get_configured_hospital_code(user=None):
    hospital = get_configured_hospital(user)
    if hospital:
        return hospital.hospital_code

    return current_app.config.get("INITIAL_HOSPITAL_CODE") or ""
