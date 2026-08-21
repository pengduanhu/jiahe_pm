from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3

from utils import now_iso


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return salt, password_hash.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return hmac.compare_digest(actual_hash, expected_hash)


def create_session(conn: sqlite3.Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO auth_sessions (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, now_iso()),
    )
    return token


def public_user(user: sqlite3.Row | None) -> dict | None:
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "role_permissions": user["role_permissions"] if "role_permissions" in user.keys() else "[]",
        "status": user["status"],
        "last_login": user["last_login"],
    }
