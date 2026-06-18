"""Modulo vii: directorio /tmp."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Iterable, List


SCRIPT_EXTENSIONS = (".sh", ".py", ".pl", ".php")


def is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def scan_tmp(paths: Iterable[Path]) -> List[dict]:
    alarms: List[dict] = []
    for path in paths:
        try:
            if path.is_file() and (is_executable(path) or path.suffix in SCRIPT_EXTENSIONS):
                alarms.append(
                    {
                        "tipo_alarma": "ARCHIVO_TMP_SOSPECHOSO",
                        "modulo": "tmp_monitor",
                        "ip_origen": None,
                        "severidad": "media",
                        "archivo": str(path),
                        "detalle": f"Archivo ejecutable o script en /tmp: {path}",
                    }
                )
        except OSError:
            continue
    return alarms


def run_check(tmp_dir: str = "/tmp") -> List[dict]:
    paths = (Path(root) / name for root, _, files in os.walk(tmp_dir) for name in files)
    return scan_tmp(paths)
