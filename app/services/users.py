from datetime import datetime
import secrets
import string

from email_validator import EmailNotValidError, validate_email
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.hospital import Hospital
from app.models.user import User


ROLES = ("Admin", "Encoder", "Analyst")


def user_query(include_deleted=False):
    query = User.query
    if not include_deleted:
        query = query.filter(User.deleted_at.is_(None))
    return query


def generate_initial_password(length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(character.islower() for character in password)
            and any(character.isupper() for character in password)
            and any(character.isdigit() for character in password)
            and any(character in "!@#$%&*" for character in password)
        ):
            return password


def validate_user_form(form):
    errors = []
    employee_no = form.get("employee_no", "").strip()
    full_name = form.get("full_name", "").strip()
    username = form.get("username", "").strip()
    email = form.get("email", "").strip()
    hospital_id = form.get("hospital_id", "").strip()
    role = form.get("role", "")

    if not employee_no:
        errors.append("Employee number is required.")
    elif not employee_no.isdigit():
        errors.append("Employee number must contain numbers only.")
    if not full_name:
        errors.append("Full name is required.")
    if not username:
        errors.append("Username is required.")
    if role not in ROLES:
        errors.append("Invalid role selected.")
    if hospital_id != "__all__" and (not hospital_id.isdigit() or not Hospital.query.filter(Hospital.id == int(hospital_id), Hospital.deleted_at.is_(None)).first()):
        errors.append("Select an active hospital.")
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        errors.append("Email must be a valid email address.")

    if errors:
        raise ValueError(" ".join(errors))


def update_user_from_form(user, form):
    validate_user_form(form)
    user.employee_no = form.get("employee_no", "").strip()
    user.full_name = form.get("full_name", "").strip()
    user.email = validate_email(form.get("email", "").strip(), check_deliverability=False).normalized.lower()
    user.username = form.get("username", "").strip()
    hospital_id = form.get("hospital_id", "").strip()
    user.hospital_id = None if hospital_id == "__all__" else int(hospital_id)
    user.role = form.get("role")
    return user


def create_user_from_form(form, initial_password):
    user = User()
    update_user_from_form(user, form)
    user.is_active_user = True
    user.deleted_at = None
    user.set_password(initial_password)
    return user


def deactivate_user(user):
    user.is_active_user = False
    user.deactivated_at = datetime.utcnow()


def reactivate_user(user):
    user.is_active_user = True
    user.deactivated_at = None


def soft_delete_user(user, actor, remarks=None):
    user.is_active_user = False
    user.deactivated_at = datetime.utcnow()
    user.deleted_at = datetime.utcnow()
    user.deleted_remarks = (remarks or "").strip() or None
    user.active_session_id = None
    user.active_session_started_at = None
    user.active_session_last_seen_at = None
    return user


def commit_or_raise_duplicate():
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("Employee number, email, or username is already in use.") from exc
