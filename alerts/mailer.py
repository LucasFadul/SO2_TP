"""Envio de alertas por email usando smtplib."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Mapping, Optional


def build_alert_message(
    alarm: Mapping[str, object],
    prevention_result: Optional[Mapping[str, object]] = None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = os.getenv("HIPS_ALERT_FROM", "hips@localhost")
    message["To"] = os.getenv("HIPS_ALERT_TO", "admin@localhost")
    message["Subject"] = f"[HIPS ALERTA] {alarm.get('tipo_alarma', 'Alarma')}"
    prevention_lines = []
    if prevention_result:
        prevention_lines = [
            "",
            "Accion preventiva:",
            f"Accion: {prevention_result.get('accion')}",
            f"Dry run: {prevention_result.get('dry_run')}",
            f"Resultado: {prevention_result}",
        ]

    message.set_content(
        "\n".join(
            [
                "Se detecto una alarma HIPS.",
                f"Modulo: {alarm.get('modulo')}",
                f"Tipo: {alarm.get('tipo_alarma')}",
                f"IP origen: {alarm.get('ip_origen') or 'N/A'}",
                f"Severidad: {alarm.get('severidad')}",
                f"Detalle: {alarm.get('detalle')}",
            ]
            + prevention_lines
        )
    )
    return message


def send_alert(
    alarm: Mapping[str, object],
    prevention_result: Optional[Mapping[str, object]] = None,
    dry_run: bool = True,
) -> dict:
    message = build_alert_message(alarm, prevention_result=prevention_result)
    if dry_run:
        return {
            "accion": "send_email",
            "dry_run": True,
            "ok": True,
            "to": message["To"],
            "subject": message["Subject"],
        }

    host = os.getenv("HIPS_SMTP_HOST", "localhost")
    port = int(os.getenv("HIPS_SMTP_PORT", "25"))
    timeout = float(os.getenv("HIPS_SMTP_TIMEOUT", "10"))
    username = os.getenv("HIPS_SMTP_USER", "")
    password = os.getenv("HIPS_SMTP_PASSWORD", "")

    with smtplib.SMTP(host, port, timeout=timeout) as smtp:
        if os.getenv("HIPS_SMTP_STARTTLS", "false").lower() in {"1", "true", "yes", "on"}:
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(message)
    return {
        "accion": "send_email",
        "dry_run": False,
        "ok": True,
        "to": message["To"],
        "subject": message["Subject"],
    }
