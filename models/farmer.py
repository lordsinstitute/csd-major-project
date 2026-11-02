"""Farmer model: stores registered users with securely hashed passwords."""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import db


class Farmer(UserMixin, db.Model):
    """A registered farmer who can log in and upload scans."""

    __tablename__ = "farmers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)  # hash, never plain text
    phone = db.Column(db.String(20), nullable=False)
    farm_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # One farmer has many disease records
    records = db.relationship(
        "DiseaseRecord",
        backref="farmer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, raw_password):
        """Hash the given password and store the hash."""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password, raw_password)

    def __repr__(self):
        return f"<Farmer {self.id} {self.email}>"