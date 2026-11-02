"""Models package: imports every model so SQLAlchemy registers them."""

from models.farmer import Farmer
from models.disease_record import DiseaseRecord

__all__ = ["Farmer", "DiseaseRecord"]