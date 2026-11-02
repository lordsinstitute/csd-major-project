"""Security behaviour: CSRF, headers, cookies and rate limiting."""

import re

from tests.helpers import PASSWORD, login, make_farmer


def test_login_without_csrf_token_is_rejected(csrf_app):
    make_farmer(csrf_app)
    client = csrf_app.test_client()
    response = client.post(
        "/login", data={"email": "ramesh@example.com", "password": PASSWORD}
    )
    assert response.status_code == 400


def test_login_with_csrf_token_works(csrf_app):
    make_farmer(csrf_app)
    client = csrf_app.test_client()

    page = client.get("/login").get_data(as_text=True)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)
    assert match is not None

    response = client.post(
        "/login",
        data={
            "email": "ramesh@example.com",
            "password": PASSWORD,
            "csrf_token": match.group(1),
        },
    )
    assert response.status_code == 302


def test_logout_without_csrf_token_is_rejected(csrf_app):
    client = csrf_app.test_client()
    assert client.post("/logout").status_code in (400, 401, 302)


def test_security_headers_are_set(client):
    response = client.get("/login")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "same-origin"


def test_session_cookie_flags(client, farmer):
    response = login(client, farmer["email"])
    cookies = " ".join(response.headers.getlist("Set-Cookie"))
    assert "HttpOnly" in cookies
    assert "SameSite=Lax" in cookies


def test_unknown_page_uses_custom_404(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert "does not exist" in response.get_data(as_text=True)


def test_login_is_rate_limited(rate_limited_app):
    make_farmer(rate_limited_app)
    client = rate_limited_app.test_client()

    for _ in range(10):
        response = login(client, "ramesh@example.com", "WrongPass1")
        assert response.status_code == 200

    blocked = login(client, "ramesh@example.com", "WrongPass1")
    assert blocked.status_code == 429
    assert "Too many attempts" in blocked.get_data(as_text=True)

    # Opening the page is never counted or blocked
    assert client.get("/login").status_code == 200