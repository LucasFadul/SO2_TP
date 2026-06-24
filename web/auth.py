"""Utilidades basicas de autenticacion."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from typing import Optional


PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 260000
SESSION_COOKIE_NAME = "hips_session"
DEFAULT_SESSION_MAX_AGE = 8 * 60 * 60


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_digest = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password_hash: str, password: str) -> bool:
    try:
        algorithm, iterations, encoded_salt, expected_digest = password_hash.split("$", 3)
        if algorithm != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False

        salt = base64.b64decode(encoded_salt.encode("ascii"))
        actual_digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
    except (binascii.Error, TypeError, ValueError):
        return False

    return hmac.compare_digest(
        base64.b64encode(actual_digest).decode("ascii"),
        expected_digest,
    )


def session_secret() -> bytes:
    value = os.getenv("HIPS_SESSION_SECRET") or os.getenv("HIPS_DB_PASSWORD")
    if not value:
        raise RuntimeError("Falta HIPS_SESSION_SECRET en .env")
    return value.encode("utf-8")


def session_max_age() -> int:
    return int(os.getenv("HIPS_SESSION_MAX_AGE", str(DEFAULT_SESSION_MAX_AGE)))


def encode_session(username: str, now: Optional[int] = None) -> str:
    issued_at = int(now if now is not None else time.time())
    payload = {
        "username": username,
        "issued_at": issued_at,
        "expires_at": issued_at + session_max_age(),
    }
    encoded_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(
        session_secret(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_session(token: str, now: Optional[int] = None) -> Optional[str]:
    try:
        encoded_payload, supplied_signature = token.split(".", 1)
        expected_signature = hmac.new(
            session_secret(),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None

        padding = "=" * (-len(encoded_payload) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(encoded_payload + padding).decode("utf-8")
        )
        current_time = int(now if now is not None else time.time())
        if current_time >= int(payload["expires_at"]):
            return None
        username = str(payload["username"]).strip()
        return username or None
    except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
