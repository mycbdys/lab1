"""SQLite helpers. Every statement uses bound parameters (no string concatenation)."""

from __future__ import annotations

import os
import sqlite3

from flask import current_app, g

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db() -> sqlite3.Connection:
    """Open (once per request) a connection with safe defaults."""
    if "db" not in g:
        database = current_app.config["DATABASE"]
        os.makedirs(os.path.dirname(database) or ".", exist_ok=True)
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        g.db = connection
    return g.db


def close_db(_exception: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    connection = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as handle:
        connection.executescript(handle.read())
    connection.commit()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
