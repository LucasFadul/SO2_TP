"""Acciones sobre servicios systemd."""

from __future__ import annotations

import subprocess
from typing import List


def build_stop_service_command(service: str) -> List[str]:
    return ["systemctl", "stop", service]


def stop_service(service: str, dry_run: bool = True) -> dict:
    command = build_stop_service_command(service)
    if dry_run:
        return {"accion": "stop_service", "service": service, "dry_run": True, "command": command, "ok": True}

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "accion": "stop_service",
        "service": service,
        "dry_run": False,
        "command": command,
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

