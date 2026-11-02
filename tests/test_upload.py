"""Image upload: validation, secure storage, replacement and private serving."""

import re
from datetime import date, timedelta

import pytest

from tests.helpers import make_image_bytes, post_upload

FILENAME_PATTERN = re.compile(r"^\d+_[0-9a-f]{32}\.(jpg|png)$")


def saved_files(app):
    """Return the files currently in the upload folder."""
    return sorted(app.config["UPLOAD_FOLDER"].iterdir())


# ------------------------------------------------------------- happy path
def test_upload_page_loads(auth_client):
    assert auth_client.get("/upload").status_code == 200


def test_valid_upload_saves_clean_copy(app, auth_client, farmer):
    response = post_upload(auth_client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/upload/review")

    files = saved_files(app)
    assert len(files) == 1
    assert FILENAME_PATTERN.match(files[0].name)
    assert files[0].name.startswith(f"{farmer['id']}_")
    assert "chicken" not in files[0].name  # the user's file name is never used


def test_jpeg_is_saved_with_jpg_extension(app, auth_client):
    post_upload(
        auth_client, image_bytes=make_image_bytes("JPEG"), filename="photo.jpg"
    )
    files = saved_files(app)
    assert len(files) == 1
    assert files[0].suffix == ".jpg"


def test_review_page_shows_entered_details(auth_client):
    post_upload(auth_client, batch_name="Batch Zeta")
    response = auth_client.get("/upload/review")
    assert response.status_code == 200
    assert "Batch Zeta" in response.get_data(as_text=True)


def test_review_without_upload_redirects(auth_client):
    response = auth_client.get("/upload/review")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/upload")


# ------------------------------------------------------------- validation
@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"sick_birds": "150"}, "Sick birds cannot exceed total birds."),
        (
            {"sick_birds": "60", "dead_birds": "50"},
            "Sick and dead birds together cannot exceed total birds.",
        ),
        (
            {"scan_date": (date.today() + timedelta(days=1)).isoformat()},
            "Date cannot be in the future.",
        ),
        ({"total_birds": "0"}, "Number must be between"),
        ({"batch_name": ""}, "This field is required."),
        ({"sick_birds": ""}, "Enter the number of sick birds"),
        ({"image": None}, "Please choose an image to upload."),
    ],
    ids=[
        "sick-above-total",
        "sick-plus-dead-above-total",
        "future-date",
        "zero-total",
        "missing-batch",
        "missing-sick",
        "missing-file",
    ],
)
def test_invalid_form_is_rejected(app, auth_client, overrides, message):
    response = post_upload(auth_client, **overrides)
    assert response.status_code == 200
    assert message in response.get_data(as_text=True)
    assert saved_files(app) == []


def test_fake_image_is_rejected(app, auth_client):
    response = post_upload(
        auth_client, image_bytes=b"this is plain text, not an image", filename="fake.jpg"
    )
    assert response.status_code == 200
    assert "not a valid image" in response.get_data(as_text=True)
    assert saved_files(app) == []


def test_disallowed_extension_is_rejected(app, auth_client):
    response = post_upload(auth_client, filename="photo.gif")
    assert response.status_code == 200
    assert "Only JPG, JPEG and PNG files are allowed." in response.get_data(as_text=True)
    assert saved_files(app) == []


def test_gif_content_with_jpg_name_is_rejected(app, auth_client):
    response = post_upload(
        auth_client, image_bytes=make_image_bytes("GIF"), filename="photo.jpg"
    )
    assert response.status_code == 200
    assert "Only JPG and PNG images are accepted." in response.get_data(as_text=True)
    assert saved_files(app) == []


def test_tiny_image_is_rejected(app, auth_client):
    response = post_upload(
        auth_client, image_bytes=make_image_bytes(size=(32, 32))
    )
    assert response.status_code == 200
    assert "Image is too small" in response.get_data(as_text=True)
    assert saved_files(app) == []


# ------------------------------------------------- replace and cancel
def test_new_upload_replaces_pending_one(app, auth_client):
    post_upload(auth_client, image_bytes=make_image_bytes(seed=1))
    post_upload(auth_client, image_bytes=make_image_bytes(seed=2))
    assert len(saved_files(app)) == 1


def test_cancel_deletes_pending_image(app, auth_client):
    post_upload(auth_client)
    assert len(saved_files(app)) == 1

    response = auth_client.post("/upload/cancel")
    assert response.status_code == 302
    assert saved_files(app) == []

    review = auth_client.get("/upload/review")
    assert review.status_code == 302


# ----------------------------------------------------- serving images
def test_owner_can_view_uploaded_image(app, auth_client):
    post_upload(auth_client)
    name = saved_files(app)[0].name

    response = auth_client.get(f"/uploads/{name}")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert "private" in response.headers["Cache-Control"]


def test_other_farmer_cannot_view_image(app, auth_client, second_client):
    post_upload(auth_client)
    name = saved_files(app)[0].name
    assert second_client.get(f"/uploads/{name}").status_code == 404


def test_anonymous_cannot_view_image(app, auth_client, client):
    post_upload(auth_client)
    name = saved_files(app)[0].name

    response = client.get(f"/uploads/{name}")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@pytest.mark.parametrize("name", ["notes.txt", "1_abc.png", ".."])
def test_invalid_image_names_give_404(auth_client, name):
    assert auth_client.get(f"/uploads/{name}").status_code == 404


def test_missing_image_of_owner_gives_404(auth_client, farmer):
    name = f"{farmer['id']}_{'a' * 32}.png"
    assert auth_client.get(f"/uploads/{name}").status_code == 404