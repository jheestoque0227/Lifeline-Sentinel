from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.auth.decorators import role_required
from app.models.user import User
from app.services.audit import record_audit
from app.services.email import send_initial_password_email, send_password_reset_email
from app.services.hospitals import (
    active_hospitals,
    create_hospital_from_form,
    get_hospital_or_404,
    soft_delete_hospital,
    update_hospital_from_form,
)
from app.services.users import (
    ROLES,
    commit_or_raise_duplicate,
    create_user_from_form,
    deactivate_user,
    generate_initial_password,
    reactivate_user,
    soft_delete_user,
    update_user_from_form,
    user_query,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@role_required("Admin")
def users():
    users = user_query().order_by(User.role, User.full_name).all()
    return render_template("admin/users.html", users=users, roles=ROLES, hospitals=active_hospitals())


@admin_bp.route("/hospitals")
@login_required
@role_required("Admin")
def hospitals():
    from app.models.hospital import Hospital

    hospitals = Hospital.query.filter(Hospital.deleted_at.is_(None)).order_by(Hospital.hospital_name.asc()).all()
    return render_template("admin/hospitals.html", hospitals=hospitals)


@admin_bp.route("/hospitals/create", methods=["POST"])
@login_required
@role_required("Admin")
def create_hospital():
    try:
        hospital = create_hospital_from_form(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.hospitals"))

    record_audit(
        "create_hospital",
        "admin",
        remarks=f"Created hospital {hospital.hospital_code}.",
        new_values=_hospital_snapshot(hospital),
    )
    db.session.commit()
    flash("Hospital created.", "success")
    return redirect(url_for("admin.hospitals"))


@admin_bp.route("/hospitals/<int:hospital_id>/update", methods=["POST"])
@login_required
@role_required("Admin")
def update_hospital(hospital_id):
    hospital = get_hospital_or_404(hospital_id)
    old_values = _hospital_snapshot(hospital)
    try:
        update_hospital_from_form(hospital, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.hospitals"))

    record_audit(
        "update_hospital",
        "admin",
        remarks=f"Updated hospital {hospital.hospital_code}.",
        old_values=old_values,
        new_values=_hospital_snapshot(hospital),
    )
    db.session.commit()
    flash("Hospital updated.", "success")
    return redirect(url_for("admin.hospitals"))


@admin_bp.route("/hospitals/<int:hospital_id>/delete", methods=["POST"])
@login_required
@role_required("Admin")
def delete_hospital(hospital_id):
    hospital = get_hospital_or_404(hospital_id)
    old_values = _hospital_snapshot(hospital)
    soft_delete_hospital(hospital, current_user, request.form.get("deleted_remarks"))
    record_audit(
        "delete_hospital",
        "admin",
        remarks=f"Soft deleted hospital {hospital.hospital_code}.",
        old_values=old_values,
        new_values=_hospital_snapshot(hospital),
    )
    db.session.commit()
    flash("Hospital deleted.", "success")
    return redirect(url_for("admin.hospitals"))


@admin_bp.route("/users/create", methods=["POST"])
@login_required
@role_required("Admin")
def create_user():
    initial_password = generate_initial_password()
    try:
        user = create_user_from_form(request.form, initial_password)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.users"))

    db.session.add(user)
    record_audit(
        "create_user",
        "admin",
        remarks=f"Created user {user.username}.",
        new_values=_user_snapshot(user),
    )
    try:
        commit_or_raise_duplicate()
    except ValueError as exc:
        flash(str(exc), "danger")
    else:
        email_result = send_initial_password_email(user, initial_password)
        flash(
            "User account created and initial password sent by email."
            if email_result
            else f"User account created, but email could not be sent. {email_result.error}",
            "success" if email_result else "warning",
        )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/update", methods=["POST"])
@login_required
@role_required("Admin")
def update_user(user_id):
    user = user_query().filter(User.id == user_id).first_or_404()

    old_values = _user_snapshot(user)
    try:
        update_user_from_form(user, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.users"))
    new_password = request.form.get("password", "")
    if new_password:
        if len(new_password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("admin.users"))
        user.set_password(new_password)

    record_audit(
        "update_user",
        "admin",
        remarks=f"Updated user {user.username}.",
        old_values=old_values,
        new_values=_user_snapshot(user),
    )
    try:
        commit_or_raise_duplicate()
    except ValueError as exc:
        flash(str(exc), "danger")
    else:
        flash("User account updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
@role_required("Admin")
def deactivate(user_id):
    user = user_query().filter(User.id == user_id).first_or_404()
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.users"))

    old_values = _user_snapshot(user)
    deactivate_user(user)
    record_audit(
        "deactivate_user",
        "admin",
        remarks=f"Deactivated user {user.username}.",
        old_values=old_values,
        new_values=_user_snapshot(user),
    )
    db.session.commit()
    flash("User account deactivated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reactivate", methods=["POST"])
@login_required
@role_required("Admin")
def reactivate(user_id):
    user = user_query().filter(User.id == user_id).first_or_404()
    old_values = _user_snapshot(user)
    reactivate_user(user)
    record_audit(
        "reactivate_user",
        "admin",
        remarks=f"Reactivated user {user.username}.",
        old_values=old_values,
        new_values=_user_snapshot(user),
    )
    db.session.commit()
    flash("User account reactivated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("Admin")
def delete_user(user_id):
    user = user_query().filter(User.id == user_id).first_or_404()
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users"))

    old_values = _user_snapshot(user)
    soft_delete_user(user, current_user, request.form.get("deleted_remarks"))
    record_audit(
        "delete_user",
        "admin",
        remarks=f"Soft deleted user {user.username}.",
        old_values=old_values,
        new_values=_user_snapshot(user),
    )
    db.session.commit()
    flash("User account deleted.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/send-reset", methods=["POST"])
@login_required
@role_required("Admin")
def send_reset(user_id):
    user = user_query().filter(User.id == user_id).first_or_404()
    if not user.is_active_user:
        flash("Only active users can receive password reset email.", "danger")
        return redirect(url_for("admin.users"))

    email_result = send_password_reset_email(user)
    record_audit(
        "reset_password_requested",
        "admin",
        remarks=f"Admin sent password reset email to {user.username}.",
        new_values={"target_user_id": user.id, "email_sent": bool(email_result), "email_error": email_result.error},
    )
    db.session.commit()
    flash(
        "Password reset email sent."
        if email_result
        else f"Password reset email was not sent. {email_result.error}",
        "info" if email_result else "warning",
    )
    return redirect(url_for("admin.users"))


def _user_snapshot(user):
    return {
        "id": user.id,
        "employee_no": user.employee_no,
        "full_name": user.full_name,
        "email": user.email,
        "username": user.username,
        "hospital_id": user.hospital_id,
        "hospital_code": user.hospital.hospital_code if user.hospital else "All Hospitals",
        "role": user.role,
        "is_active_user": user.is_active_user,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
        "deleted_remarks": user.deleted_remarks,
    }


def _hospital_snapshot(hospital):
    return {
        "id": hospital.id,
        "hospital_code": hospital.hospital_code,
        "hospital_name": hospital.hospital_name,
        "deleted_at": hospital.deleted_at.isoformat() if hospital.deleted_at else None,
        "deleted_remarks": hospital.deleted_remarks,
    }
