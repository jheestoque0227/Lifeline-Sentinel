import smtplib
from dataclasses import dataclass

from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from app.extensions import mail


@dataclass
class EmailSendResult:
    sent: bool
    error: str | None = None

    def __bool__(self):
        return self.sent


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="password-reset")


def generate_reset_token(user):
    return _serializer().dumps({"user_id": user.id, "password_hash": user.password_hash})


def verify_reset_token(token, max_age=3600):
    from app.models.user import User

    try:
        payload = _serializer().loads(token, max_age=max_age)
    except Exception:
        return None

    user = User.query.get(payload.get("user_id"))
    if not user or not user.is_active_user or user.deleted_at:
        return None
    if payload.get("password_hash") != user.password_hash:
        return None
    return user


def send_password_reset_email(user):
    reset_url = url_for("auth.reset_password", token=generate_reset_token(user), _external=True)
    subject = "Lifeline Sentinel password reset"
    body = (
        f"Hello {user.full_name},\n\n"
        "A password reset was requested for your Lifeline Sentinel account.\n"
        f"Open this link within 1 hour to set a new password:\n{reset_url}\n\n"
        "If you did not request this, you may ignore this message."
    )
    return send_email(user.email, subject, body)


def send_initial_password_email(user, initial_password):
    subject = "Lifeline Sentinel account created"
    body = (
        f"Hello {user.full_name},\n\n"
        "Your Lifeline Sentinel account has been created.\n\n"
        f"Username: {user.username}\n"
        f"Initial password: {initial_password}\n\n"
        "Please sign in and reset your password as soon as possible."
    )
    return send_email(user.email, subject, body)


def send_mfa_code_email(user, code, expires_minutes):
    subject = "Lifeline Sentinel verification code"
    body = (
        f"Hello {user.full_name},\n\n"
        "Use this verification code to complete your Lifeline Sentinel sign in:\n\n"
        f"{code}\n\n"
        f"This code expires in {expires_minutes} minutes. "
        "If you did not try to sign in, please contact your system administrator."
    )
    return send_email(user.email, subject, body)


def send_email(to_address, subject, body):
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username
    if not username or not password or not sender:
        message_text = "Mail is not configured. Check MAIL_USERNAME, MAIL_PASSWORD, and MAIL_DEFAULT_SENDER."
        current_app.logger.warning(message_text)
        return EmailSendResult(False, message_text)

    message = Message(
        subject=subject,
        sender=sender,
        recipients=[to_address],
        body=body,
    )

    try:
        mail.send(message)
    except smtplib.SMTPAuthenticationError as exc:
        smtp_error = exc.smtp_error.decode(errors="ignore") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
        message_text = f"SMTP authentication failed: {exc.smtp_code} {smtp_error}"
        current_app.logger.exception(message_text)
        return EmailSendResult(False, message_text)
    except (OSError, smtplib.SMTPException) as exc:
        message_text = f"Email could not be sent: {type(exc).__name__}: {exc}"
        current_app.logger.exception(message_text)
        return EmailSendResult(False, message_text)
    return EmailSendResult(True)
