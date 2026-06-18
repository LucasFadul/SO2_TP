"""Acciones preventivas sobre archivos sospechosos o criticos."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List


def build_protect_file_command(path: str) -> List[str]:
    return ["chmod", "go-w", path]


def protect_file(path: str, dry_run: bool = True) -> dict:
    command = build_protect_file_command(path)
    if dry_run:
        return {
            "accion": "protect_file",
            "archivo": path,
            "dry_run": True,
            "command": command,
            "ok": True,
        }

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "accion": "protect_file",
        "archivo": path,
        "dry_run": False,
        "command": command,
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def quarantine_file(path: str, dry_run: bool = True) -> dict:
    source = Path(path)
    destination_dir = Path("/var/tmp/hips_quarantine")
    destination = destination_dir / source.name
    command = ["mv", str(source), str(destination)]

    if dry_run:
        return {
            "accion": "quarantine_file",
            "archivo": path,
            "destino": str(destination),
            "dry_run": True,
            "command": command,
            "ok": True,
        }

    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return {
            "accion": "quarantine_file",
            "archivo": path,
            "destino": str(destination),
            "dry_run": False,
            "command": command,
            "ok": True,
        }
    except OSError as exc:
        return {
            "accion": "quarantine_file",
            "archivo": path,
            "destino": str(destination),
            "dry_run": False,
            "command": command,
            "ok": False,
            "error": str(exc),
        }
