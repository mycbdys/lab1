"""Configuration loaded from the environment (never hard-code secrets)."""

from __future__ import annotations

import os
import secrets
from datetime import timedelta


def _secret_key() -> str:
    """Return the deployment secret or a random per-process development key."""
    return os.environ.get("SECRET_KEY") or secrets.token_hex(32)


class Config:  # pylint: disable=too-few-public-methods
    SECRET_KEY = _secret_key()
    JWT_ALGORITHM = "HS256"
    JWT_ISSUER = os.environ.get("JWT_ISSUER", "hdu-is-lab1")
    JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "hdu-is-lab1-api")
    JWT_TTL = timedelta(minutes=int(os.environ.get("JWT_TTL_MINUTES", "15")))
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
    DATABASE = os.environ.get(
        "DATABASE",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "lab1.sqlite3"),
    )
    LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_WINDOW_SECONDS = int(os.environ.get("LOGIN_WINDOW_SECONDS", "60"))
    MAX_CONTENT_LENGTH = 64 * 1024
    JSON_SORT_KEYS = False
