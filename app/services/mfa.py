from datetime import datetime, timedelta
import secrets

from flask import session
from werkzeug.security import check_password_hash, generate_password_hash


MFA_CODE_LENGTH = 6
MFA_EXPIRES_MINUTES = 5
MFA_MAX_ATTEMPTS = 5


def generate_mfa_code():
    return f"{secrets.randbelow(10 ** MFA_CODE_LENGTH):0{MFA_CODE_LENGTH}d}"


def start_mfa_challenge(user, remember=False):
    code = generate_mfa_code()
    session["mfa"] = {
        "user_id": user.id,
        "code_hash": generate_password_hash(code),
        "expires_at": (datetime.utcnow() + timedelta(minutes=MFA_EXPIRES_MINUTES)).isoformat(),
        "attempts": 0,
        "remember": bool(remember),
    }
    session.modified = True
    return code


def get_mfa_challenge():
    challenge = session.get("mfa")
    if not challenge:
        return None
    try:
        expires_at = datetime.fromisoformat(challenge["expires_at"])
    except (KeyError, TypeError, ValueError):
        clear_mfa_challenge()
        return None
    if datetime.utcnow() > expires_at:
        clear_mfa_challenge()
        return None
    return challenge


def verify_mfa_code(code):
    challenge = get_mfa_challenge()
    if not challenge:
        return False, "Verification code expired. Please sign in again."

    challenge["attempts"] = int(challenge.get("attempts", 0)) + 1
    session["mfa"] = challenge
    session.modified = True

    if challenge["attempts"] > MFA_MAX_ATTEMPTS:
        clear_mfa_challenge()
        return False, "Too many verification attempts. Please sign in again."

    if not check_password_hash(challenge["code_hash"], code.strip()):
        return False, "Invalid verification code."

    return True, None


def clear_mfa_challenge():
    session.pop("mfa", None)
    session.modified = True
