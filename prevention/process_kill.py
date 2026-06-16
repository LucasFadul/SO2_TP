"""Acciones de finalizacion de procesos."""

from __future__ import annotations

import os
import signal
import time


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_process(pid: int, dry_run: bool = True) -> dict:
    if dry_run:
        return {
            "accion": "kill_process",
            "pid": pid,
            "dry_run": True,
            "ok": True,
            "metodo": "SIGTERM_then_SIGKILL",
        }

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(5)
        if process_exists(pid):
            os.kill(pid, signal.SIGKILL)
            return {
                "accion": "kill_process",
                "pid": pid,
                "dry_run": False,
                "ok": True,
                "metodo": "SIGKILL",
            }
        return {
            "accion": "kill_process",
            "pid": pid,
            "dry_run": False,
            "ok": True,
            "metodo": "SIGTERM",
        }
    except OSError as exc:
        return {
            "accion": "kill_process",
            "pid": pid,
            "dry_run": False,
            "ok": False,
            "error": str(exc),
        }
