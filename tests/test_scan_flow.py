"""Analyze step and result page: saving records and access control."""

from sqlalchemy import func, select

from database.db import db
from models import DiseaseRecord
from tests.helpers import CLASS_COLORS, add_record, make_image_bytes, post_upload


def record_count(app):
    with app.app_context():
        return db.session.scalar(select(func.count(DiseaseRecord.id)))


# ----------------------------------------------------- model not trained
def test_review_disables_analyze_without_model(auth_client):
    post_upload(auth_client)
    text = auth_client.get("/upload/review").get_data(as_text=True)
    assert "has not been trained" in text
    assert "disabled" in text


def test_analyze_without_model_creates_no_record(app, auth_client):
    post_upload(auth_client)
    response = auth_client.post("/upload/analyze", follow_redirects=True)
    assert "has not been trained" in response.get_data(as_text=True)
    assert record_count(app) == 0

    # The upload is still waiting, so the farmer can retry after training
    assert auth_client.get("/upload/review").status_code == 200


def test_analyze_without_pending_upload_redirects(auth_client):
    response = auth_client.post("/upload/analyze")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/upload")


# --------------------------------------------------------- with a model
def test_analyze_saves_record_and_shows_result(
    app, auth_client, farmer, trained_model
):
    image = make_image_bytes(color=CLASS_COLORS["Coccidiosis"], seed=500)
    post_upload(auth_client, image_bytes=image)

    response = auth_client.post("/upload/analyze")
    assert response.status_code == 302
    assert "/result/" in response.headers["Location"]
    assert record_count(app) == 1

    with app.app_context():
        record = db.session.execute(select(DiseaseRecord)).scalar_one()
        assert record.farmer_id == farmer["id"]
        assert record.batch_name == "Batch A"
        assert (record.total_birds, record.sick_birds, record.dead_birds) == (100, 10, 2)
        assert record.predicted_disease == "Coccidiosis"
        assert 0 <= record.confidence <= 100
        assert record.risk_level in ("High", "Medium", "Low")
        assert (app.config["UPLOAD_FOLDER"] / record.image_path).is_file()

    page = auth_client.get(response.headers["Location"])
    text = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Recommendation" in text
    assert "Keep litter dry." in text
    assert "not a veterinary diagnosis" in text
    assert "Probability by class" in text


def test_second_analyze_does_not_create_duplicate(app, auth_client, trained_model):
    post_upload(auth_client)
    auth_client.post("/upload/analyze")

    again = auth_client.post("/upload/analyze")
    assert again.status_code == 302
    assert again.headers["Location"].endswith("/upload")
    assert record_count(app) == 1


# ----------------------------------------------------------- result page
def test_result_page_belongs_to_owner(app, auth_client, second_client, farmer):
    record_id = add_record(app, farmer["id"])
    assert auth_client.get(f"/result/{record_id}").status_code == 200
    assert second_client.get(f"/result/{record_id}").status_code == 404


def test_result_for_unknown_id_is_404(auth_client):
    assert auth_client.get("/result/9999").status_code == 404


def test_low_confidence_warning(app, auth_client, farmer):
    unsure = add_record(app, farmer["id"], confidence=55.0, risk_level="Low")
    sure = add_record(app, farmer["id"], confidence=95.0, risk_level="High")

    assert "not very sure" in auth_client.get(f"/result/{unsure}").get_data(as_text=True)
    assert "not very sure" not in auth_client.get(f"/result/{sure}").get_data(as_text=True)