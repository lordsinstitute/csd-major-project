"""Authentication: registration, login, logout and protected pages."""

import pytest
from sqlalchemy import func, select

from database.db import db
from models import Farmer
from tests.helpers import PASSWORD, login, make_farmer


def register_data(**overrides):
    """Valid registration form data, with optional changes."""
    data = {
        "name": "Ramesh Kumar",
        "email": "new@example.com",
        "phone": "9876543210",
        "farm_name": "Green Valley Poultry",
        "password": PASSWORD,
        "confirm_password": PASSWORD,
    }
    data.update(overrides)
    return data


def farmer_count(app):
    with app.app_context():
        return db.session.scalar(select(func.count(Farmer.id)))


# ---------------------------------------------------------------- register
def test_register_page_loads(client):
    assert client.get("/register").status_code == 200


def test_register_stores_hashed_password(app, client):
    response = client.post("/register", data=register_data())
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        farmer = db.session.execute(
            select(Farmer).filter_by(email="new@example.com")
        ).scalar_one()
        assert farmer.password != PASSWORD
        assert PASSWORD not in farmer.password
        assert farmer.check_password(PASSWORD)
        assert not farmer.check_password("WrongPass1")


def test_register_accepts_formatted_phone(app, client):
    response = client.post("/register", data=register_data(phone="98765 43210"))
    assert response.status_code == 302
    with app.app_context():
        farmer = db.session.execute(select(Farmer)).scalar_one()
        assert farmer.phone == "9876543210"


@pytest.mark.parametrize(
    "password",
    ["abc1", "abcdefgh", "12345678"],
    ids=["too-short", "no-digit", "no-letter"],
)
def test_register_rejects_weak_password(app, client, password):
    response = client.post(
        "/register",
        data=register_data(password=password, confirm_password=password),
    )
    assert response.status_code == 200
    assert "Password must" in response.get_data(as_text=True)
    assert farmer_count(app) == 0


def test_register_rejects_password_mismatch(app, client):
    response = client.post(
        "/register", data=register_data(confirm_password="Different123")
    )
    assert response.status_code == 200
    assert "Passwords do not match." in response.get_data(as_text=True)
    assert farmer_count(app) == 0


@pytest.mark.parametrize("email", ["ramesh@example.com", "RAMESH@EXAMPLE.COM"])
def test_register_rejects_duplicate_email(app, client, farmer, email):
    response = client.post("/register", data=register_data(email=email))
    assert response.status_code == 200
    assert "already registered" in response.get_data(as_text=True)
    assert farmer_count(app) == 1


def test_register_rejects_invalid_email(app, client):
    response = client.post("/register", data=register_data(email="not-an-email"))
    assert response.status_code == 200
    assert "valid email" in response.get_data(as_text=True)
    assert farmer_count(app) == 0


def test_register_rejects_invalid_phone(app, client):
    response = client.post("/register", data=register_data(phone="123"))
    assert response.status_code == 200
    assert "valid phone number" in response.get_data(as_text=True)
    assert farmer_count(app) == 0


def test_register_shows_success_message(client):
    response = client.post("/register", data=register_data(), follow_redirects=True)
    assert "Account created successfully" in response.get_data(as_text=True)


# ------------------------------------------------------------------- login
def test_login_success_goes_to_dashboard(client, farmer):
    response = login(client, farmer["email"])
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_login_shows_welcome_message(client, farmer):
    response = login(client, farmer["email"], follow_redirects=True)
    assert "Welcome back, Ramesh" in response.get_data(as_text=True)


def test_login_email_is_case_insensitive(client, farmer):
    response = login(client, "RAMESH@EXAMPLE.COM")
    assert response.status_code == 302


def test_login_wrong_password_is_rejected(client, farmer):
    response = login(client, farmer["email"], "WrongPass1")
    assert response.status_code == 200
    assert "Invalid email or password." in response.get_data(as_text=True)


def test_login_unknown_email_gives_same_message(client, farmer):
    response = login(client, "nobody@example.com")
    assert response.status_code == 200
    assert "Invalid email or password." in response.get_data(as_text=True)


def test_login_follows_safe_next_page(client, farmer):
    response = client.post(
        "/login?next=/history",
        data={"email": farmer["email"], "password": farmer["password"]},
    )
    assert response.status_code == 302
    assert "/history" in response.headers["Location"]


@pytest.mark.parametrize("target", ["https://evil.example/", "//evil.example/x"])
def test_login_ignores_external_next_page(client, farmer, target):
    response = client.post(
        "/login",
        query_string={"next": target},
        data={"email": farmer["email"], "password": farmer["password"]},
    )
    assert response.status_code == 302
    assert "evil.example" not in response.headers["Location"]


def test_logged_in_user_skips_login_page(auth_client):
    response = auth_client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_index_redirects(client, auth_client):
    anonymous = client.get("/")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]

    logged_in = auth_client.get("/")
    assert logged_in.status_code == 302
    assert logged_in.headers["Location"].endswith("/dashboard")


# ------------------------------------------------------------------ logout
def test_logout_requires_post(auth_client):
    assert auth_client.get("/logout").status_code == 405


def test_logout_ends_session(auth_client):
    response = auth_client.post("/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    after = auth_client.get("/dashboard")
    assert after.status_code == 302
    assert "/login" in after.headers["Location"]


# --------------------------------------------------------- protected pages
@pytest.mark.parametrize(
    "url",
    [
        "/dashboard",
        "/api/dashboard-data",
        "/upload",
        "/upload/review",
        "/history",
        "/analytics",
        "/export/csv",
        "/export/pdf",
        "/result/1",
    ],
)
def test_pages_require_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]