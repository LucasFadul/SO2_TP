"""Logger central para /var/log/hips."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional


DEFAULT_LOG_DIR = "/var/log/hips"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    return (
        f"{normalized['timestamp']} :: {normalized['tipo_alarma']} :: "
        f"{ip_origen} :: {normalized['modulo']} :: {normalized['severidad']} :: "
        f"{normalized['detalle']}"
    )


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
