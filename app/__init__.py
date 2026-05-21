from datetime import datetime, timedelta

from flask import Flask, flash, redirect, request, url_for
from flask_login import current_user, logout_user
from .config import Config
from .extensions import db, mail, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .registry.routes import registry_bp
    from .analytics.routes import analytics_bp
    from .reports.routes import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(registry_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)

    from .cli import register_cli
    register_cli(app)

    from .models import AuditLog, CaseAscertainment, DiagnosisDisposition, IncidentDetail, PsychiatricHistory, Registry, RegistryIncidentMethod, User  # noqa: F401

    @app.before_request
    def manage_authenticated_session():
        if not current_user.is_authenticated:
            return None
        if request.endpoint in {"static", "auth.logout"}:
            return None

        from .services.audit import record_audit
        from .services.sessions import (
            clear_session,
            clear_user_session,
            get_session_snapshot,
            touch_session,
        )

        snapshot = get_session_snapshot()
        session_id = snapshot.get("session_id")
        if not session_id or current_user.active_session_id != session_id:
            record_audit(
                "session_forced_logout",
                "auth",
                remarks="Session ended because a newer login session is active.",
                old_values=snapshot,
                new_values={"active_session_id": current_user.active_session_id},
            )
            db.session.commit()
            logout_user()
            clear_session()
            flash("You were signed out because your account signed in from another session.", "warning")
            return redirect(url_for("auth.login"))

        last_activity = snapshot.get("last_activity_at")
        timeout_at = None
        if last_activity:
            try:
                timeout_at = datetime.fromisoformat(last_activity) + timedelta(
                    minutes=app.config["SESSION_IDLE_TIMEOUT_MINUTES"]
                )
            except ValueError:
                timeout_at = datetime.utcnow()

        if timeout_at and datetime.utcnow() > timeout_at:
            clear_user_session(current_user, session_id)
            record_audit(
                "session_timeout",
                "auth",
                remarks=f"Session timed out. Session ID: {snapshot.get('session_id')}",
                old_values=snapshot,
            )
            db.session.commit()
            logout_user()
            clear_session()
            flash("Your session expired due to inactivity. Please sign in again.", "warning")
            return redirect(url_for("auth.login"))

        touch_session(current_user)
        db.session.commit()
        return None

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        if user and user.is_active_user:
            return user
        return None

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role == "Encoder":
            return redirect(url_for("analytics.descriptive"))
        return redirect(url_for("analytics.analytics_dashboard"))

    @app.route("/dashboard/")
    def legacy_dashboard():
        return redirect(url_for("analytics.analytics_dashboard"))

    @app.route("/dashboard/registry-statistics")
    def legacy_registry_statistics():
        return redirect(url_for("analytics.descriptive"))

    return app
