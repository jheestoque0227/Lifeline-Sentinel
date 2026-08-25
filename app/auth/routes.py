from datetime import datetime

from flask import Blueprint, render_template, redirect, request, session, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models.user import User
from app.services.audit import record_audit
from app.services.email import send_mfa_code_email, send_password_reset_email, verify_reset_token
from app.services.mfa import (
    MFA_EXPIRES_MINUTES,
    clear_mfa_challenge,
    get_mfa_challenge,
    start_mfa_challenge,
    verify_mfa_code,
)
from app.services.sessions import (
    clear_session,
    clear_user_session,
    get_session_snapshot,
    start_login_session,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _redirect_for_role(user):
    if user.role == "Encoder":
        return redirect(url_for("registry.index"))
    return redirect(url_for("analytics.analytics_dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username, deleted_at=None).first()

        if not user or not user.is_active_user or user.deleted_at or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html", username=username)

        clear_session()
        code = start_mfa_challenge(user, remember=False)
        email_result = send_mfa_code_email(user, code, MFA_EXPIRES_MINUTES)
        record_audit(
            "mfa_code_sent",
            "auth",
            user=user,
            remarks="MFA verification code sent." if email_result else f"MFA verification code failed: {email_result.error}",
            new_values={"email_sent": bool(email_result), "email_error": email_result.error},
        )
        db.session.commit()
        if not email_result:
            clear_mfa_challenge()
            flash(f"Verification email could not be sent. {email_result.error}", "danger")
            return render_template("auth/login.html", username=username)

        flash("A verification code was sent to your email.", "info")
        return redirect(url_for("auth.mfa_verify"))

    return render_template("auth/login.html")


@auth_bp.route("/mfa", methods=["GET", "POST"])
def mfa_verify():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    challenge = get_mfa_challenge()
    if not challenge:
        flash("Your verification session expired. Please sign in again.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get(challenge["user_id"])
    if not user or not user.is_active_user or user.deleted_at:
        clear_mfa_challenge()
        flash("Unable to verify this account. Please sign in again.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        code = request.form.get("code", "")
        valid, error = verify_mfa_code(code)
        if not valid:
            flash(error, "danger")
            return render_template("auth/mfa.html", email=user.email, expires_minutes=MFA_EXPIRES_MINUTES)

        clear_session()
        login_user(user, remember=False)
        session_id = start_login_session(user)
        user.last_login_at = datetime.utcnow()
        record_audit(
            "login",
            "auth",
            user=user,
            remarks=f"User logged in after email MFA. Session ID: {session_id}",
            new_values=get_session_snapshot(),
        )
        db.session.commit()
        flash("Welcome back.", "success")
        return _redirect_for_role(user)

    return render_template("auth/mfa.html", email=user.email, expires_minutes=MFA_EXPIRES_MINUTES)


@auth_bp.route("/mfa/resend", methods=["POST"])
def mfa_resend():
    challenge = get_mfa_challenge()
    if not challenge:
        flash("Your verification session expired. Please sign in again.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get(challenge["user_id"])
    if not user or not user.is_active_user or user.deleted_at:
        clear_mfa_challenge()
        flash("Unable to verify this account. Please sign in again.", "danger")
        return redirect(url_for("auth.login"))

    code = start_mfa_challenge(user, remember=challenge.get("remember", False))
    email_result = send_mfa_code_email(user, code, MFA_EXPIRES_MINUTES)
    record_audit(
        "mfa_code_resent",
        "auth",
        user=user,
        remarks="MFA verification code resent." if email_result else f"MFA verification resend failed: {email_result.error}",
        new_values={"email_sent": bool(email_result), "email_error": email_result.error},
    )
    db.session.commit()
    flash(
        "A new verification code was sent to your email."
        if email_result
        else f"Verification email could not be sent. {email_result.error}",
        "info" if email_result else "danger",
    )
    return redirect(url_for("auth.mfa_verify"))


@auth_bp.route("/logout")
@login_required
def logout():
    snapshot = get_session_snapshot()
    clear_user_session(current_user, snapshot.get("session_id"))
    record_audit(
        "logout",
        "auth",
        remarks=f"User logged out. Session ID: {snapshot.get('session_id')}",
        old_values=snapshot,
    )
    db.session.commit()
    logout_user()
    clear_session()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        if not identity:
            flash("Please enter a registered username or email address.", "danger")
            return render_template("auth/forgot_password.html", identity=identity)

        identity_lower = identity.lower()
        user = User.query.filter(
            ((db.func.lower(User.email) == identity_lower) | (db.func.lower(User.username) == identity_lower)),
            User.deleted_at.is_(None),
        ).first()

        if not user:
            flash("No account was found for that username or email address.", "danger")
            return render_template("auth/forgot_password.html", identity=identity)

        if not user.is_active_user:
            flash("This account is disabled. Please contact an administrator.", "danger")
            return render_template("auth/forgot_password.html", identity=identity)

        send_password_reset_email(user)
        record_audit("reset_password_requested", "auth", user=user, remarks="Password reset email requested.")
        db.session.commit()
        flash("A password reset link has been sent to the registered email address.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", identity="")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash("The password reset link is invalid or expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/reset_password.html", token=token)
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_password.html", token=token)

        user.set_password(password)
        record_audit("reset_password", "auth", user=user, remarks="User reset password using email link.")
        db.session.commit()
        flash("Your password has been updated. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
