#!/usr/bin/env bash
set -u

ok() {
  printf "[OK]   %s\n" "$1"
}

warn() {
  printf "[WARN] %s\n" "$1"
}

check_command() {
  local command_name="$1"
  if command -v "$command_name" >/dev/null 2>&1; then
    ok "Comando disponible: $command_name"
  else
    warn "Falta el comando: $command_name"
  fi
}

printf "Preflight de demostracion HIPS\n\n"

if [[ -f main.py && -d detection && -d web ]]; then
  ok "Ejecutado desde la raiz del repositorio"
else
  warn "Ejecutar desde ~/SO2_TP"
fi

if [[ -x .venv/bin/python3 ]]; then
  ok "Entorno virtual disponible"
else
  warn "No existe .venv/bin/python3"
fi

if [[ -f .env ]]; then
  ok "Archivo .env presente"
else
  warn "Falta el archivo .env"
fi

check_command psql
check_command curl
check_command ssh
check_command tcpdump
check_command mailq

if ! command -v systemctl >/dev/null 2>&1; then
  warn "systemctl no esta disponible; ejecutar este preflight dentro de Rocky"
elif systemctl is-active --quiet postgresql; then
  ok "PostgreSQL activo"
else
  warn "PostgreSQL no esta activo"
fi

if ! command -v systemctl >/dev/null 2>&1; then
  warn "No se pudo verificar firewalld fuera de Rocky"
elif systemctl is-active --quiet firewalld; then
  ok "firewalld activo"
else
  warn "firewalld no esta activo"
fi

if curl --silent --fail http://127.0.0.1:8000/health >/dev/null 2>&1; then
  ok "Dashboard responde en el puerto 8000"
else
  warn "Dashboard no responde; iniciar Uvicorn antes de la demo"
fi

if [[ -d /var/log/hips ]]; then
  ok "Directorio /var/log/hips disponible"
else
  warn "Todavia no existe /var/log/hips"
fi

if grep -q '^HIPS_PREVENTION_DRY_RUN=true$' .env 2>/dev/null; then
  ok "Prevencion configurada en dry-run"
else
  warn "Revisar HIPS_PREVENTION_DRY_RUN; para la demo se recomienda true"
fi

if grep -q '^HIPS_EMAIL_DRY_RUN=false$' .env 2>/dev/null; then
  ok "Envio real de email habilitado"
else
  warn "Email en dry-run o sin configurar"
fi

printf "\nEl preflight solo verifica; no modifica el sistema.\n"
