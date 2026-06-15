"""Manual check for Python -> PostgreSQL alarm insertion."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from db.models import get_connection, insert_alarm


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

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
