#!/usr/bin/env python3
"""Crea o actualiza un usuario del dashboard sin exponer su contraseña."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.models import upsert_web_user
from web.auth import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear usuario del dashboard HIPS")
    parser.add_argument("username", help="Nombre del usuario")
    parser.add_argument(
        "--role",
        default="administrador",
        help="Rol del usuario (default: administrador)",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    username = args.username.strip()
    if not username:
        raise SystemExit("El nombre de usuario no puede estar vacío.")

    password = getpass.getpass("Contraseña: ")
    confirmation = getpass.getpass("Confirmar contraseña: ")
    if password != confirmation:
        raise SystemExit("Las contraseñas no coinciden.")
    if len(password) < 10:
        raise SystemExit("La contraseña debe tener al menos 10 caracteres.")

    user_id = upsert_web_user(
        username=username,
        password_hash=hash_password(password),
        rol=args.role,
    )
    print(f"Usuario web listo: id={user_id} username={username} rol={args.role}")


if __name__ == "__main__":
    main()
