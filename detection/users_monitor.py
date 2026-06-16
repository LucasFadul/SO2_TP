"""Modulo ii: usuarios conectados."""

from __future__ import annotations

import ipaddress
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


NOLOGIN_SHELLS = {"/sbin/nologin", "/usr/sbin/nologin", "/bin/false"}
DEFAULT_ALLOWED_NETWORKS = ("192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12")


def list_logged_users() -> str:
    result = subprocess.run(["who"], check=False, text=True, capture_output=True)
    return result.stdout


def read_user_shells(passwd_path: str = "/etc/passwd") -> Dict[str, str]:
    shells: Dict[str, str] = {}
    path = Path(passwd_path)
    if not path.exists():
        return shells

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 7:
            shells[parts[0]] = parts[6]
    return shells


def parse_origin(parts: List[str]) -> Optional[str]:
    if len(parts) < 5:
        return None
    value = parts[-1].strip("()")
    if value.startswith(":"):
        return None
    return value


def ip_in_allowed_networks(ip_value: Optional[str], networks: Iterable[str]) -> bool:
    if not ip_value:
        return True
    try:
        ip_obj = ipaddress.ip_address(ip_value)
    except ValueError:
        return True
    return any(ip_obj in ipaddress.ip_network(network, strict=False) for network in networks)


def build_alarm(username: str, ip_origen: Optional[str], severidad: str, detalle: str) -> dict:
    return {
        "tipo_alarma": "USUARIO_SOSPECHOSO",
        "modulo": "users_monitor",
        "ip_origen": ip_origen,
        "severidad": severidad,
        "usuario": username,
        "detalle": detalle,
    }


def run_check(
    allowed_users: Optional[Set[str]] = None,
    allowed_networks: Optional[Iterable[str]] = None,
    max_sessions: int = 2,
    user_shells: Optional[Dict[str, str]] = None,
) -> List[dict]:
    allowed_users = allowed_users or set()
    allowed_networks = tuple(allowed_networks or DEFAULT_ALLOWED_NETWORKS)
    user_shells = user_shells if user_shells is not None else read_user_shells()
    alarms: List[dict] = []
    sessions_by_user: Counter[str] = Counter()
    first_ip_by_user: Dict[str, Optional[str]] = {}

    for line in list_logged_users().splitlines():
        parts = line.split()
        if not parts:
            continue
        username = parts[0]
        ip_origen = parse_origin(parts)
        sessions_by_user[username] += 1
        first_ip_by_user.setdefault(username, ip_origen)

        if allowed_users and username not in allowed_users:
            alarms.append(
                build_alarm(
                    username,
                    ip_origen,
                    "media",
                    f"Usuario conectado no esperado: {username}",
                )
            )

        if user_shells.get(username) in NOLOGIN_SHELLS:
            alarms.append(
                build_alarm(
                    username,
                    ip_origen,
                    "alta",
                    f"Usuario con shell no interactiva conectado: {username}",
                )
            )

        if not ip_in_allowed_networks(ip_origen, allowed_networks):
            alarms.append(
                build_alarm(
                    username,
                    ip_origen,
                    "alta",
                    f"Conexion desde red no permitida: {username} desde {ip_origen}",
                )
            )

    for username, count in sessions_by_user.items():
        if count > max_sessions:
            alarms.append(
                build_alarm(
                    username,
                    first_ip_by_user.get(username),
                    "media",
                    f"Usuario con {count} sesiones simultaneas: {username}",
                )
            )

    return alarms
