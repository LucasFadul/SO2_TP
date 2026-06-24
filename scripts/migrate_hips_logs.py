#!/usr/bin/env python3
"""Migra los logs historicos del HIPS sin eliminar registros."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def formatted_date(value: str) -> str:
    value = value.strip()
    try:
        parsed = datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
        except ValueError:
            return value
    return parsed.strftime("%d/%m/%Y")


def migrate_alarm_line(line: str) -> str:
    parts = [part.strip() for part in line.split("::")]
    if len(parts) < 3:
        return line.rstrip("\n")
    return f"{formatted_date(parts[0])} :: {parts[1]} :: {parts[2] or 'N/A'}"


def migrate_prevention_line(line: str) -> str:
    parts = [part.strip() for part in line.split("::")]
    if len(parts) < 2:
        return line.rstrip("\n")
    parts[0] = formatted_date(parts[0])
    return " :: ".join(parts)


def migrate_file(path: Path, line_migrator) -> int:
    if not path.exists():
        return 0

    backup_path = path.with_name(f"{path.name}.bak")
    if not backup_path.exists():
        shutil.copy2(path, backup_path)

    original_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    migrated_lines = [line_migrator(line) for line in original_lines if line.strip()]
    content = "\n".join(migrated_lines)
    path.write_text(f"{content}\n" if content else "", encoding="utf-8")
    return len(migrated_lines)


def normalize_prevention_filename(log_dir: Path) -> None:
    accented_path = log_dir / "prevención.log"
    regular_path = log_dir / "prevencion.log"
    if not accented_path.exists():
        return

    if regular_path.exists():
        with regular_path.open("a", encoding="utf-8") as destination:
            content = accented_path.read_text(encoding="utf-8", errors="replace")
            if content:
                destination.write(content if content.endswith("\n") else f"{content}\n")
        accented_path.rename(accented_path.with_name("prevención.log.bak"))
    else:
        accented_path.rename(regular_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Actualiza los logs historicos del HIPS conservando respaldos."
    )
    parser.add_argument(
        "--log-dir",
        default="/var/log/hips",
        help="Directorio de logs (default: /var/log/hips)",
    )
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    normalize_prevention_filename(log_dir)
    alarm_count = migrate_file(log_dir / "alarmas.log", migrate_alarm_line)
    prevention_count = migrate_file(
        log_dir / "prevencion.log",
        migrate_prevention_line,
    )

    print(f"alarmas.log: {alarm_count} registros conservados")
    print(f"prevencion.log: {prevention_count} registros conservados")
    print("Respaldos: alarmas.log.bak y prevencion.log.bak")
    print("Los archivos .jsonl no fueron modificados.")


if __name__ == "__main__":
    main()
