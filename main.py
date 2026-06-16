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
from detection.process_monitor import run_check as run_process_check
from detection.users_monitor import run_check as run_users_check
from prevention.firewall import block_ip
from prevention.process_kill import kill_process
from prevention.user_actions import lock_user


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

    result = run_prevention(alarm, dry_run=prevention_dry_run)
    if not result:
        return

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


def run_prevention(alarm: Mapping[str, object], dry_run: bool) -> dict | None:
    modulo = alarm.get("modulo")

    if modulo == "log_analyzer" and alarm.get("ip_origen"):
        return block_ip(str(alarm["ip_origen"]), dry_run=dry_run)

    if modulo == "process_monitor" and alarm.get("pid"):
        return kill_process(int(alarm["pid"]), dry_run=dry_run)

    if modulo == "users_monitor" and alarm.get("usuario"):
        return lock_user(str(alarm["usuario"]), dry_run=dry_run)

    return None


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


def allowed_users_from_env() -> set[str]:
    raw_users = os.getenv("HIPS_ALLOWED_USERS")
    if raw_users:
        return {user.strip() for user in raw_users.split(",") if user.strip()}

    default_user = os.getenv("SUDO_USER") or os.getenv("USER")
    return {default_user} if default_user else set()


def csv_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [value.strip() for value in raw_value.split(",") if value.strip()]


def run_users_monitor() -> List[dict]:
    allowed_users = allowed_users_from_env()
    allowed_networks = csv_env(
        "HIPS_ALLOWED_NETWORKS",
        "192.168.0.0/16,10.0.0.0/8,172.16.0.0/12",
    )
    max_sessions = int(os.getenv("HIPS_USERS_MAX_SESSIONS", "2"))
    alarms = run_users_check(
        allowed_users=allowed_users,
        allowed_networks=allowed_networks,
        max_sessions=max_sessions,
    )
    print(
        "Modulo users_monitor: "
        f"usuarios_permitidos={','.join(sorted(allowed_users)) or 'sin filtro'} "
        f"redes_permitidas={','.join(allowed_networks)} "
        f"max_sesiones={max_sessions} "
        f"alarmas={len(alarms)}"
    )
    return alarms


def run_process_monitor() -> List[dict]:
    cpu_limit = float(os.getenv("HIPS_CPU_LIMIT_PERCENT", "90"))
    memory_limit = float(os.getenv("HIPS_MEMORY_LIMIT_PERCENT", "90"))
    process_whitelist = csv_env("HIPS_PROCESS_WHITELIST", "postgres,rsync,find,dnf")
    alarms = run_process_check(
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
        process_whitelist=process_whitelist,
    )
    print(
        "Modulo process_monitor: "
        f"cpu_limit={cpu_limit} memory_limit={memory_limit} "
        f"whitelist={','.join(process_whitelist)} alarmas={len(alarms)}"
    )
    return alarms


def run_enabled_modules() -> Iterable[dict]:
    yield from run_log_analyzer()
    yield from run_users_monitor()
    yield from run_process_monitor()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    prevention_dry_run = os.getenv("HIPS_PREVENTION_DRY_RUN", "true").lower() == "true"

    alarms = list(run_enabled_modules())
    print(f"Alarmas detectadas: {len(alarms)}")

    for alarm in alarms:
        register_alarm_with_prevention(alarm, prevention_dry_run=prevention_dry_run)


if __name__ == "__main__":
    main()
