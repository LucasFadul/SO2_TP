"""Modulo viii: deteccion DDoS usando log DNS provisto."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List


IP_PATTERN = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})")


def analyze_dns_lines(lines: Iterable[str], request_limit: int = 1000) -> List[dict]:
    requests_by_ip: Counter[str] = Counter()
    for line in lines:
        match = IP_PATTERN.search(line)
        if match:
            requests_by_ip[match.group("ip")] += 1

    return [
        {
            "tipo_alarma": "DDOS_DETECTADO",
            "modulo": "ddos_detect",
            "ip_origen": ip,
            "severidad": "alta",
            "detalle": f"{count} solicitudes DNS desde {ip}",
        }
        for ip, count in requests_by_ip.items()
        if count > request_limit
    ]


def run_check(log_path: str = "data/dns.log", request_limit: int = 1000) -> List[dict]:
    path = Path(log_path)
    if not path.exists():
        return []
    return analyze_dns_lines(path.read_text(errors="ignore").splitlines(), request_limit=request_limit)
