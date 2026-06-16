#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${HIPS_DB_NAME:-hips}"
APP_USER="${HIPS_DB_USER:-hips_app}"

run_sql() {
  local title="$1"
  local sql="$2"

  printf "\n== %s ==\n" "$title"
  sudo -u postgres psql -d "$DB_NAME" -c "$sql"
}

printf "PostgreSQL hardening audit\n"
printf "Database: %s\n" "$DB_NAME"
printf "Application user: %s\n" "$APP_USER"

run_sql "1. Usuario de aplicacion sin privilegios administrativos" \
  "SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls FROM pg_roles WHERE rolname='${APP_USER}';"

run_sql "2. Password encryption" \
  "SHOW password_encryption;"

run_sql "3. Listen addresses" \
  "SHOW listen_addresses;"

run_sql "4. SSL" \
  "SHOW ssl;"

run_sql "5. Log connections" \
  "SHOW log_connections;"

run_sql "6. Log disconnections" \
  "SHOW log_disconnections;"

run_sql "7. Archivo pg_hba.conf activo" \
  "SHOW hba_file;"

HBA_FILE="$(sudo -u postgres psql -d "$DB_NAME" -Atc "SHOW hba_file;")"

printf "\n== 8. Reglas activas de pg_hba.conf ==\n"
sudo grep -vE '^[[:space:]]*#|^[[:space:]]*$' "$HBA_FILE"

printf "\n== 9. Verificacion de metodo trust ==\n"
if sudo grep -vE '^[[:space:]]*#|^[[:space:]]*$' "$HBA_FILE" | grep -qw trust; then
  printf "NO CUMPLE: se encontro metodo trust en pg_hba.conf\n"
  exit 1
fi

printf "CUMPLE: no se encontro metodo trust en reglas activas\n"
