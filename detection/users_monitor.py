"""Modulo ii: usuarios conectados."""

from __future__ import annotations

import subprocess
from typing import List, Optional, Set


def list_logged_users() -> str:
    result = subprocess.run(["who"], check=False, text=True, capture_output=True)
    return result.stdout


def run_check(allowed_users: Optional[Set[str]] = None) -> List[dict]:
    allowed_users = allowed_users or set()
    alarms: List[dict] = []

    for line in list_logged_users().splitlines():
        parts = line.split()
        if not parts:
            continue
        username = parts[0]
        if allowed_users and username not in allowed_users:
            alarms.append(
                {
                    "tipo_alarma": "USUARIO_SOSPECHOSO",
                    "modulo": "users_monitor",
                    "ip_origen": parts[-1].strip("()") if len(parts) >= 5 else None,
                    "severidad": "media",
                    "detalle": f"Usuario conectado no esperado: {username}",
                }
            )

    return alarms
