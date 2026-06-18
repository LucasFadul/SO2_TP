"""Modulo i: integridad de archivos criticos."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_FILES = ("/etc/passwd", "/etc/shadow")


def calculate_sha256(path: str) -> str:
    """Return the SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_integrity(
    baseline: Dict[str, str],
    files: Iterable[str] = DEFAULT_FILES,
) -> List[dict]:
    alarms: List[dict] = []
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            continue

        expected_hash = baseline.get(file_path)
        if not expected_hash:
            continue

        try:
            current_hash = calculate_sha256(file_path)
        except OSError:
            continue
        if expected_hash and expected_hash != current_hash:
            alarms.append(
                {
                    "tipo_alarma": "MODIFICACION_ARCHIVO",
                    "modulo": "file_integrity",
                    "ip_origen": None,
                    "severidad": "alta",
                    "detalle": f"Hash distinto para {file_path}",
                }
            )
    return alarms


def run_check() -> List[dict]:
    return check_integrity(baseline={})
