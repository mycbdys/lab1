"""Tests for the protected endpoints, output encoding and token validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from conftest import bearer, login


def test_data_requires_token(client):
    response = client.get("/api/data")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


def test_data_returns_only_callers_posts(client):
    alice_headers = bearer(client, "alice")
    client.post(
        "/api/posts",
        json={"title": "Alice note", "body": "Alice body"},
        headers=alice_headers,
    )

    bob_headers = bearer(client, "bob")
    bob_view = client.get("/api/data", headers=bob_headers).get_json()
    assert bob_view["username"] == "bob"
    assert bob_view["posts"] == []

    alice_view = client.get("/api/data", headers=alice_headers).get_json()
    assert alice_view["username"] == "alice"
    assert [post["title"] for post in alice_view["posts"]] == ["Alice note"]


def test_create_post_requires_authentication(client):
    response = client.post("/api/posts", json={"title": "x", "body": "y"})
    assert response.status_code == 401


def test_create_post_validation(client):
    headers = bearer(client)
    assert client.post("/api/posts", json={"title": "", "body": "x"}, headers=headers).status_code == 400
    assert client.post("/api/posts", json={"title": "x"}, headers=headers).status_code == 400
    assert (
        client.post("/api/posts", json={"title": "x" * 121, "body": "y"}, headers=headers).status_code
        == 400
    )


def test_stored_xss_is_html_escaped_on_output(client):
    headers = bearer(client)
    payload = "<script>alert('xss')</script>"
    created = client.post(
        "/api/posts", json={"title": payload, "body": payload}, headers=headers
    )
    assert created.status_code == 201
    assert "<script>" not in created.get_data(as_text=True)
    assert "&lt;script&gt;" in created.get_json()["title"]

    listing = client.get("/api/data", headers=headers)
    assert "<script>" not in listing.get_data(as_text=True)
    assert listing.get_json()["posts"][0]["title"] == (
        "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    )


def test_sql_metacharacters_are_stored_literally(client, app):
    headers = bearer(client)
    payload = "'; DROP TABLE posts; --"
    created = client.post("/api/posts", json={"title": payload, "body": payload}, headers=headers)
    assert created.status_code == 201

    listing = client.get("/api/data", headers=headers)
    assert listing.status_code == 200
    assert listing.get_json()["posts"][0]["title"] == "&#x27;; DROP TABLE posts; --"

    with app.app_context():
        from app.db import get_db

        assert get_db().execute("SELECT COUNT(*) AS n FROM posts").fetchone()["n"] == 1


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "no-referrer"


def _token(app, **overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "1",
        "username": "alice",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "iss": app.config["JWT_ISSUER"],
        "aud": app.config["JWT_AUDIENCE"],
    }
    claims.update(overrides)
    return jwt.encode(claims, app.config["SECRET_KEY"], algorithm="HS256")


def test_tampered_token_rejected(client):
    token = login(client).get_json()["access_token"]
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    response = client.get("/api/data", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


def test_expired_token_rejected(client, app):
    token = _token(app, exp=datetime.now(timezone.utc) - timedelta(seconds=5))
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_alg_none_token_rejected(client, app):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "1",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": app.config["JWT_ISSUER"],
            "aud": app.config["JWT_AUDIENCE"],
        },
        key="",
        algorithm="none",
    )
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_signed_with_other_key_rejected(client, app):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "1",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": app.config["JWT_ISSUER"],
            "aud": app.config["JWT_AUDIENCE"],
        },
        "attacker-controlled-secret-key-0123456789abcdef",
        algorithm="HS256",
    )
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_for_deleted_user_rejected(client, app):
    token = _token(app, sub="9999")
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_malformed_authorization_header(client):
    assert client.get("/api/data", headers={"Authorization": "Basic abc"}).status_code == 401
    assert client.get("/api/data", headers={"Authorization": "Bearer"}).status_code == 401
