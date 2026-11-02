"""Pytest fixtures: an isolated app, database and upload folder per test."""

import os

# Must be set before the app module is imported (it builds an app on import)
os.environ["APP_ENV"] = "testing"

import joblib
import pytest

from app import create_app
from config import TestingConfig
from database.db import db
from tests.helpers import build_bundle, login, make_farmer


def _make_config(tmp_path, **extra):
    """Build a test config class that keeps every file inside tmp_path."""
    attrs = {
        "DATABASE_DIR": tmp_path / "database",
        "UPLOAD_FOLDER": tmp_path / "uploads",
        "EXPORT_FOLDER": tmp_path / "exports",
        "MODEL_DIR": tmp_path / "ml_model",
        "DATASET_DIR": tmp_path / "dataset",
        "MODEL_PATH": tmp_path / "ml_model" / "poultry_rf_model.joblib",
    }
    attrs.update(extra)
    return type("TempConfig", (TestingConfig,), attrs)


def _dispose(flask_app):
    """Drop the in-memory database after a test."""
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def app(tmp_path):
    """A fresh app with its own in-memory database (CSRF and limits off)."""
    flask_app = create_app(_make_config(tmp_path))
    yield flask_app
    _dispose(flask_app)


@pytest.fixture()
def csrf_app(tmp_path):
    """An app with CSRF protection switched on."""
    flask_app = create_app(_make_config(tmp_path, WTF_CSRF_ENABLED=True))
    yield flask_app
    _dispose(flask_app)


@pytest.fixture()
def rate_limited_app(tmp_path):
    """An app with rate limiting switched on."""
    flask_app = create_app(_make_config(tmp_path, RATELIMIT_ENABLED=True))
    yield flask_app
    _dispose(flask_app)


@pytest.fixture()
def client(app):
    """An anonymous test client."""
    return app.test_client()


@pytest.fixture()
def farmer(app):
    """A registered farmer (stored with a hashed password)."""
    return make_farmer(app)


@pytest.fixture()
def second_farmer(app):
    """A second farmer on a different farm."""
    return make_farmer(
        app, email="suresh@example.com", name="Suresh", farm_name="Sunrise Farm"
    )


@pytest.fixture()
def auth_client(app, farmer):
    """A test client logged in through the real login form."""
    test_client = app.test_client()
    response = login(test_client, farmer["email"], farmer["password"])
    assert response.status_code == 302
    return test_client


@pytest.fixture()
def second_client(app, second_farmer):
    """A separate client logged in as the second farmer."""
    test_client = app.test_client()
    response = login(test_client, second_farmer["email"], second_farmer["password"])
    assert response.status_code == 302
    return test_client


@pytest.fixture()
def trained_model(app):
    """Save a tiny trained model where the app expects it."""
    path = app.config["MODEL_PATH"]
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(build_bundle(), path)
    return path