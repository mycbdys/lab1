"""Tests for POST /auth/login and password storage."""

from __future__ import annotations

import bcrypt

from app.db import get_db
from conftest import login


def test_login_returns_signed_token(client):
    response = login(client)
    assert response.status_code == 200
    body = response.get_json()
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 900
    assert body["access_token"].count(".") == 2


def test_wrong_password_is_rejected(client):
    response = login(client, password="Wrong#2026")
    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid username or password"


def test_unknown_user_has_identical_error(client):
    response = login(client, username="mallory", password="Wrong#2026")
    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid username or password"


def test_missing_or_non_json_body(client):
    assert client.post("/auth/login", json={"username": "alice"}).status_code == 400
    assert client.post("/auth/login", data="not-json", content_type="text/plain").status_code == 400
    assert client.post("/auth/login", json=["alice"]).status_code == 400


def test_short_password_rejected(client):
    assert login(client, password="short").status_code == 400


def test_sql_injection_attempt_cannot_authenticate(client):
    response = login(client, username="alice' OR '1'='1", password="x' OR '1'='1")
    assert response.status_code == 400

    response = login(client, password="' OR '1'='1' --")
    assert response.status_code == 401


def test_password_is_stored_as_bcrypt_hash(client, app):
    with app.app_context():
        row = get_db().execute(
            "SELECT password_hash FROM users WHERE username = ?", ("alice",)
        ).fetchone()
    assert row["password_hash"] != "Alice#2026"
    assert row["password_hash"].startswith("$2b$")
    assert bcrypt.checkpw(b"Alice#2026", row["password_hash"].encode())


def test_login_is_rate_limited(client):
    for _ in range(5):
        assert login(client, password="Wrong#2026").status_code == 401
    response = login(client, password="Wrong#2026")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
