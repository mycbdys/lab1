"""Shared pytest fixtures: isolated database, demo users and API client."""

from __future__ import annotations

import os
import shutil
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.db import get_db  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORDS = {"alice": "Alice#2026", "bob": "Bob#2026"}
RUNTIME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_runtime")


@pytest.fixture()
def workdir():
    """Per-test scratch directory created with inherited (writable) ACLs."""
    path = os.path.join(RUNTIME_DIR, uuid.uuid4().hex)
    os.makedirs(path, exist_ok=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def app(workdir):
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": os.path.join(workdir, "test.sqlite3"),
            "SECRET_KEY": "unit-test-secret-key-not-for-production",
            "BCRYPT_ROUNDS": 4,
            "LOGIN_MAX_ATTEMPTS": 5,
            "LOGIN_WINDOW_SECONDS": 60,
        }
    )
    with application.app_context():
        connection = get_db()
        for username, password in PASSWORDS.items():
            connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password)),
            )
        connection.commit()
    yield application
    with application.app_context():
        application.extensions["login_limiter"].reset()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username: str = "alice", password: str | None = None):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password or PASSWORDS[username]},
    )
    return response


def bearer(client, username: str = "alice") -> dict:
    token = login(client, username).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
