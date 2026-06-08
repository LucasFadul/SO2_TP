"""Acciones de finalizacion de procesos."""

from __future__ import annotations

import os
import signal


def kill_process(pid: int, dry_run: bool = True) -> dict:
    if dry_run:
        return {"accion": "kill_process", "pid": pid, "dry_run": True, "ok": True}

    try:
        os.kill(pid, signal.SIGKILL)
        return {"accion": "kill_process", "pid": pid, "dry_run": False, "ok": True}
    except OSError as exc:
        return {"accion": "kill_process", "pid": pid, "dry_run": False, "ok": False, "error": str(exc)}

