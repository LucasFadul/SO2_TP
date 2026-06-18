"""Acciones preventivas sobre interfaces de red."""

from __future__ import annotations

import subprocess
from typing import List


def build_disable_promisc_command(interface: str) -> List[str]:
    return ["ip", "link", "set", interface, "promisc", "off"]


def disable_promiscuous_mode(interface: str, dry_run: bool = True) -> dict:
    command = build_disable_promisc_command(interface)
    if dry_run:
        return {
            "accion": "disable_promisc",
            "interfaz": interface,
            "dry_run": True,
            "command": command,
            "ok": True,
        }

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "accion": "disable_promisc",
        "interfaz": interface,
        "dry_run": False,
        "command": command,
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
