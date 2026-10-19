"""Protected data endpoints: read the caller's posts and create a new post."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .db import get_db
from .security import auth_required, escape_text

api_bp = Blueprint("api", __name__)

TITLE_MAX = 120
BODY_MAX = 2000


def _serialize_post(row) -> dict:
    # Output encoding: stored text is untrusted and is escaped before it leaves
    # the API, so a client that injects the value into HTML cannot execute it.
    return {
        "id": row["id"],
        "title": escape_text(row["title"]),
        "body": escape_text(row["body"]),
        "created_at": row["created_at"],
    }


@api_bp.get("/api/data")
@auth_required
def get_data():
    user = g.current_user
    rows = get_db().execute(
        "SELECT id, title, body, created_at FROM posts WHERE user_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()
    return jsonify(username=user["username"], posts=[_serialize_post(row) for row in rows])


@api_bp.post("/api/posts")
@auth_required
def create_post():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Bad Request", message="A JSON object is required"), 400

    title = data.get("title")
    body = data.get("body")
    if not isinstance(title, str) or not isinstance(body, str):
        return jsonify(error="Bad Request", message="title and body must be strings"), 400

    title = title.strip()
    body = body.strip()
    if not 1 <= len(title) <= TITLE_MAX:
        return jsonify(error="Bad Request", message=f"title must be 1-{TITLE_MAX} characters"), 400
    if not 1 <= len(body) <= BODY_MAX:
        return jsonify(error="Bad Request", message=f"body must be 1-{BODY_MAX} characters"), 400

    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO posts (user_id, title, body) VALUES (?, ?, ?)",
        (g.current_user["id"], title, body),
    )
    connection.commit()
    row = connection.execute(
        "SELECT id, title, body, created_at FROM posts WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return jsonify(**_serialize_post(row)), 201
