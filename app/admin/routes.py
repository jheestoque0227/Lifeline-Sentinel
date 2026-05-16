from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.auth.decorators import role_required
from app.models.user import User
from app.services.audit import record_audit
from app.services.email import send_initial_password_email, send_password_reset_email
from app.services.users import (
    ROLES,
    commit_or_raise_duplicate,
    create_user_from_form,
    deactivate_user,
    generate_initial_password,
    reactivate_user,
    update_user_from_form,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@role_required("Admin")
def users():
    users = User.query.order_by(User.role, User.full_name).all()
    return render_template("admin/users.html", users=users, roles=ROLES)


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
    user = User.query.get_or_404(user_id)

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
    user = User.query.get_or_404(user_id)
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
    user = User.query.get_or_404(user_id)
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


@admin_bp.route("/users/<int:user_id>/send-reset", methods=["POST"])
@login_required
@role_required("Admin")
def send_reset(user_id):
    user = User.query.get_or_404(user_id)
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
        "role": user.role,
        "is_active_user": user.is_active_user,
    }
