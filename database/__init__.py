"""Database package: exposes the shared SQLAlchemy instance."""

from database.db import db, init_db

__all__ = ["db", "init_db"]