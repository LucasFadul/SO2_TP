"""Modulo x: intentos de acceso invalidos."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import DefaultDict, Iterable, List, Optional, Set


IP_PATTERN = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})")
USER_PATTERNS = (
    re.compile(r"Invalid user (?P<user>\S+)"),
    re.compile(r"for (?P<user>\S+) from"),
)


def extract_ip(line: str) -> Optional[str]:
    match = IP_PATTERN.search(line)
    return match.group("ip") if match else None


def extract_user(line: str) -> Optional[str]:
    for pattern in USER_PATTERNS:
        match = pattern.search(line)
        if match:
            return match.group("user")
    return None


def analyze_access_lines(
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
                    "tipo_alarma": "ACCESO_INVALIDO_REPETIDO",
                    "modulo": "access_monitor",
                    "ip_origen": ip,
                    "severidad": "alta",
                    "detalle": f"{count} intentos fallidos desde {ip}",
                }
            )
        if len(users_by_ip[ip]) > distinct_user_limit:
            alarms.append(
                {
                    "tipo_alarma": "CREDENTIAL_STUFFING",
                    "modulo": "access_monitor",
                    "ip_origen": ip,
                    "severidad": "critica",
                    "detalle": f"{len(users_by_ip[ip])} usuarios distintos probados desde {ip}",
                }
            )
    return alarms


def run_check() -> List[dict]:
    try:
        with open("/var/log/secure", "r", encoding="utf-8", errors="ignore") as file_obj:
            return analyze_access_lines(file_obj)
    except FileNotFoundError:
        return []
