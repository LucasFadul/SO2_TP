"""Modulo iii: sniffers y modo promiscuo."""

from __future__ import annotations

import subprocess
from typing import Iterable, List, Optional


SNIFFER_PROCESS_NAMES = ("tcpdump", "wireshark", "tshark", "dumpcap", "ethereal")


def command_output(command: list[str]) -> str:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return result.stdout


def detect_promiscuous_interfaces(ip_link_output: str) -> List[str]:
    interfaces: List[str] = []
    current_iface: Optional[str] = None

    for line in ip_link_output.splitlines():
        if line and line[0].isdigit() and ": " in line:
            current_iface = line.split(": ", 2)[1].split("@", 1)[0]
            if "PROMISC" in line and current_iface:
                interfaces.append(current_iface)

    return interfaces


def detect_sniffer_processes(ps_output: str, names: Iterable[str] = SNIFFER_PROCESS_NAMES) -> List[str]:
    matches: List[str] = []
    for line in ps_output.splitlines():
        lowered = line.lower()
        if any(name in lowered for name in names):
            if "sniffer_detect.py" not in lowered:
                matches.append(line)
    return matches


def run_check(authorized: bool = False) -> List[dict]:
    if authorized:
        return []

    ip_link_output = command_output(["ip", "link"])
    ps_output = command_output(["ps", "aux"])

    alarms: List[dict] = []
    for iface in detect_promiscuous_interfaces(ip_link_output):
        alarms.append(
            {
                "tipo_alarma": "SNIFFER_DETECTADO",
                "modulo": "sniffer_detect",
                "ip_origen": None,
                "severidad": "alta",
                "detalle": f"Interfaz en modo promiscuo: {iface}",
            }
        )

    for process_line in detect_sniffer_processes(ps_output):
        alarms.append(
            {
                "tipo_alarma": "SNIFFER_DETECTADO",
                "modulo": "sniffer_detect",
                "ip_origen": None,
                "severidad": "alta",
                "detalle": f"Proceso sniffer detectado: {process_line}",
            }
        )

    return alarms
