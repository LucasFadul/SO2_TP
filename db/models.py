"""Conexion y operaciones basicas sobre PostgreSQL."""

from __future__ import annotations

import os
from typing import List, Mapping, Optional

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


def insert_alarm(alarm: Mapping[str, object]) -> int:
    query = """
        INSERT INTO alarmas (tipo_alarma, ip_origen, modulo, severidad, detalle, resuelta)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
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
            alarm_id = cur.fetchone()[0]
            return int(alarm_id)


RANGE_INTERVALS = {
    "hora": "1 hour",
    "dia": "1 day",
    "semana": "7 days",
    "mes": "30 days",
}


def list_alarms(
    limit: int = 100,
    modulo: Optional[str] = None,
    rango: Optional[str] = None,
) -> List[dict]:
    filters = []
    values: list[object] = []

    if modulo:
        filters.append("a.modulo = %s")
        values.append(modulo)

    if rango in RANGE_INTERVALS:
        filters.append(f"a.timestamp >= now() - interval '{RANGE_INTERVALS[rango]}'")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    query = f"""
        SELECT
            a.id,
            a.timestamp,
            a.tipo_alarma,
            a.ip_origen,
            a.modulo,
            a.severidad,
            a.detalle,
            a.resuelta,
            ap.accion AS accion_tomada,
            ap.resultado AS resultado_prevencion
        FROM alarmas a
        LEFT JOIN LATERAL (
            SELECT accion, resultado
            FROM acciones_prevencion
            WHERE alarma_id = a.id
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
        ) ap ON true
        {where_clause}
        ORDER BY a.timestamp DESC, a.id DESC
        LIMIT %s
    """
    values.append(limit)
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            return list(cur.fetchall())


def insert_prevention_action(
    alarma_id: Optional[int],
    accion: str,
    resultado: str,
    ejecutada_por: str = "sistema",
) -> int:
    query = """
        INSERT INTO acciones_prevencion (alarma_id, accion, resultado, ejecutada_por)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    values = (alarma_id, accion, resultado, ejecutada_por)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            action_id = cur.fetchone()[0]
            return int(action_id)


def get_module_config(modulo: str, parametro: str) -> Optional[str]:
    query = """
        SELECT valor
        FROM configuracion_modulos
        WHERE modulo = %s AND parametro = %s AND activo = true
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (modulo, parametro))
            row = cur.fetchone()
            return str(row[0]) if row else None


def set_module_config(modulo: str, parametro: str, valor: object) -> None:
    query = """
        INSERT INTO configuracion_modulos (modulo, parametro, valor)
        VALUES (%s, %s, %s)
        ON CONFLICT (modulo, parametro)
        DO UPDATE SET valor = EXCLUDED.valor, activo = true, actualizado_en = now()
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (modulo, parametro, str(valor)))
