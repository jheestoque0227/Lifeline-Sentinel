import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv(override=True)


def _env_str(name, default=""):
    return os.getenv(name, default).strip().strip('"').strip("'")


def _env_bool(name, default=False):
    value = _env_str(name, str(default)).lower()
    return value in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = _env_str("SECRET_KEY", "dev-secret-key")

    DB_HOST = _env_str("DB_HOST", "localhost")
    DB_PORT = _env_str("DB_PORT", "3306")
    DB_NAME = _env_str("DB_NAME", "lifeline_sentinel_db")
    DB_USER = _env_str("DB_USER", "root")
    DB_PASSWORD = _env_str("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_IDLE_TIMEOUT_MINUTES = int(_env_str("SESSION_IDLE_TIMEOUT_MINUTES", "15"))
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_IDLE_TIMEOUT_MINUTES)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = _env_str("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)

    MAIL_SERVER = _env_str("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(_env_str("MAIL_PORT", "587"))
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = _env_str("MAIL_USERNAME", "")
    MAIL_PASSWORD = _env_str("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = _env_str("MAIL_DEFAULT_SENDER", "")

    INITIAL_ADMIN_EMPLOYEE_NO = _env_str("INITIAL_ADMIN_EMPLOYEE_NO", "")
    INITIAL_ADMIN_FULL_NAME = _env_str("INITIAL_ADMIN_FULL_NAME", "")
    INITIAL_ADMIN_EMAIL = _env_str("INITIAL_ADMIN_EMAIL", "")
    INITIAL_ADMIN_USERNAME = _env_str("INITIAL_ADMIN_USERNAME", "")
    INITIAL_ADMIN_PASSWORD = _env_str("INITIAL_ADMIN_PASSWORD", "")
