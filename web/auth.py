"""Utilidades basicas de autenticacion."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os


PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 260000


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
    return hmac.compare_digest(
        base64.b64encode(actual_digest).decode("ascii"),
        expected_digest,
    )
