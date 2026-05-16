from flask import request
from flask_login import current_user

from app.extensions import db
from app.models.audit_log import AuditLog


def record_audit(event, module, user=None, remarks=None, old_values=None, new_values=None):
    actor = user
    if actor is None and current_user and current_user.is_authenticated:
        actor = current_user

    log = AuditLog(
        user_id=getattr(actor, "id", None),
        role=getattr(actor, "role", None),
        event=event,
        module=module,
        remarks=remarks,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr) if request else None,
        user_agent=request.headers.get("User-Agent", "")[:255] if request else None,
    )
    db.session.add(log)
    return log
