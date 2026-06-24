"""General HIPS runner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Mapping

from dotenv import load_dotenv

from alerts.logger import write_alarm, write_prevention
from alerts.mailer import send_alert
from config.module_settings import SETTINGS_BY_KEY
from db.models import (
    get_module_config,
    insert_alarm,
    insert_prevention_action,
    set_module_config,
)
from detection.access_monitor import analyze_access_lines
from detection.cron_monitor import run_check as run_cron_check
from detection.ddos_detect import run_check as run_ddos_check
from detection.file_integrity import run_check as run_file_integrity_check
from detection.log_analyzer import analyze_lines
from detection.mail_queue import run_check as run_mail_queue_check
from detection.process_monitor import run_check as run_process_check
from detection.sniffer_detect import run_check as run_sniffer_check
from detection.tmp_monitor import run_check as run_tmp_check
from detection.users_monitor import run_check as run_users_check
from prevention.file_actions import protect_file, quarantine_file
from prevention.firewall import block_ip
from prevention.network import disable_promiscuous_mode
from prevention.process_kill import kill_process
from prevention.service_mgmt import stop_service
from prevention.user_actions import lock_user


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SECURE_LOG_PATH = Path("/var/log/secure")


def read_sshd_journal(since: str) -> List[str]:
    command = ["journalctl", "-u", "sshd", "--since", since, "--no-pager"]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo leer journalctl")
    return result.stdout.splitlines()


def offset_param(path: Path) -> str:
    return f"log_offset:{path}"


def read_new_log_lines(path: Path, modulo: str) -> List[str]:
    offset_value = get_module_config(modulo, offset_param(path))
    offset = int(offset_value) if offset_value else 0
    size = path.stat().st_size
    if offset > size:
        offset = 0

    with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
        file_obj.seek(offset)
        data = file_obj.read()
        new_offset = file_obj.tell()

    set_module_config(modulo, offset_param(path), new_offset)
    return data.splitlines()


def configured_log_paths() -> List[Path]:
    return [Path(path) for path in config_csv("log_analyzer", "paths")]


def read_configured_logs() -> tuple[List[str], List[str]]:
    lines: List[str] = []
    sources: List[str] = []

    for path in configured_log_paths():
        if not path.exists():
            continue
        try:
            new_lines = read_new_log_lines(path, "log_analyzer")
        except OSError:
            continue
        if new_lines:
            lines.extend(new_lines)
        sources.append(str(path))

    return lines, sources


def read_journal_fallback() -> tuple[List[str], str]:
    since = config_value("log_analyzer", "ssh_journal_since")
    return read_sshd_journal(since), f"journalctl -u sshd --since '{since}'"


def register_alarm_with_prevention(
    alarm: Mapping[str, object],
    prevention_dry_run: bool,
) -> None:
    alarm_id = insert_alarm(alarm)
    log_alarm(alarm)

    result = run_prevention(alarm, dry_run=prevention_dry_run)
    if result:
        insert_prevention_action(
            alarma_id=alarm_id,
            accion=result["accion"],
            resultado=str(result),
        )
        log_prevention(alarm, result)

    notify_admin(alarm, result)


def log_alarm(alarm: Mapping[str, object]) -> None:
    try:
        write_alarm(alarm)
    except Exception as exc:
        print(f"Advertencia: no se pudo escribir alarmas.log: {exc}")


def log_prevention(
    alarm: Mapping[str, object],
    prevention_result: Mapping[str, object],
) -> None:
    try:
        write_prevention(alarm, prevention_result)
    except Exception as exc:
        print(f"Advertencia: no se pudo escribir prevencion.log: {exc}")


def notify_admin(
    alarm: Mapping[str, object],
    prevention_result: Mapping[str, object] | None,
) -> None:
    email_dry_run = os.getenv("HIPS_EMAIL_DRY_RUN", "true").lower() == "true"
    try:
        send_alert(
            alarm,
            prevention_result=prevention_result,
            dry_run=email_dry_run,
        )
    except Exception as exc:
        print(f"Advertencia: no se pudo enviar email: {exc}")


def run_prevention(alarm: Mapping[str, object], dry_run: bool) -> dict | None:
    modulo = alarm.get("modulo")

    if modulo == "file_integrity" and alarm.get("archivo"):
        return protect_file(str(alarm["archivo"]), dry_run=dry_run)

    if modulo in {"log_analyzer", "ddos_detect", "access_monitor"} and alarm.get("ip_origen"):
        return block_ip(str(alarm["ip_origen"]), dry_run=dry_run)

    if modulo == "sniffer_detect" and alarm.get("pid"):
        return kill_process(int(alarm["pid"]), dry_run=dry_run)

    if modulo == "sniffer_detect" and alarm.get("interfaz"):
        return disable_promiscuous_mode(str(alarm["interfaz"]), dry_run=dry_run)

    if modulo == "mail_queue":
        service = str(alarm.get("service") or "postfix")
        return stop_service(service, dry_run=dry_run)

    if modulo == "process_monitor" and alarm.get("pid"):
        return kill_process(int(alarm["pid"]), dry_run=dry_run)

    if modulo in {"tmp_monitor", "cron_monitor"} and alarm.get("archivo"):
        return quarantine_file(str(alarm["archivo"]), dry_run=dry_run)

    if modulo == "users_monitor" and alarm.get("usuario"):
        return lock_user(str(alarm["usuario"]), dry_run=dry_run)

    return None


def config_value(modulo: str, parametro: str) -> str:
    setting = SETTINGS_BY_KEY[(modulo, parametro)]
    try:
        db_value = get_module_config(modulo, parametro)
    except Exception:
        db_value = None
    return db_value or os.getenv(setting.env_name, setting.default)


def config_bool(modulo: str, parametro: str) -> bool:
    return config_value(modulo, parametro).lower() in {"1", "true", "yes", "on"}


def config_csv(modulo: str, parametro: str) -> list[str]:
    raw_value = config_value(modulo, parametro)
    return [value.strip() for value in raw_value.split(",") if value.strip()]


def run_file_integrity() -> List[dict]:
    files = config_csv("file_integrity", "paths")
    return run_file_integrity_check(files=files)


def run_log_analyzer() -> List[dict]:
    failed_limit = int(config_value("log_analyzer", "failed_login_limit"))
    http_limit = int(config_value("log_analyzer", "http_404_limit"))
    mail_limit = int(config_value("log_analyzer", "mail_anomaly_limit"))

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

    return alarms


def run_sniffer_detect() -> List[dict]:
    authorized = config_bool("sniffer_detect", "authorized")
    process_names = config_csv("sniffer_detect", "process_names")
    return run_sniffer_check(authorized=authorized, process_names=process_names)


def run_mail_queue() -> List[dict]:
    limit = int(config_value("mail_queue", "queue_limit"))
    return run_mail_queue_check(limit=limit)


def run_tmp_monitor() -> List[dict]:
    tmp_dir = config_value("tmp_monitor", "tmp_dir")
    return run_tmp_check(tmp_dir=tmp_dir)


def run_ddos_detect() -> List[dict]:
    log_path = config_value("ddos_detect", "log_path")
    request_limit = int(config_value("ddos_detect", "request_limit"))
    return run_ddos_check(log_path=log_path, request_limit=request_limit)


def run_cron_monitor() -> List[dict]:
    paths = config_csv("cron_monitor", "paths")
    return run_cron_check(paths=paths)


def run_access_monitor() -> List[dict]:
    failed_limit = int(config_value("access_monitor", "failed_limit"))
    distinct_user_limit = int(config_value("access_monitor", "distinct_user_limit"))
    access_log_path = Path(config_value("access_monitor", "log_path"))
    if not access_log_path.exists():
        return []
    try:
        lines = read_new_log_lines(access_log_path, "access_monitor")
    except OSError:
        return []
    return analyze_access_lines(
        lines,
        failed_limit=failed_limit,
        distinct_user_limit=distinct_user_limit,
    )


def allowed_users_from_env() -> set[str]:
    raw_users = config_value("users_monitor", "allowed_users")
    if raw_users:
        return {user.strip() for user in raw_users.split(",") if user.strip()}

    default_user = os.getenv("SUDO_USER") or os.getenv("USER")
    return {default_user} if default_user else set()


def run_users_monitor() -> List[dict]:
    allowed_users = allowed_users_from_env()
    allowed_networks = config_csv("users_monitor", "allowed_networks")
    max_sessions = int(config_value("users_monitor", "max_sessions"))
    alarms = run_users_check(
        allowed_users=allowed_users,
        allowed_networks=allowed_networks,
        max_sessions=max_sessions,
        validate_sessions=True,
    )
    return alarms


def run_process_monitor() -> List[dict]:
    cpu_limit = float(config_value("process_monitor", "cpu_limit_percent"))
    memory_limit = float(config_value("process_monitor", "memory_limit_percent"))
    process_whitelist = config_csv("process_monitor", "process_whitelist")
    alarms = run_process_check(
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
        process_whitelist=process_whitelist,
    )
    return alarms


def alarm_word(count: int) -> str:
    return "alarma" if count == 1 else "alarmas"


def print_summary(module_alarms: Mapping[str, List[dict]]) -> None:
    registered_alarms = [
        alarm for alarms in module_alarms.values() for alarm in alarms
    ]

    print("HIPS iniciado")
    for module_name, alarms in module_alarms.items():
        print(f"{module_name}: {len(alarms)} {alarm_word(len(alarms))}")

    print()
    print(f"Alarmas registradas: {len(registered_alarms)}")
    for alarm in registered_alarms:
        print(f"- {alarm['tipo_alarma']} | {alarm['modulo']}")

    print()
    print("Ver dashboard para detalles.")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    prevention_dry_run = os.getenv("HIPS_PREVENTION_DRY_RUN", "true").lower() == "true"

    module_alarms = {
        "file_integrity": run_file_integrity(),
        "users_monitor": run_users_monitor(),
        "sniffer_detect": run_sniffer_detect(),
        "log_analyzer": run_log_analyzer(),
        "mail_queue": run_mail_queue(),
        "process_monitor": run_process_monitor(),
        "tmp_monitor": run_tmp_monitor(),
        "ddos_detect": run_ddos_detect(),
        "cron_monitor": run_cron_monitor(),
        "access_monitor": run_access_monitor(),
    }

    for alarms in module_alarms.values():
        for alarm in alarms:
            register_alarm_with_prevention(alarm, prevention_dry_run=prevention_dry_run)

    print_summary(module_alarms)


if __name__ == "__main__":
    main()
