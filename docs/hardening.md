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

### Auditoria rapida Rocky Linux

Ejecutar en Rocky desde la raiz del proyecto:

```bash
bash scripts/audit_rocky_hardening.sh
```

El script no modifica configuracion. Solo verifica:

- SELinux;
- firewalld;
- reglas activas del firewall;
- configuracion efectiva de SSH;
- privilegios del usuario administrador;
- estado de `auditd`;
- reglas de auditoria para `/etc/passwd` y `/etc/shadow`;
- opciones de montaje de `/tmp`;
- actualizaciones de seguridad disponibles.

### Estado esperado Rocky Linux

| Control | Resultado esperado |
| ----- | ----- |
| SELinux | `Enforcing` |
| firewalld | `active` |
| Puertos permitidos | Solo servicios necesarios: SSH y dashboard durante demo |
| SSH root | `permitrootlogin no` |
| SSH passwords | Ideal `passwordauthentication no`; durante pruebas puede quedar `yes` y documentarse |
| Usuario admin | Usuario personal con sudo; no operar como root directamente |
| auditd | `active` |
| Auditoria archivos criticos | Reglas para `/etc/passwd` y `/etc/shadow` |
| `/tmp` | Ideal `noexec,nosuid,nodev`; si no se aplica, documentar como pendiente/justificado |
| Actualizaciones | Revisadas con `dnf updateinfo list security` |

### Comandos de ajuste Rocky Linux

SELinux enforcing:

```bash
sudo setenforce 1
sudo sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
```

firewalld activo:

```bash
sudo systemctl enable --now firewalld
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

SSH sin login root:

```bash
sudo sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl reload sshd
```

auditd activo:

```bash
sudo dnf install -y audit
sudo systemctl enable --now auditd
```

Reglas auditd para archivos criticos:

```bash
sudo auditctl -w /etc/passwd -p wa -k identity
sudo auditctl -w /etc/shadow -p wa -k identity
```

Actualizaciones de seguridad:

```bash
sudo dnf updateinfo list security
sudo dnf update --security
```

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

### Auditoria rapida PostgreSQL

Ejecutar en Rocky desde la raiz del proyecto:

```bash
bash scripts/audit_postgres_hardening.sh
```

El script no modifica configuracion. Solo verifica:

- privilegios del usuario `hips_app`;
- `password_encryption`;
- `listen_addresses`;
- `ssl`;
- `log_connections`;
- `log_disconnections`;
- ruta activa de `pg_hba.conf`;
- reglas activas de `pg_hba.conf`;
- ausencia del metodo `trust`.

### Estado esperado PostgreSQL

| Control | Resultado esperado |
| ----- | ----- |
| Usuario `hips_app` | `rolsuper=false`, `rolcreaterole=false`, `rolcreatedb=false`, `rolreplication=false`, `rolbypassrls=false` |
| `password_encryption` | `scram-sha-256` |
| `listen_addresses` | `localhost` o una IP interna justificada |
| `ssl` | `on` si hay conexiones remotas; aceptable `off` si solo se usa `localhost` y se documenta |
| `log_connections` | `on` |
| `log_disconnections` | `on` |
| `pg_hba.conf` | sin metodo `trust`; conexiones locales TCP con `scram-sha-256` |

### Comandos de ajuste PostgreSQL

Entrar a PostgreSQL como administrador:

```bash
sudo -u postgres psql
```

Aplicar parametros recomendados:

```sql
ALTER SYSTEM SET password_encryption = 'scram-sha-256';
ALTER SYSTEM SET listen_addresses = 'localhost';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
SELECT pg_reload_conf();
```

Editar `/var/lib/pgsql/data/pg_hba.conf` y usar `scram-sha-256` para conexiones locales TCP:

```text
host    all    all    127.0.0.1/32    scram-sha-256
host    all    all    ::1/128         scram-sha-256
```

Recargar PostgreSQL:

```bash
sudo systemctl reload postgresql
```

## Evidencia recomendada

Guardar capturas o salidas de consola en `docs/evidencias/`:

```bash
mkdir -p docs/evidencias
getenforce | tee docs/evidencias/selinux.txt
systemctl is-active firewalld | tee docs/evidencias/firewalld.txt
bash scripts/audit_postgres_hardening.sh | tee docs/evidencias/postgresql_hardening.txt
bash scripts/audit_rocky_hardening.sh | tee docs/evidencias/rocky_hardening.txt
```
