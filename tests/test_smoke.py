from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models.user import User
from app.services.email import EmailSendResult


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_IDLE_TIMEOUT_MINUTES = 15
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "test@example.com"
    MAIL_PASSWORD = "app-password"
    MAIL_DEFAULT_SENDER = "test@example.com"


def _make_app(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr("app.auth.routes.send_mfa_code_email", lambda *args, **kwargs: EmailSendResult(True))
    monkeypatch.setattr("app.auth.routes.verify_mfa_code", lambda code: (True, None))
    with app.app_context():
        db.create_all()
        user = User(
            employee_no="1001",
            full_name="Admin User",
            email="admin@example.com",
            username="admin",
            role="Admin",
            is_active_user=True,
        )
        user.set_password("Password@123")
        db.session.add(user)
        db.session.commit()
    return app


def _login(client):
    login_response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "Password@123"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302
    mfa_response = client.post("/auth/mfa", data={"code": "123456"}, follow_redirects=False)
    assert mfa_response.status_code == 302
    return mfa_response


def test_login_session_cookie_expires_when_browser_closes(monkeypatch):
    app = _make_app(monkeypatch)
    client = app.test_client()

    response = _login(client)
    set_cookie = response.headers.get("Set-Cookie", "")

    assert "session=" in set_cookie
    assert "Expires=" not in set_cookie


def test_new_login_forces_previous_session_to_logout(monkeypatch):
    app = _make_app(monkeypatch)
    first_client = app.test_client()
    second_client = app.test_client()

    _login(first_client)
    with app.app_context():
        first_session_id = User.query.filter_by(username="admin").first().active_session_id

    _login(second_client)
    with app.app_context():
        second_session_id = User.query.filter_by(username="admin").first().active_session_id

    response = first_client.get("/", follow_redirects=False)

    assert first_session_id != second_session_id
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_idle_timeout_clears_active_session(monkeypatch):
    app = _make_app(monkeypatch)
    client = app.test_client()

    _login(client)
    with client.session_transaction() as session:
        session["last_activity_at"] = (datetime.utcnow() - timedelta(minutes=16)).isoformat()

    response = client.get("/", follow_redirects=False)

    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        assert user.active_session_id is None

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
