"""General HIPS runner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable, List, Mapping

from dotenv import load_dotenv

from db.models import insert_alarm, insert_prevention_action
from detection.access_monitor import analyze_access_lines
from prevention.firewall import block_ip


PROJECT_ROOT = Path(__file__).resolve().parent


def read_sshd_journal(since: str) -> List[str]:
    command = ["journalctl", "-u", "sshd", "--since", since, "--no-pager"]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo leer journalctl")
    return result.stdout.splitlines()


def register_alarm_with_prevention(
    alarm: Mapping[str, object],
    prevention_dry_run: bool,
) -> None:
    alarm_id = insert_alarm(alarm)
    print(
        "Insertada: "
        f"{alarm['tipo_alarma']} | {alarm.get('ip_origen') or 'N/A'} | "
        f"{alarm['modulo']} | {alarm['detalle']}"
    )

    ip_origen = alarm.get("ip_origen")
    if not ip_origen:
        return

    result = block_ip(str(ip_origen), dry_run=prevention_dry_run)
    action_id = insert_prevention_action(
        alarma_id=alarm_id,
        accion=result["accion"],
        resultado=str(result),
    )
    print(
        "Prevencion registrada: "
        f"accion_id={action_id} | alarma_id={alarm_id} | "
        f"{result['accion']} | dry_run={result['dry_run']}"
    )


def run_access_monitor() -> List[dict]:
    since = os.getenv("HIPS_SSH_JOURNAL_SINCE", "10 minutes ago")
    failed_limit = int(os.getenv("HIPS_FAILED_LOGIN_LIMIT", "5"))
    distinct_user_limit = int(os.getenv("HIPS_DISTINCT_USER_LIMIT", "5"))

    lines = read_sshd_journal(since)
    alarms = analyze_access_lines(
        lines,
        failed_limit=failed_limit,
        distinct_user_limit=distinct_user_limit,
    )

    print(f"Modulo access_monitor: lineas sshd leidas={len(lines)} alarmas={len(alarms)}")
    return alarms


def run_enabled_modules() -> Iterable[dict]:
    yield from run_access_monitor()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    prevention_dry_run = os.getenv("HIPS_PREVENTION_DRY_RUN", "true").lower() == "true"

    alarms = list(run_enabled_modules())
    print(f"Alarmas detectadas: {len(alarms)}")

    for alarm in alarms:
        register_alarm_with_prevention(alarm, prevention_dry_run=prevention_dry_run)


if __name__ == "__main__":
    main()
