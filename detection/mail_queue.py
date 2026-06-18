"""Modulo v: cola de correo."""

from __future__ import annotations

import subprocess
from typing import List


def get_mailq_output() -> str:
    try:
        result = subprocess.run(["mailq"], check=False, text=True, capture_output=True)
    except FileNotFoundError:
        return "Mail queue is empty"
    return result.stdout


def count_queued_messages(mailq_output: str) -> int:
    if "Mail queue is empty" in mailq_output:
        return 0
    return sum(1 for line in mailq_output.splitlines() if line and not line.startswith("-"))


def run_check(limit: int = 100) -> List[dict]:
    count = count_queued_messages(get_mailq_output())
    if count > limit:
        return [
            {
                "tipo_alarma": "MAIL_QUEUE_ALTA",
                "modulo": "mail_queue",
                "ip_origen": None,
                "severidad": "media",
                "service": "postfix",
                "conteo": count,
                "detalle": f"Cola de correo con {count} mensajes",
            }
        ]
    return []
