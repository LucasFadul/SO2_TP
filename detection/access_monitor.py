"""Compatibilidad para intentos de acceso invalidos.

La deteccion real de logs SSH vive en detection.log_analyzer, que es el
modulo seleccionado para el TP.
"""

from __future__ import annotations

from typing import Iterable, List

from detection.log_analyzer import analyze_sshd_lines

def analyze_access_lines(
    lines: Iterable[str],
    failed_limit: int = 5,
    distinct_user_limit: int = 5,
) -> List[dict]:
    return analyze_sshd_lines(
        lines,
        failed_limit=failed_limit,
        distinct_user_limit=distinct_user_limit,
    )


def run_check() -> List[dict]:
    try:
        with open("/var/log/secure", "r", encoding="utf-8", errors="ignore") as file_obj:
            return analyze_access_lines(file_obj)
    except FileNotFoundError:
        return []
