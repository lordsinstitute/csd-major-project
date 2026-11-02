"""DiseaseRecord model: one row per image scan submitted by a farmer."""

from datetime import date

from database.db import db


class DiseaseRecord(db.Model):
    """Stores the scan details, bird counts and the ML prediction."""

    __tablename__ = "disease_records"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("farmers.id"), nullable=False, index=True
    )
    batch_name = db.Column(db.String(100), nullable=False)
    total_birds = db.Column(db.Integer, nullable=False, default=0)
    sick_birds = db.Column(db.Integer, nullable=False, default=0)
    dead_birds = db.Column(db.Integer, nullable=False, default=0)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    image_path = db.Column(db.String(255), nullable=False)
    predicted_disease = db.Column(db.String(50), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)  # stored as percent (0-100)
    risk_level = db.Column(db.String(10), nullable=False)  # High / Medium / Low

    __table_args__ = (
        db.CheckConstraint("total_birds >= 0", name="ck_total_birds_non_negative"),
        db.CheckConstraint("sick_birds >= 0", name="ck_sick_birds_non_negative"),
        db.CheckConstraint("dead_birds >= 0", name="ck_dead_birds_non_negative"),
        db.CheckConstraint(
            "confidence >= 0 AND confidence <= 100", name="ck_confidence_range"
        ),
    )

    def to_dict(self):
        """Return the record as a dictionary (used by CSV/PDF export)."""
        return {
            "id": self.id,
            "date": self.date.strftime("%d-%m-%Y"),
            "farmer": self.farmer.name,
            "farm_name": self.farmer.farm_name,
            "batch_name": self.batch_name,
            "total_birds": self.total_birds,
            "sick_birds": self.sick_birds,
            "dead_birds": self.dead_birds,
            "predicted_disease": self.predicted_disease,
            "confidence": round(self.confidence, 2),
            "risk_level": self.risk_level,
            "image_path": self.image_path,
        }

    def __repr__(self):
        return f"<DiseaseRecord {self.id} {self.predicted_disease}>"