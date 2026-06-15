"""Read real sshd logs from journalctl and insert access alarms."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from db.models import insert_alarm
from detection.access_monitor import analyze_access_lines


def read_sshd_journal(since: str) -> List[str]:
    command = ["journalctl", "-u", "sshd", "--since", since, "--no-pager"]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo leer journalctl")
    return result.stdout.splitlines()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    since = os.getenv("HIPS_SSH_JOURNAL_SINCE", "10 minutes ago")
    failed_limit = int(os.getenv("HIPS_FAILED_LOGIN_LIMIT", "5"))
    distinct_user_limit = int(os.getenv("HIPS_DISTINCT_USER_LIMIT", "5"))

    lines = read_sshd_journal(since)
    alarms = analyze_access_lines(
        lines,
        failed_limit=failed_limit,
        distinct_user_limit=distinct_user_limit,
    )

    print(f"Lineas sshd leidas: {len(lines)}")
    print(f"Alarmas detectadas: {len(alarms)}")

    for alarm in alarms:
        insert_alarm(alarm)
        print(
            "Insertada: "
            f"{alarm['tipo_alarma']} | {alarm.get('ip_origen') or 'N/A'} | "
            f"{alarm['modulo']} | {alarm['detalle']}"
        )


if __name__ == "__main__":
    main()
