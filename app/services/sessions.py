from datetime import datetime
import secrets

from flask import session


SESSION_ID_BYTES = 16


def start_login_session(user):
    now = datetime.utcnow()
    now_iso = now.isoformat()
    session_id = secrets.token_urlsafe(SESSION_ID_BYTES)
    session.permanent = False
    session["session_id"] = session_id
    session["session_user_id"] = user.id
    session["session_started_at"] = now_iso
    session["last_activity_at"] = now_iso
    session.modified = True
    user.active_session_id = session_id
    user.active_session_started_at = now
    user.active_session_last_seen_at = now
    return session_id


def touch_session(user=None):
    now = datetime.utcnow()
    session["last_activity_at"] = now.isoformat()
    session.modified = True
    if user is not None:
        user.active_session_last_seen_at = now


def get_session_snapshot():
    return {
        "session_id": session.get("session_id"),
        "session_user_id": session.get("session_user_id"),
        "session_started_at": session.get("session_started_at"),
        "last_activity_at": session.get("last_activity_at"),
    }


def clear_user_session(user, session_id=None):
    if user is None:
        return
    if session_id and user.active_session_id != session_id:
        return
    user.active_session_id = None
    user.active_session_started_at = None
    user.active_session_last_seen_at = None


def clear_session():
    session.clear()
    session.modified = True
