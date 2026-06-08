"""Modulo vi: procesos con alto consumo de recursos."""

from __future__ import annotations

import subprocess
from typing import List


def get_process_table() -> str:
    result = subprocess.run(
        ["ps", "-eo", "pid,user,pcpu,pmem,comm", "--sort=-pcpu"],
        check=False,
        text=True,
        capture_output=True,
    )
    return result.stdout


def run_check(cpu_limit: float = 90.0, memory_limit: float = 90.0) -> List[dict]:
    alarms: List[dict] = []
    for line in get_process_table().splitlines()[1:]:
        parts = line.split(None, 4)
        if len(parts) != 5:
            continue
        pid, user, cpu, memory, command = parts
        if float(cpu) >= cpu_limit or float(memory) >= memory_limit:
            alarms.append(
                {
                    "tipo_alarma": "PROCESO_ALTO_CONSUMO",
                    "modulo": "process_monitor",
                    "ip_origen": None,
                    "severidad": "media",
                    "detalle": f"PID {pid} usuario {user} comando {command} CPU {cpu}% MEM {memory}%",
                }
            )
    return alarms

