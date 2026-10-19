"""Application factory for the HDU IS Lab 1 secure REST API."""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .api import api_bp
from .auth import auth_bp
from .config import Config
from .db import init_app as init_db_app
from .security import install_security, login_limiter


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    logging.basicConfig(level=logging.INFO)

    init_db_app(app)
    install_security(app)
    app.extensions["login_limiter"] = login_limiter(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.get("/health")
    def health():  # pragma: no cover - trivial
        return jsonify(status="ok")

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        response = jsonify(error=error.name, message=error.description)
        response.status_code = error.code
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):  # pragma: no cover - defensive
        app.logger.exception("Unhandled error: %s", error)
        return jsonify(error="Internal Server Error", message="Unexpected server error"), 500

    return app
