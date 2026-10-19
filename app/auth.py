"""POST /auth/login - credential verification and JWT issuance."""

from __future__ import annotations

import re

from flask import Blueprint, current_app, jsonify, request

from .db import get_db
from .security import create_access_token, verify_password

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
GENERIC_ERROR = "Invalid username or password"
AUTH_SCHEME = "Bearer"


def _bad_request(message: str):
    return jsonify(error="Bad Request", message=message), 400


@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("A JSON object with username and password is required")

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return _bad_request("username and password must be strings")
    username = username.strip()
    if not USERNAME_RE.fullmatch(username):
        return _bad_request("username must be 3-32 characters (letters, digits, . _ -)")
    if not 8 <= len(password) <= 72:
        return _bad_request("password must be 8-72 characters")

    limiter = current_app.extensions["login_limiter"]
    limiter_key = f"{request.remote_addr}|{username.lower()}"
    if not limiter.allow(limiter_key):
        response = jsonify(error="Too Many Requests", message="Too many login attempts, retry later")
        response.status_code = 429
        response.headers["Retry-After"] = str(current_app.config["LOGIN_WINDOW_SECONDS"])
        return response

    user = get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()

    if not verify_password(password, user["password_hash"] if user else None):
        return jsonify(error="Unauthorized", message=GENERIC_ERROR), 401

    limiter.reset_key(limiter_key)
    token, expires_in = create_access_token(user["id"], user["username"])
    return (
        jsonify(access_token=token, token_type=AUTH_SCHEME, expires_in=expires_in),
        200,
    )
