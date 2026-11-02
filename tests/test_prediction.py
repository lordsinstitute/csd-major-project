"""Feature extraction, model loading, prediction and risk rules."""

import joblib
import numpy as np
import pytest

from tests.helpers import CLASS_COLORS, build_bundle, make_image_bytes, make_rgb_array
from utils.feature_extraction import (
    extract_features_from_array,
    load_image_rgb,
    preprocess_image,
)
from utils.ml_model import (
    ModelNotAvailableError,
    PredictionError,
    get_model_info,
    is_model_available,
    predict_image,
)
from utils.recommendations import (
    get_disease_info,
    get_recommendations,
    get_risk_level,
)

# HOG 7x7 blocks x 36 values + colour 102 + LBP 10 + GLCM 8
EXPECTED_FEATURES = 1884


# ------------------------------------------------------ feature extraction
def test_feature_vector_shape_and_type():
    vector = extract_features_from_array(make_rgb_array((100, 150, 50)))
    assert vector.ndim == 1
    assert vector.dtype == np.float32
    assert vector.shape[0] == EXPECTED_FEATURES
    assert np.isfinite(vector).all()


def test_feature_length_is_independent_of_image_size():
    square = extract_features_from_array(make_rgb_array((100, 150, 50)))
    wide = extract_features_from_array(make_rgb_array((100, 150, 50), size=(300, 200)))
    assert square.shape == wide.shape


def test_features_are_deterministic():
    array = make_rgb_array((10, 200, 90), seed=5)
    assert np.array_equal(
        extract_features_from_array(array), extract_features_from_array(array)
    )


def test_different_colours_give_different_features():
    red = extract_features_from_array(make_rgb_array(CLASS_COLORS["Coccidiosis"]))
    green = extract_features_from_array(make_rgb_array(CLASS_COLORS["Healthy"]))
    assert not np.array_equal(red, green)


@pytest.mark.parametrize("value", [0, 128, 255])
def test_flat_images_do_not_produce_nan(value):
    flat = np.full((128, 128, 3), value, dtype=np.uint8)
    assert np.isfinite(extract_features_from_array(flat)).all()


def test_preprocess_resizes_to_128x128():
    result = preprocess_image(make_rgb_array((50, 50, 50), size=(300, 200)))
    assert result.shape == (128, 128, 3)


def test_load_image_rgb_reads_png_and_rejects_garbage(tmp_path):
    good = tmp_path / "good.png"
    good.write_bytes(make_image_bytes())
    assert load_image_rgb(good).shape == (128, 128, 3)

    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(ValueError):
        load_image_rgb(bad)


# ------------------------------------------------------------- prediction
def test_predict_image_returns_valid_result(app, trained_model, tmp_path):
    path = tmp_path / "red.png"
    path.write_bytes(make_image_bytes(color=CLASS_COLORS["Coccidiosis"], seed=300))

    with app.app_context():
        result = predict_image(path)

    assert result["disease"] == "Coccidiosis"
    assert set(result["probabilities"]) == set(app.config["CLASSES"])
    assert abs(sum(result["probabilities"].values()) - 100) < 0.1
    assert result["confidence"] == result["probabilities"][result["disease"]]
    assert result["risk_level"] in ("High", "Medium", "Low")


def test_predict_image_rejects_unreadable_file(app, trained_model, tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"garbage")
    with app.app_context():
        with pytest.raises(PredictionError):
            predict_image(path)


def test_missing_model_is_reported(app, tmp_path):
    path = tmp_path / "x.png"
    path.write_bytes(make_image_bytes())
    with app.app_context():
        assert is_model_available() is False
        assert get_model_info() is None
        with pytest.raises(ModelNotAvailableError):
            predict_image(path)


def test_available_model_reports_info(app, trained_model):
    with app.app_context():
        assert is_model_available() is True
        info = get_model_info()
    assert info["n_samples"] == 48


def test_model_with_other_feature_version_is_refused(app):
    path = app.config["MODEL_PATH"]
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(build_bundle(feature_version=999), path)
    with app.app_context():
        assert is_model_available() is False


def test_model_with_unknown_format_is_refused(app):
    path = app.config["MODEL_PATH"]
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": "nothing useful"}, path)
    with app.app_context():
        assert is_model_available() is False


def test_corrupted_model_file_is_refused(app):
    path = app.config["MODEL_PATH"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"this is not a joblib file")
    with app.app_context():
        assert is_model_available() is False


# -------------------------------------------------------------- risk level
@pytest.mark.parametrize(
    "disease, confidence, expected",
    [
        ("Salmonella", 95.0, "High"),
        ("Newcastle", 90.01, "High"),
        ("Salmonella", 90.0, "Medium"),
        ("Coccidiosis", 70.0, "Medium"),
        ("Coccidiosis", 69.9, "Low"),
        ("Healthy", 99.0, "Low"),
    ],
)
def test_risk_level_rules(app, disease, confidence, expected):
    with app.app_context():
        assert get_risk_level(disease, confidence) == expected


def test_healthy_follows_confidence_when_switch_is_off(app):
    app.config["RISK_HEALTHY_IS_LOW"] = False
    with app.app_context():
        assert get_risk_level("Healthy", 95.0) == "High"


# --------------------------------------------------------- recommendations
@pytest.mark.parametrize(
    "disease, expected_line",
    [
        ("Healthy", "Continue monitoring."),
        ("Coccidiosis", "Keep litter dry."),
        ("Salmonella", "Clean feed containers."),
        ("Newcastle", "Contact veterinarian."),
    ],
)
def test_recommendations_exist_for_every_class(disease, expected_line):
    assert expected_line in get_recommendations(disease)


def test_disease_info_exists_for_every_class(app):
    for name in app.config["CLASSES"]:
        info = get_disease_info(name)
        assert info["title"] != "Unknown"
        assert info["summary"]


def test_unknown_disease_has_safe_fallback():
    assert get_recommendations("Nonsense") == []
    assert get_disease_info("Nonsense")["title"] == "Unknown"