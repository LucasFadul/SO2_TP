"""Modulo iv: analisis de logs."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional


IP_PATTERN = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})")
FAILED_LOGIN_PATTERNS = ("Failed password", "authentication failure", "Invalid user")
HTTP_SCANNER_PATTERNS = ("/.env", "/wp-admin", "/phpmyadmin", " 403 ", " 404 ")


def read_lines(paths: Iterable[str]) -> List[str]:
    lines: List[str] = []
    for path in paths:
        file_path = Path(path)
        if file_path.exists():
            lines.extend(file_path.read_text(errors="ignore").splitlines())
    return lines


def extract_ip(line: str) -> Optional[str]:
    match = IP_PATTERN.search(line)
    return match.group("ip") if match else None


def analyze_lines(
    lines: Iterable[str],
    failed_login_limit: int = 5,
    http_scanner_limit: int = 30,
) -> List[dict]:
    failed_logins: Counter[str] = Counter()
    http_scanners: Counter[str] = Counter()

    for line in lines:
        ip = extract_ip(line)
        if not ip:
            continue
        if any(pattern in line for pattern in FAILED_LOGIN_PATTERNS):
            failed_logins[ip] += 1
        if any(pattern in line for pattern in HTTP_SCANNER_PATTERNS):
            http_scanners[ip] += 1

    alarms: List[dict] = []
    for ip, count in failed_logins.items():
        if count > failed_login_limit:
            alarms.append(
                {
                    "tipo_alarma": "FAILED_LOGIN_MULTIPLE",
                    "modulo": "log_analyzer",
                    "ip_origen": ip,
                    "severidad": "alta",
                    "detalle": f"{count} fallos de autenticacion desde {ip}",
                }
            )

    for ip, count in http_scanners.items():
        if count > http_scanner_limit:
            alarms.append(
                {
                    "tipo_alarma": "SCANNER_HTTP",
                    "modulo": "log_analyzer",
                    "ip_origen": ip,
                    "severidad": "media",
                    "detalle": f"{count} eventos HTTP sospechosos desde {ip}",
                }
            )

    return alarms


def run_check() -> List[dict]:
    paths = (
        "/var/log/secure",
        "/var/log/messages",
        "/var/log/httpd/access_log",
        "/var/log/httpd/error_log",
    )
    return analyze_lines(read_lines(paths))
