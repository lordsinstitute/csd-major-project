"""Application configuration for the Poultry Disease Detection project."""

import os
import secrets
from datetime import timedelta
from pathlib import Path

# Absolute path of the project root folder
BASE_DIR = Path(__file__).resolve().parent


def _load_secret_key():
    """
    Return the Flask secret key.

    Priority:
    1. SECRET_KEY environment variable.
    2. A key stored in the local .secret_key file.
    3. A newly generated random key, saved to .secret_key so that
       user sessions stay valid after a server restart.
    """
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    key_file = BASE_DIR / ".secret_key"
    if key_file.exists():
        stored_key = key_file.read_text(encoding="utf-8").strip()
        if stored_key:
            return stored_key

    new_key = secrets.token_hex(32)
    key_file.write_text(new_key, encoding="utf-8")
    try:
        os.chmod(key_file, 0o600)
    except OSError:
        # Some platforms (e.g. Windows) do not support POSIX permissions
        pass
    return new_key


class Config:
    """Base configuration shared by all environments."""

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
    SECRET_KEY = _load_secret_key()
    DEBUG = False
    TESTING = False

    # ------------------------------------------------------------------
    # Folders
    # ------------------------------------------------------------------
    DATABASE_DIR = BASE_DIR / "database"
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    EXPORT_FOLDER = BASE_DIR / "exports"
    MODEL_DIR = BASE_DIR / "ml_model"
    DATASET_DIR = BASE_DIR / "dataset"

    # ------------------------------------------------------------------
    # Database (SQLite through SQLAlchemy ORM)
    # ------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + (DATABASE_DIR / "poultry.db").as_posix(),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------
    # Sessions, cookies and CSRF
    # ------------------------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True

    # ------------------------------------------------------------------
    # Image upload
    # ------------------------------------------------------------------
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB per request
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

    # ------------------------------------------------------------------
    # Machine learning
    # ------------------------------------------------------------------
    IMAGE_SIZE = (128, 128)
    CLASSES = ["Healthy", "Coccidiosis", "Salmonella", "Newcastle"]
    MODEL_PATH = MODEL_DIR / "poultry_rf_model.joblib"
    RF_N_ESTIMATORS = 200

    # Risk level thresholds on confidence (percent)
    RISK_HIGH_THRESHOLD = 90.0    # above 90        -> High
    RISK_MEDIUM_THRESHOLD = 70.0  # 70 to 90        -> Medium, below 70 -> Low
    # A "Healthy" prediction is always shown as Low risk, even when the
    # model is very confident. Set to False to use only the confidence
    # thresholds for every class.
    RISK_HEALTHY_IS_LOW = True

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    RECORDS_PER_PAGE = 10

    # ------------------------------------------------------------------
    # Password policy
    # ------------------------------------------------------------------
    PASSWORD_MIN_LENGTH = 8
    # ------------------------------------------------------------------
    # Rate limiting (Flask-Limiter). Counted per client IP address.
    # For several server processes use a shared store such as Redis:
    #   RATELIMIT_STORAGE_URI=redis://localhost:6379
    # ------------------------------------------------------------------
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    LOGIN_RATE_LIMIT = "10 per minute;100 per hour"
    REGISTER_RATE_LIMIT = "20 per hour"


class DevelopmentConfig(Config):
    """Configuration for local development."""

    DEBUG = True


class ProductionConfig(Config):
    """Configuration for deployment (HTTPS required for cookies)."""

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuration for automated tests using an in-memory database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Return the config class selected by the APP_ENV environment variable."""
    env_name = os.environ.get("APP_ENV", "development").lower()
    return CONFIG_MAP.get(env_name, DevelopmentConfig)


def ensure_directories(config_class=None):
    """Create every folder the application needs if it does not exist."""
    cfg = config_class or get_config()
    for folder in (
        cfg.DATABASE_DIR,
        cfg.UPLOAD_FOLDER,
        cfg.EXPORT_FOLDER,
        cfg.MODEL_DIR,
        cfg.DATASET_DIR,
    ):
        Path(folder).mkdir(parents=True, exist_ok=True)