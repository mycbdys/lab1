"""Authentication, output encoding and defensive HTTP headers."""

from __future__ import annotations

import html
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, g, jsonify, request

from .db import get_db

# A random unusable hash: verifying against it keeps the "unknown user" path as
# slow as the "wrong password" path, preventing username enumeration by timing.
_DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(24), bcrypt.gensalt(rounds=12))


class LoginLimiter:
    """Small in-memory sliding-window limiter for failed login attempts."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.max_attempts:
                return False
            events.append(now)
            return True

    def reset_key(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


def login_limiter(app) -> LoginLimiter:
    return LoginLimiter(app.config["LOGIN_MAX_ATTEMPTS"], app.config["LOGIN_WINDOW_SECONDS"])


def hash_password(password: str) -> str:
    """Hash a password with bcrypt and a per-password salt."""
    rounds = current_app.config["BCRYPT_ROUNDS"]
    digest = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds))
    return digest.decode("ascii")


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Constant-time bcrypt verification; never raises on malformed input."""
    if not stored_hash:
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def escape_text(value: str) -> str:
    """HTML-encode untrusted text for safe embedding in any HTML context."""
    return html.escape(value, quote=True)


def create_access_token(user_id: int, username: str) -> tuple[str, int]:
    """Issue a short-lived, signed HS256 JWT with issuer/audience claims."""
    now = datetime.now(timezone.utc)
    ttl = current_app.config["JWT_TTL"]
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=int(ttl.total_seconds())),
        "iss": current_app.config["JWT_ISSUER"],
        "aud": current_app.config["JWT_AUDIENCE"],
        "jti": secrets.token_hex(16),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token, int(ttl.total_seconds())


def _unauthorized(message: str = "Authentication required"):
    response = jsonify(error="Unauthorized", message=message)
    response.status_code = 401
    response.headers["WWW-Authenticate"] = 'Bearer realm="api"'
    return response


def auth_required(view):
    """Verify the Bearer JWT and attach the current user to ``g``."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return _unauthorized("Missing Bearer token")

        try:
            claims = jwt.decode(
                token.strip(),
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],  # pinned: rejects alg=none and RS/HS confusion
                audience=current_app.config["JWT_AUDIENCE"],
                issuer=current_app.config["JWT_ISSUER"],
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
            user_id = int(claims["sub"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            return _unauthorized("Invalid or expired token")

        user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            return _unauthorized("Invalid or expired token")

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def install_security(app) -> None:
    """Attach hardening headers to every response."""

    @app.after_request
    def set_security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.path.startswith(("/api/", "/auth/")):
            response.headers["Cache-Control"] = "no-store"
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
