"""General HIPS runner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable, List, Mapping

from dotenv import load_dotenv

from db.models import (
    get_module_config,
    insert_alarm,
    insert_prevention_action,
    set_module_config,
)
from detection.log_analyzer import analyze_lines
from prevention.firewall import block_ip


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SECURE_LOG_PATH = Path("/var/log/secure")
DEFAULT_LOG_PATHS = (
    DEFAULT_SECURE_LOG_PATH,
    Path("/var/log/httpd/access_log"),
    Path("/var/log/httpd/access.log"),
    Path("/var/log/nginx/access.log"),
    Path("/var/log/maillog"),
)


def read_sshd_journal(since: str) -> List[str]:
    command = ["journalctl", "-u", "sshd", "--since", since, "--no-pager"]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo leer journalctl")
    return result.stdout.splitlines()


def offset_param(path: Path) -> str:
    return f"log_offset:{path}"


def read_new_log_lines(path: Path) -> List[str]:
    offset_value = get_module_config("log_analyzer", offset_param(path))
    offset = int(offset_value) if offset_value else 0
    size = path.stat().st_size
    if offset > size:
        offset = 0

    with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
        file_obj.seek(offset)
        data = file_obj.read()
        new_offset = file_obj.tell()

    set_module_config("log_analyzer", offset_param(path), new_offset)
    return data.splitlines()


def configured_log_paths() -> List[Path]:
    raw_paths = os.getenv("HIPS_LOG_ANALYZER_PATHS")
    if not raw_paths:
        return list(DEFAULT_LOG_PATHS)
    return [Path(path.strip()) for path in raw_paths.split(",") if path.strip()]


def read_configured_logs() -> tuple[List[str], List[str]]:
    lines: List[str] = []
    sources: List[str] = []

    for path in configured_log_paths():
        if not path.exists():
            continue
        try:
            new_lines = read_new_log_lines(path)
        except PermissionError:
            print(f"No se pudo leer {path}: permiso denegado.")
            continue
        if new_lines:
            lines.extend(new_lines)
        sources.append(str(path))

    return lines, sources


def read_journal_fallback() -> tuple[List[str], str]:
    since = os.getenv("HIPS_SSH_JOURNAL_SINCE", "10 minutes ago")
    return read_sshd_journal(since), f"journalctl -u sshd --since '{since}'"


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


def run_log_analyzer() -> List[dict]:
    failed_limit = int(os.getenv("HIPS_FAILED_LOGIN_LIMIT", "5"))
    http_limit = int(os.getenv("HIPS_HTTP_404_LIMIT", "30"))
    mail_limit = int(os.getenv("HIPS_MAIL_ANOMALY_LIMIT", "10"))

    lines, sources = read_configured_logs()
    if not lines:
        journal_lines, journal_source = read_journal_fallback()
        lines.extend(journal_lines)
        sources.append(journal_source)

    alarms = analyze_lines(
        lines,
        failed_login_limit=failed_limit,
        http_scanner_limit=http_limit,
        mail_anomaly_limit=mail_limit,
    )

    print(
        "Modulo log_analyzer: "
        f"fuentes={', '.join(sources) or 'N/A'} "
        f"lineas leidas={len(lines)} alarmas={len(alarms)}"
    )
    return alarms


def run_enabled_modules() -> Iterable[dict]:
    yield from run_log_analyzer()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    prevention_dry_run = os.getenv("HIPS_PREVENTION_DRY_RUN", "true").lower() == "true"

    alarms = list(run_enabled_modules())
    print(f"Alarmas detectadas: {len(alarms)}")

    for alarm in alarms:
        register_alarm_with_prevention(alarm, prevention_dry_run=prevention_dry_run)


if __name__ == "__main__":
    main()
