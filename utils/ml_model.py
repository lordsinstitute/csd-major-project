"""Prediction service: loads the trained Random Forest and classifies images."""

import threading
from pathlib import Path

import joblib
from flask import current_app

from utils.feature_extraction import FEATURE_VERSION, extract_features
from utils.recommendations import get_risk_level

REQUIRED_KEYS = ("model", "feature_version", "n_features")

_lock = threading.Lock()
_cache = {"path": None, "mtime": None, "bundle": None}


class ModelNotAvailableError(RuntimeError):
    """Raised when the trained model file is missing or unusable."""


class PredictionError(RuntimeError):
    """Raised when an image cannot be analysed."""


def _load_bundle(model_path):
    """
    Load the model bundle, reusing the cached copy until the file changes.

    Only load model files that you trained yourself: joblib files are
    Python pickles and must never come from an untrusted source.
    """
    model_path = Path(model_path)
    with _lock:
        if not model_path.is_file():
            _cache.update(path=None, mtime=None, bundle=None)
            raise ModelNotAvailableError(
                "The disease model has not been trained yet. "
                "Run: python train_model.py"
            )

        mtime = model_path.stat().st_mtime
        if _cache["path"] == model_path and _cache["mtime"] == mtime:
            return _cache["bundle"]

        try:
            bundle = joblib.load(model_path)
        except Exception as error:  # corrupted or incompatible file
            raise ModelNotAvailableError(
                "The model file could not be loaded. Please retrain it "
                "with: python train_model.py"
            ) from error

        if not isinstance(bundle, dict) or any(k not in bundle for k in REQUIRED_KEYS):
            raise ModelNotAvailableError(
                "The model file has an unknown format. Please retrain it "
                "with: python train_model.py"
            )
        if bundle["feature_version"] != FEATURE_VERSION:
            raise ModelNotAvailableError(
                "The model was trained with different feature settings. "
                "Please retrain it with: python train_model.py"
            )

        _cache.update(path=model_path, mtime=mtime, bundle=bundle)
        return bundle


def is_model_available():
    """Return True when a usable trained model exists."""
    try:
        _load_bundle(current_app.config["MODEL_PATH"])
    except ModelNotAvailableError:
        return False
    return True


def get_model_info():
    """Return training details (date, samples, metrics) or None."""
    try:
        bundle = _load_bundle(current_app.config["MODEL_PATH"])
    except ModelNotAvailableError:
        return None
    return {
        "trained_at": bundle.get("trained_at"),
        "n_samples": bundle.get("n_samples"),
        "class_counts": bundle.get("class_counts"),
        "metrics": bundle.get("metrics"),
    }


def predict_image(image_path):
    """
    Classify one image file.

    Returns a dictionary:
        disease        - predicted class name
        confidence     - probability of that class, in percent (0-100)
        probabilities  - percent for every class
        risk_level     - High, Medium or Low
    """
    bundle = _load_bundle(current_app.config["MODEL_PATH"])
    model = bundle["model"]

    try:
        features = extract_features(image_path)
    except Exception as error:
        raise PredictionError(
            "The image could not be processed. Please upload a different photo."
        ) from error

    sample = features.reshape(1, -1)
    if sample.shape[1] != bundle["n_features"]:
        raise ModelNotAvailableError(
            "The model does not match the current feature settings. "
            "Please retrain it with: python train_model.py"
        )

    # predict() gives the class, predict_proba() gives the probability of
    # every class (the fraction of the 200 trees that voted for it)
    disease = str(model.predict(sample)[0])
    probabilities_raw = model.predict_proba(sample)[0]
    classes = [str(name) for name in model.classes_]

    probabilities = {
        name: round(float(prob) * 100, 2)
        for name, prob in zip(classes, probabilities_raw)
    }
    ordered = {
        name: probabilities.get(name, 0.0)
        for name in current_app.config["CLASSES"]
    }
    confidence = probabilities[disease]

    return {
        "disease": disease,
        "confidence": confidence,
        "probabilities": ordered,
        "risk_level": get_risk_level(disease, confidence),
    }