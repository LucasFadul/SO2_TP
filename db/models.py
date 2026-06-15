"""Conexion y operaciones basicas sobre PostgreSQL."""

from __future__ import annotations

import os
from typing import List, Mapping

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    host = os.getenv("HIPS_DB_HOST", "localhost")
    port = os.getenv("HIPS_DB_PORT", "5432")
    name = os.getenv("HIPS_DB_NAME", "hips")
    user = os.getenv("HIPS_DB_USER", "hips_app")
    password = os.getenv("HIPS_DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def get_connection():
    return psycopg.connect(database_url())


def insert_alarm(alarm: Mapping[str, object]) -> None:
    query = """
        INSERT INTO alarmas (tipo_alarma, ip_origen, modulo, severidad, detalle, resuelta)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (
        alarm.get("tipo_alarma"),
        alarm.get("ip_origen"),
        alarm.get("modulo"),
        alarm.get("severidad", "media"),
        alarm.get("detalle", ""),
        alarm.get("resuelta", False),
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)


def list_alarms(limit: int = 100) -> List[dict]:
    query = """
        SELECT id, timestamp, tipo_alarma, ip_origen, modulo, severidad, detalle, resuelta
        FROM alarmas
        ORDER BY timestamp DESC, id DESC
        LIMIT %s
    """
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            return list(cur.fetchall())
