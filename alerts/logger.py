"""Logger central para /var/log/hips."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional


DEFAULT_LOG_DIR = "/var/log/hips"
PREVENTION_LOG_NAME = "prevención.log"
LEGACY_PREVENTION_LOG_NAME = "prevencion.log"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_log_date(timestamp: object = None) -> str:
    if isinstance(timestamp, datetime):
        value = timestamp
    elif timestamp:
        try:
            value = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        except ValueError:
            value = datetime.now().astimezone()
    else:
        value = datetime.now().astimezone()
    return value.astimezone().strftime("%d/%m/%Y")


def normalize_alarm(alarm: Mapping[str, object]) -> dict:
    return {
        "timestamp": alarm.get("timestamp") or utc_now_iso(),
        "tipo_alarma": alarm.get("tipo_alarma", "ALARMA_DESCONOCIDA"),
        "ip_origen": alarm.get("ip_origen"),
        "modulo": alarm.get("modulo", "unknown"),
        "severidad": alarm.get("severidad", "media"),
        "detalle": alarm.get("detalle", ""),
        "resuelta": alarm.get("resuelta", False),
    }


def format_alarm_line(alarm: Mapping[str, object]) -> str:
    normalized = normalize_alarm(alarm)
    ip_origen = normalized["ip_origen"] or "N/A"
    date = format_log_date(normalized["timestamp"])
    return f"{date} :: {normalized['tipo_alarma']} :: {ip_origen}"


def write_alarm(alarm: Mapping[str, object], log_dir: Optional[str] = None) -> Path:
    target_dir = Path(log_dir or os.getenv("HIPS_LOG_DIR", DEFAULT_LOG_DIR))
    target_dir.mkdir(parents=True, exist_ok=True)

    log_path = target_dir / "alarmas.log"
    with log_path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(format_alarm_line(alarm) + "\n")

    json_path = target_dir / "alarmas.jsonl"
    with json_path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(normalize_alarm(alarm), ensure_ascii=True) + "\n")

    return log_path


def format_prevention_line(
    alarm: Mapping[str, object],
    prevention_result: Mapping[str, object],
) -> str:
    alarm_type = alarm.get("tipo_alarma", "ALARMA_DESCONOCIDA")
    module = alarm.get("modulo", "unknown")
    action = prevention_result.get("accion", "accion_desconocida")
    dry_run = prevention_result.get("dry_run")
    ok = prevention_result.get("ok")
    return (
        f"{utc_now_iso()} :: {alarm_type} :: {module} :: "
        f"{action} :: dry_run={dry_run} :: ok={ok} :: {prevention_result}"
    )


def write_prevention(
    alarm: Mapping[str, object],
    prevention_result: Mapping[str, object],
    log_dir: Optional[str] = None,
) -> Path:
    target_dir = Path(log_dir or os.getenv("HIPS_LOG_DIR", DEFAULT_LOG_DIR))
    target_dir.mkdir(parents=True, exist_ok=True)

    log_path = target_dir / PREVENTION_LOG_NAME
    legacy_log_path = target_dir / LEGACY_PREVENTION_LOG_NAME
    if legacy_log_path.exists() and not log_path.exists():
        legacy_log_path.rename(log_path)

    with log_path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(format_prevention_line(alarm, prevention_result) + "\n")

    json_path = target_dir / "prevencion.jsonl"
    with json_path.open("a", encoding="utf-8") as file_obj:
        payload = {
            "timestamp": utc_now_iso(),
            "alarma": normalize_alarm(alarm),
            "prevencion": dict(prevention_result),
        }
        file_obj.write(json.dumps(payload, ensure_ascii=True) + "\n")

    return log_path
