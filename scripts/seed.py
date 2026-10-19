"""Create the demo users used by the cURL walkthrough."""

from __future__ import annotations

from app import create_app
from app.db import get_db
from app.security import hash_password

DEMO_USERS = {
    "alice": "Alice#2026",
    "bob": "Bob#2026",
}


def main() -> None:
    app = create_app()
    with app.app_context():
        connection = get_db()
        for username, password in DEMO_USERS.items():
            existing = connection.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                print(f"user {username!r} already exists (id={existing['id']})")
                continue
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password)),
            )
            connection.commit()
            print(f"created user {username!r} (id={cursor.lastrowid})")
        print("demo credentials: alice/Alice#2026, bob/Bob#2026")


if __name__ == "__main__":
    main()
