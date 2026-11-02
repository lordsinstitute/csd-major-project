"""Shared helpers for the test suite (data builders and request helpers)."""

import functools
import io
from datetime import date, timedelta

import numpy as np
from PIL import Image

from database.db import db
from models import DiseaseRecord, Farmer

PASSWORD = "Secret123"

# Strongly different colours so a tiny model can separate the four classes.
# These are synthetic test images only; they are not real droppings photos.
CLASS_COLORS = {
    "Healthy": (60, 160, 60),
    "Coccidiosis": (180, 40, 40),
    "Salmonella": (200, 190, 50),
    "Newcastle": (50, 60, 190),
}


# ----------------------------------------------------------------------
# Images
# ----------------------------------------------------------------------
def make_rgb_array(color, seed=0, size=(128, 128)):
    """Return a noisy RGB image array of one base colour (width, height)."""
    rng = np.random.default_rng(seed)
    noise = rng.integers(-15, 16, size=(size[1], size[0], 3))
    return np.clip(np.array(color) + noise, 0, 255).astype(np.uint8)


def make_image_bytes(image_format="PNG", color=(180, 40, 40), size=(128, 128), seed=0):
    """Return an encoded image (PNG, JPEG or GIF) as bytes."""
    buffer = io.BytesIO()
    Image.fromarray(make_rgb_array(color, seed, size)).save(
        buffer, format=image_format
    )
    return buffer.getvalue()


# ----------------------------------------------------------------------
# Users and records
# ----------------------------------------------------------------------
def make_farmer(
    app,
    email="ramesh@example.com",
    name="Ramesh",
    farm_name="Green Valley Poultry",
    password=PASSWORD,
):
    """Create a farmer in the test database and return its details."""
    with app.app_context():
        farmer = Farmer(
            name=name, email=email, phone="9876543210", farm_name=farm_name
        )
        farmer.set_password(password)
        db.session.add(farmer)
        db.session.commit()
        return {
            "id": farmer.id,
            "email": email,
            "password": password,
            "name": name,
            "farm_name": farm_name,
        }


def login(client, email, password=PASSWORD, **kwargs):
    """Submit the login form."""
    return client.post(
        "/login", data={"email": email, "password": password}, **kwargs
    )


def add_record(app, farmer_id, **overrides):
    """Insert one disease record and return its id."""
    values = {
        "farmer_id": farmer_id,
        "batch_name": "Batch A",
        "total_birds": 100,
        "sick_birds": 10,
        "dead_birds": 2,
        "date": date.today(),
        "image_path": "x.png",
        "predicted_disease": "Salmonella",
        "confidence": 91.0,
        "risk_level": "High",
    }
    values.update(overrides)
    with app.app_context():
        record = DiseaseRecord(**values)
        db.session.add(record)
        db.session.commit()
        return record.id


def seed_three(app, farmer_id):
    """Add three records with different diseases, risks and dates."""
    today = date.today()
    add_record(
        app, farmer_id, batch_name="Alpha", predicted_disease="Healthy",
        confidence=95.0, risk_level="Low", sick_birds=0, dead_birds=0,
        date=today - timedelta(days=30),
    )
    add_record(
        app, farmer_id, batch_name="Bravo", predicted_disease="Salmonella",
        confidence=91.0, risk_level="High", date=today - timedelta(days=10),
    )
    add_record(
        app, farmer_id, batch_name="Charlie", predicted_disease="Newcastle",
        confidence=75.0, risk_level="Medium", date=today,
    )


# ----------------------------------------------------------------------
# Upload form
# ----------------------------------------------------------------------
def upload_form(image_bytes, filename="chicken.png", **overrides):
    """Build the multipart form data for the upload page."""
    data = {
        "batch_name": "Batch A",
        "scan_date": date.today().isoformat(),
        "total_birds": "100",
        "sick_birds": "10",
        "dead_birds": "2",
        "image": (io.BytesIO(image_bytes), filename),
    }
    data.update(overrides)
    if data.get("image") is None:
        data.pop("image")
    return data


def post_upload(client, image_bytes=None, filename="chicken.png", **overrides):
    """Post the upload form (a valid PNG is used unless told otherwise)."""
    if image_bytes is None:
        image_bytes = make_image_bytes()
    return client.post(
        "/upload",
        data=upload_form(image_bytes, filename, **overrides),
        content_type="multipart/form-data",
    )


# ----------------------------------------------------------------------
# Tiny trained model (only proves the pipeline works, not real accuracy)
# ----------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _trained_model():
    """Train a small Random Forest on synthetic images (built once)."""
    from sklearn.ensemble import RandomForestClassifier

    from utils.feature_extraction import extract_features_from_array

    features, labels = [], []
    for name, color in CLASS_COLORS.items():
        for seed in range(12):
            features.append(extract_features_from_array(make_rgb_array(color, seed)))
            labels.append(name)
    x_train = np.array(features)
    model = RandomForestClassifier(n_estimators=30, random_state=0)
    model.fit(x_train, np.array(labels))
    return model, int(x_train.shape[1])


def build_bundle(feature_version=None):
    """Return a model bundle in the same format train_model.py saves."""
    from utils.feature_extraction import FEATURE_VERSION

    model, n_features = _trained_model()
    return {
        "model": model,
        "classes": [str(name) for name in model.classes_],
        "feature_version": FEATURE_VERSION if feature_version is None else feature_version,
        "n_features": n_features,
        "image_size": [128, 128],
        "trained_at": "2026-01-01T00:00:00+00:00",
        "n_samples": 48,
        "class_counts": {name: 12 for name in CLASS_COLORS},
        "metrics": {},
    }