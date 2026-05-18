from flask import current_app

from app.models.hospital import Hospital


def get_configured_hospital():
    hospital_code = current_app.config.get("INITIAL_HOSPITAL_CODE")
    if hospital_code:
        hospital = Hospital.query.filter_by(hospital_code=hospital_code).first()
        if hospital:
            return hospital

    return Hospital.query.order_by(Hospital.id.asc()).first()


def get_configured_hospital_code():
    hospital = get_configured_hospital()
    if hospital:
        return hospital.hospital_code

    return current_app.config.get("INITIAL_HOSPITAL_CODE") or ""
