"""Modulo iv: analisis de logs."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable, List, Optional, Set


IP_PATTERN = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})")
FAILED_LOGIN_PATTERNS = ("Failed password", "authentication failure", "Invalid user")
HTTP_SCANNER_PATTERNS = ("/.env", "/wp-admin", "/phpmyadmin", " 403 ", " 404 ")
MAIL_ANOMALY_PATTERNS = (
    "SASL authentication failed",
    "Relay access denied",
    "authentication failed",
    "too many errors",
    "lost connection after AUTH",
)
USER_PATTERNS = (
    re.compile(r"Invalid user (?P<user>\S+)"),
    re.compile(r"for (?P<user>\S+) from"),
)


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


def extract_user(line: str) -> Optional[str]:
    for pattern in USER_PATTERNS:
        match = pattern.search(line)
        if match:
            return match.group("user")
    return None


def analyze_sshd_lines(
    lines: Iterable[str],
    failed_limit: int = 5,
    distinct_user_limit: int = 5,
) -> List[dict]:
    failed_by_ip: Counter[str] = Counter()
    users_by_ip: DefaultDict[str, Set[str]] = defaultdict(set)

    for line in lines:
        if "Failed password" not in line and "Invalid user" not in line:
            continue
        ip = extract_ip(line)
        if not ip:
            continue
        failed_by_ip[ip] += 1
        user = extract_user(line)
        if user:
            users_by_ip[ip].add(user)

    alarms: List[dict] = []
    for ip, count in failed_by_ip.items():
        if count > failed_limit:
            alarms.append(
                {
                    "tipo_alarma": "FAILED_LOGIN_MULTIPLE",
                    "modulo": "log_analyzer",
                    "ip_origen": ip,
                    "severidad": "alta",
                    "detalle": f"{count} intentos fallidos desde {ip}",
                }
            )
        if len(users_by_ip[ip]) > distinct_user_limit:
            alarms.append(
                {
                    "tipo_alarma": "CREDENTIAL_STUFFING",
                    "modulo": "log_analyzer",
                    "ip_origen": ip,
                    "severidad": "critica",
                    "detalle": f"{len(users_by_ip[ip])} usuarios distintos probados desde {ip}",
                }
            )
    return alarms


def analyze_lines(
    lines: Iterable[str],
    failed_login_limit: int = 5,
    http_scanner_limit: int = 30,
    mail_anomaly_limit: int = 10,
) -> List[dict]:
    failed_logins: Counter[str] = Counter()
    http_scanners: Counter[str] = Counter()
    mail_anomalies: Counter[str] = Counter()

    for line in lines:
        ip = extract_ip(line)
        if not ip:
            continue
        if any(pattern in line for pattern in FAILED_LOGIN_PATTERNS):
            failed_logins[ip] += 1
        if any(pattern in line for pattern in HTTP_SCANNER_PATTERNS):
            http_scanners[ip] += 1
        if any(pattern in line for pattern in MAIL_ANOMALY_PATTERNS):
            mail_anomalies[ip] += 1

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

    for ip, count in mail_anomalies.items():
        if count > mail_anomaly_limit:
            alarms.append(
                {
                    "tipo_alarma": "MAIL_ANOMALY",
                    "modulo": "log_analyzer",
                    "ip_origen": ip,
                    "severidad": "media",
                    "detalle": f"{count} eventos sospechosos de correo desde {ip}",
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
