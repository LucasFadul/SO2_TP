"""Acciones sobre usuarios del sistema."""

from __future__ import annotations

import subprocess
from typing import List


def build_lock_user_command(username: str) -> List[str]:
    return ["passwd", "-l", username]


def lock_user(username: str, dry_run: bool = True) -> dict:
    command = build_lock_user_command(username)
    if dry_run:
        return {"accion": "lock_user", "usuario": username, "dry_run": True, "command": command, "ok": True}

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "accion": "lock_user",
        "usuario": username,
        "dry_run": False,
        "command": command,
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

