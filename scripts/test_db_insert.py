"""Manual check for Python -> PostgreSQL alarm insertion."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from db.models import get_connection, insert_alarm


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    alarm = {
        "tipo_alarma": "TEST_PYTHON",
        "modulo": "manual",
        "severidad": "baja",
        "detalle": "insert desde scripts/test_db_insert.py",
    }
    insert_alarm(alarm)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tipo_alarma, modulo, severidad, detalle
                FROM alarmas
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()

    print("Insercion Python -> PostgreSQL OK")
    print(row)


if __name__ == "__main__":
    main()
