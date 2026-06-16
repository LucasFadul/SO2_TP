#!/usr/bin/env bash
set -euo pipefail

HIPS_ADMIN_USER="${HIPS_ADMIN_USER:-$USER}"

print_section() {
  printf "\n== %s ==\n" "$1"
}

run_or_warn() {
  local command_text="$1"
  bash -lc "$command_text" || true
}

printf "Rocky Linux hardening audit\n"
printf "Admin user: %s\n" "$HIPS_ADMIN_USER"

print_section "1. SELinux en modo enforcing"
run_or_warn "getenforce"

print_section "2. firewalld activo"
run_or_warn "systemctl is-active firewalld"

print_section "3. Puertos y servicios permitidos en firewalld"
run_or_warn "sudo firewall-cmd --list-all"

print_section "4. SSH sin login root"
run_or_warn "sshd -T | grep '^permitrootlogin'"

print_section "5. SSH PasswordAuthentication"
run_or_warn "sshd -T | grep '^passwordauthentication'"

print_section "6. Usuario con privilegios sudo controlados"
run_or_warn "id '$HIPS_ADMIN_USER'"
run_or_warn "sudo -l -U '$HIPS_ADMIN_USER'"

print_section "7. auditd activo"
run_or_warn "systemctl is-active auditd"

print_section "8. Reglas auditd para archivos criticos"
run_or_warn "sudo auditctl -l | grep -E '/etc/(passwd|shadow)' || true"

print_section "9. Opciones de montaje de /tmp"
run_or_warn "findmnt -no OPTIONS /tmp || true"

print_section "10. Actualizaciones de seguridad disponibles"
run_or_warn "sudo dnf updateinfo list security || true"
