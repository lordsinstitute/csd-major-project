"""Shared SQLAlchemy instance and database initialisation helper."""

from flask_sqlalchemy import SQLAlchemy

# One db object is shared by the whole application
db = SQLAlchemy()


def init_db(app):
    """
    Bind SQLAlchemy to the Flask app and create all tables.

    Models are imported inside the function so that they are registered
    with SQLAlchemy before create_all() runs.
    """
    db.init_app(app)

    with app.app_context():
        import models  # noqa: F401  (registers Farmer and DiseaseRecord)
        db.create_all()