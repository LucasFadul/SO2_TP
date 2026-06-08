# Hardening HIPS

Checklist para Rocky Linux y PostgreSQL.

## Rocky Linux - 10 controles

| # | Control | Verificacion |
| ----- | ----- | ----- |
| 1 | SELinux en modo enforcing | `getenforce` |
| 2 | firewalld activo | `systemctl is-active firewalld` |
| 3 | Puertos permitidos minimos | `firewall-cmd --list-all` |
| 4 | SSH sin login root | `sshd -T | grep permitrootlogin` |
| 5 | SSH sin passwords remotas | `sshd -T | grep passwordauthentication` |
| 6 | Usuarios con privilegio minimo | `sudo -l -U <usuario>` |
| 7 | auditd activo | `systemctl is-active auditd` |
| 8 | Auditoria de archivos criticos | `auditctl -l | grep -E '/etc/(passwd|shadow)'` |
| 9 | `/tmp` con `noexec,nosuid,nodev` | `findmnt -no OPTIONS /tmp` |
| 10 | Actualizaciones de seguridad revisadas | `dnf updateinfo list security` |

## PostgreSQL - 7 controles CIS

| # | Control | Verificacion |
| ----- | ----- | ----- |
| 1 | Usuario `hips_app` sin superusuario | `SELECT rolname, rolsuper, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname='hips_app';` |
| 2 | Password encryption `scram-sha-256` | `SHOW password_encryption;` |
| 3 | `listen_addresses` restringido | `SHOW listen_addresses;` |
| 4 | SSL activo si hay conexiones remotas | `SHOW ssl;` |
| 5 | Log de conexiones activo | `SHOW log_connections;` |
| 6 | Log de desconexiones activo | `SHOW log_disconnections;` |
| 7 | `pg_hba.conf` sin metodo `trust` | `grep -vE '^#|^$' $PGDATA/pg_hba.conf` |

## Evidencia recomendada

Guardar capturas o salidas de consola en `docs/evidencias/`:

```bash
mkdir -p docs/evidencias
getenforce | tee docs/evidencias/selinux.txt
systemctl is-active firewalld | tee docs/evidencias/firewalld.txt
```

