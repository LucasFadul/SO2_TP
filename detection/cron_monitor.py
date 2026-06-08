"""Modulo ix: archivos cron sospechosos."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


SUSPICIOUS_TOKENS = ("curl ", "wget ", "nc ", "bash -i", "/tmp/", "python -c", "base64")


def scan_cron_files(paths: Iterable[str]) -> List[dict]:
    alarms: List[dict] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        content = path.read_text(errors="ignore")
        for token in SUSPICIOUS_TOKENS:
            if token in content:
                alarms.append(
                    {
                        "tipo_alarma": "CRON_SOSPECHOSO",
                        "modulo": "cron_monitor",
                        "ip_origen": None,
                        "severidad": "alta",
                        "detalle": f"Token sospechoso '{token.strip()}' en {path}",
                    }
                )
    return alarms


def run_check() -> List[dict]:
    return scan_cron_files(("/etc/crontab", "/var/spool/cron/root"))

