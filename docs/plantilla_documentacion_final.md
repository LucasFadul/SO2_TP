# Documentacion Final - HIPS Rocky

> Plantilla base para completar con texto propio, capturas y evidencias.
> Recomendacion: copiar esta estructura a Google Docs y reemplazar cada
> bloque `[Completar]` y `[CAPTURA]`.

## Portada

**Proyecto:** HIPS Rocky  
**Materia:** Sistemas Operativos 2  
**Alumno:** Lucas Fadul  
**Profesor:** [Completar]  
**Fecha:** [Completar]  

**Descripcion breve:**  
[Completar: explicar en 3 o 4 lineas que el proyecto es un HIPS sobre Rocky
Linux que detecta comportamientos sospechosos, registra alarmas, ejecuta
acciones preventivas, envia emails y muestra un dashboard.]

## Indice

1. Introduccion
2. Objetivo del proyecto
3. Arquitectura general
4. Entorno utilizado
5. Instalacion y preparacion
6. Base de datos PostgreSQL
7. Modulos de deteccion
8. Dashboard web
9. Configuracion desde la interfaz
10. Modulo de prevencion
11. Alertas por email
12. Logs formales del HIPS
13. Hardening de Rocky Linux
14. Hardening de PostgreSQL
15. Pruebas realizadas
16. Problemas encontrados y soluciones
17. Limitaciones y mejoras futuras
18. Conclusion

## 1. Introduccion

[Completar: explicar que es un HIPS. Por ejemplo: un Host-based Intrusion
Prevention System es un sistema que corre dentro de un host y analiza eventos
locales para detectar posibles intrusiones.]

[Completar: explicar por que se eligio Rocky Linux y que el sistema fue probado
dentro de una maquina virtual.]

## 2. Objetivo del Proyecto

El objetivo del proyecto es desarrollar un HIPS capaz de:

- monitorear eventos del sistema operativo;
- detectar comportamientos anormales;
- registrar alarmas en PostgreSQL;
- registrar acciones preventivas;
- generar logs formales en `/var/log/hips/`;
- enviar alertas por email;
- mostrar las alarmas en un dashboard web;
- permitir la configuracion de parametros desde la interfaz.

## 3. Arquitectura General

Flujo general:

```text
Rocky Linux
  -> main.py
  -> Modulos de deteccion
  -> PostgreSQL
  -> Modulo de prevencion
  -> /var/log/hips/
  -> Email
  -> Dashboard FastAPI
```

Explicacion:

[Completar: explicar que `main.py` ejecuta los modulos. Si un modulo detecta
algo sospechoso, se registra una alarma en PostgreSQL. Luego se registra la
accion preventiva, se escribe en `/var/log/hips/`, se envia un email y el
dashboard permite visualizar el resultado.]

[CAPTURA: estructura general del repositorio o diagrama hecho a mano.]

## 4. Entorno Utilizado

| Componente | Valor |
| --- | --- |
| Sistema operativo | Rocky Linux 10 |
| Maquina virtual | [Completar: UTM / otra] |
| Lenguaje | Python 3 |
| Framework web | FastAPI |
| Base de datos | PostgreSQL |
| Tests | pytest |
| Equipo host | macOS |

[CAPTURA: Rocky Linux funcionando.]

Comandos de verificacion:

```bash
python3 --version
psql --version
git --version
```

[CAPTURA: salida de versiones.]

## 5. Instalacion y Preparacion

### 5.1 Paquetes del sistema

```bash
sudo dnf update -y
sudo dnf install -y git python3 python3-pip postgresql-server postgresql-contrib
```

Explicacion:

[Completar: explicar que `dnf` instala paquetes en Rocky Linux. Se instalaron
Git para clonar el repositorio, Python para ejecutar el HIPS y PostgreSQL para
guardar datos.]

### 5.2 Clonado del repositorio

```bash
git clone https://github.com/LucasFadul/SO2_TP.git
cd SO2_TP
```

[CAPTURA: repositorio clonado en Rocky.]

### 5.3 Entorno virtual Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Explicacion:

[Completar: explicar que `.venv` aisla las dependencias del proyecto para no
mezclarlas con paquetes globales del sistema.]

### 5.4 Archivo `.env`

```bash
cp .env.example .env
nano .env
```

Explicacion:

[Completar: explicar que `.env` contiene configuracion local, como datos de
base de datos, SMTP y modo dry-run. No se sube al repositorio.]

[CAPTURA: `.env` sin mostrar contrasenas reales.]

## 6. Base de Datos PostgreSQL

### 6.1 Inicializacion

```bash
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

### 6.2 Creacion de base y usuario

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE hips;
CREATE USER hips_app WITH PASSWORD '********';
GRANT ALL PRIVILEGES ON DATABASE hips TO hips_app;
\q
```

### 6.3 Creacion de tablas

```bash
sudo -u postgres psql -d hips < db/schema.sql
```

### 6.4 Tablas creadas

```bash
sudo -u postgres psql -d hips -c "\dt"
```

[CAPTURA: lista de tablas.]

Tablas principales:

| Tabla | Funcion |
| --- | --- |
| `alarmas` | Guarda alarmas detectadas |
| `acciones_prevencion` | Guarda acciones preventivas |
| `configuracion_modulos` | Guarda parametros configurables |
| `hosts_bloqueados` | Registra hosts bloqueados |
| `eventos_sistema` | Registra eventos del sistema |
| `usuarios_web` | Usuarios del dashboard |

[Completar: explicar por que se usa PostgreSQL como almacenamiento central.]

## 7. Modulos de Deteccion

El HIPS implementa 10 modulos de deteccion. Cada modulo analiza una fuente de
datos distinta y genera una alarma si detecta una condicion sospechosa.

### 7.1 Integridad de Archivos

**Archivo:** `detection/file_integrity.py`  
**Alarma:** `MODIFICACION_ARCHIVO`  
**Prevencion:** `protect_file`

**Que detecta:**  
[Completar: cambios en archivos criticos comparando hashes.]

**Fuente de datos:**  
[Completar: archivos como `/etc/passwd` y `/etc/shadow`.]

**Condicion de alarma:**  
[Completar: hash actual distinto al hash baseline.]

**Prueba / evidencia:**  
[CAPTURA: si se prueba con archivo controlado, mostrar alarma.]

### 7.2 Usuarios Conectados

**Archivo:** `detection/users_monitor.py`  
**Alarma:** `USUARIO_SOSPECHOSO`  
**Prevencion:** `lock_user`

**Que detecta:**  
[Completar: usuarios inesperados, origenes no permitidos o demasiadas sesiones.]

**Fuente de datos:**  
`who` y `/etc/passwd`.

**Prueba:**

```bash
who
sudo .venv/bin/python3 main.py
```

[CAPTURA: `who`, salida de `main.py` y dashboard.]

### 7.3 Sniffers de Red

**Archivo:** `detection/sniffer_detect.py`  
**Alarma:** `SNIFFER_DETECTADO`  
**Prevencion:** `kill_process` / `disable_promisc`

**Que detecta:**  
[Completar: tcpdump, wireshark, tshark o interfaz en modo promiscuo.]

**Prueba:**

```bash
sudo tcpdump -i enp0s1 > /dev/null &
sudo .venv/bin/python3 main.py
ps aux | grep tcpdump
```

[CAPTURA: alarma en dashboard.]

### 7.4 Analisis de Logs

**Archivo:** `detection/log_analyzer.py`  
**Alarmas:** `FAILED_LOGIN_MULTIPLE`, `SCANNER_HTTP`, `MAIL_ANOMALY`  
**Prevencion:** `block_ip`

**Que detecta:**  
[Completar: fallos SSH, eventos HTTP sospechosos y anomalias de correo.]

**Fuente de datos:**  
`/var/log/secure`, logs web, `/var/log/maillog` y fallback con `journalctl`.

**Prueba:**

```bash
ssh usuario_falso@<IP_ROCKY>
sudo .venv/bin/python3 main.py
```

[CAPTURA: intentos fallidos y alarma en dashboard.]

### 7.5 Cola de Correo

**Archivo:** `detection/mail_queue.py`  
**Alarma:** `MAIL_QUEUE_ALTA`  
**Prevencion:** `stop_service`

**Que detecta:**  
[Completar: cola de correo mayor al limite configurado.]

**Fuente de datos:**  
`mailq`.

**Prueba / evidencia:**  
[Completar: explicar si se preparo o si queda como caso dependiente de tener
servicio de correo local.]

### 7.6 Procesos de Alto Consumo

**Archivo:** `detection/process_monitor.py`  
**Alarma:** `PROCESO_ALTO_CONSUMO`  
**Prevencion:** `kill_process`

**Que detecta:**  
[Completar: procesos con CPU o RAM por encima del umbral y fuera de whitelist.]

**Prueba:**

```bash
yes > /dev/null &
sudo .venv/bin/python3 main.py
pkill yes
```

[CAPTURA: salida de terminal y dashboard.]

### 7.7 Directorio Temporal

**Archivo:** `detection/tmp_monitor.py`  
**Alarma:** `ARCHIVO_TMP_SOSPECHOSO`  
**Prevencion:** `quarantine_file`

**Que detecta:**  
[Completar: scripts o ejecutables sospechosos en `/tmp`.]

**Prueba:**

```bash
echo "curl http://malicious.example" > /tmp/suspicious.sh
sudo .venv/bin/python3 main.py
rm -f /tmp/suspicious.sh
```

[CAPTURA: archivo creado y alarma.]

### 7.8 Deteccion DDoS

**Archivo:** `detection/ddos_detect.py`  
**Alarma:** `DDOS_DETECTADO`  
**Prevencion:** `block_ip`

**Que detecta:**  
[Completar: muchas solicitudes desde una misma IP en un log DNS.]

**Fuente de datos:**  
`data/dns.log` o log provisto por el profesor.

**Prueba / evidencia:**  
[Completar con log de prueba o muestra DNS.]

### 7.9 Tareas Cron

**Archivo:** `detection/cron_monitor.py`  
**Alarma:** `CRON_SOSPECHOSO`  
**Prevencion:** `quarantine_file`

**Que detecta:**  
[Completar: tareas cron con comandos sospechosos como curl, wget, nc, bash -i,
base64 o rutas en `/tmp`.]

**Prueba / evidencia:**  
[Completar con archivo cron de prueba o captura de configuracion.]

### 7.10 Accesos Invalidos

**Archivo:** `detection/access_monitor.py`  
**Alarmas:** `ACCESO_INVALIDO_REPETIDO`, `CREDENTIAL_STUFFING`  
**Prevencion:** `block_ip`

**Que detecta:**  
[Completar: intentos repetidos desde una IP o multiples usuarios probados desde
una misma IP.]

**Fuente de datos:**  
`/var/log/secure`.

[CAPTURA: alarma en dashboard.]

## 8. Dashboard Web

El dashboard esta hecho con FastAPI y permite visualizar las alarmas almacenadas
en PostgreSQL.

Comando para levantarlo:

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

URL:

```text
http://<IP_ROCKY>:8000
```

El dashboard muestra:

- ID;
- timestamp;
- tipo de alarma;
- IP origen;
- modulo;
- severidad;
- detalle;
- accion tomada;
- estado resuelta.

[CAPTURA: dashboard con alarmas.]

## 9. Configuracion Desde la Interfaz

La pantalla `/config` permite modificar parametros de los modulos.

Ejemplos:

- limite de CPU;
- limite de RAM;
- sesiones maximas;
- rutas de logs;
- whitelist de procesos;
- limite de solicitudes DNS.

Estos valores se guardan en la tabla `configuracion_modulos`.

[CAPTURA: pantalla `/config`.]

[CAPTURA: boton `Restaurar`.]

## 10. Modulo de Prevencion

Las acciones preventivas se registran cuando una alarma es detectada.

| Accion | Descripcion |
| --- | --- |
| `block_ip` | Bloquearia una IP con firewall |
| `lock_user` | Bloquearia una cuenta de usuario |
| `kill_process` | Terminaria un proceso |
| `quarantine_file` | Moveria un archivo a cuarentena |
| `stop_service` | Detendria un servicio |
| `protect_file` | Ajustaria permisos de un archivo |

Durante la demo se usa:

```env
HIPS_PREVENTION_DRY_RUN=true
```

Esto permite demostrar la decision sin dañar la VM.

[CAPTURA: tabla `acciones_prevencion`.]

## 11. Alertas por Email

El sistema envia un correo al administrador cuando se registra una alarma y una
accion preventiva.

Configuracion en `.env`:

```env
HIPS_EMAIL_DRY_RUN=false
HIPS_SMTP_HOST=smtp.gmail.com
HIPS_SMTP_PORT=587
HIPS_SMTP_STARTTLS=true
HIPS_SMTP_USER=********
HIPS_SMTP_PASSWORD=********
HIPS_ALERT_TO=********
```

No se deben mostrar contrasenas reales en capturas.

[CAPTURA: email recibido.]

## 12. Logs Formales del HIPS

El TP pide logs formales en:

```text
/var/log/hips/
```

Archivos:

```text
/var/log/hips/alarmas.log
/var/log/hips/prevencion.log
```

Comandos:

```bash
sudo ls -l /var/log/hips
sudo tail -n 5 /var/log/hips/alarmas.log
sudo tail -n 5 /var/log/hips/prevencion.log
```

[CAPTURA: logs formales.]

## 13. Hardening de Rocky Linux

El TP solicita al menos 10 controles de hardening.

Controles verificados:

| # | Control | Evidencia |
| --- | --- | --- |
| 1 | SELinux enforcing | `getenforce` |
| 2 | firewalld activo | `systemctl is-active firewalld` |
| 3 | Puertos permitidos | `firewall-cmd --list-all` |
| 4 | SSH sin root login | `sshd -T | grep permitrootlogin` |
| 5 | Configuracion SSH revisada | `sshd -T` |
| 6 | Usuario sudo controlado | `sudo -l -U lucasfadul` |
| 7 | auditd activo | `systemctl is-active auditd` |
| 8 | Auditoria de archivos criticos | `auditctl -l` |
| 9 | Actualizaciones de seguridad revisadas | `dnf updateinfo list security` |
| 10 | Servicios/puertos justificados | salida de firewalld |

Script de auditoria:

```bash
bash scripts/audit_rocky_hardening.sh
```

[CAPTURA: salida del script.]

## 14. Hardening de PostgreSQL

Controles principales:

| # | Control | Evidencia |
| --- | --- | --- |
| 1 | Usuario `hips_app` sin superusuario | consulta a `pg_roles` |
| 2 | Password encryption | `SHOW password_encryption;` |
| 3 | Listen addresses restringido | `SHOW listen_addresses;` |
| 4 | SSL revisado | `SHOW ssl;` |
| 5 | Log connections activo | `SHOW log_connections;` |
| 6 | Log disconnections activo | `SHOW log_disconnections;` |
| 7 | `pg_hba.conf` sin trust | revision de reglas |

Script de auditoria:

```bash
bash scripts/audit_postgres_hardening.sh
```

[CAPTURA: salida del script.]

## 15. Pruebas Realizadas

### 15.1 Pruebas automaticas

```bash
python3 -m pytest -q
```

[CAPTURA: tests pasando.]

### 15.2 Pruebas manuales

| Prueba | Comando / accion | Resultado |
| --- | --- | --- |
| SSH fallido | `ssh usuario_falso@<IP_ROCKY>` | `FAILED_LOGIN_MULTIPLE` |
| Sesiones simultaneas | varias sesiones SSH | `USUARIO_SOSPECHOSO` |
| Sniffer | `tcpdump` | `SNIFFER_DETECTADO` |
| CPU alta | `yes > /dev/null &` | `PROCESO_ALTO_CONSUMO` |
| Script en `/tmp` | crear `/tmp/suspicious.sh` | `ARCHIVO_TMP_SOSPECHOSO` |

[CAPTURA: cada prueba o una captura general del dashboard con todas.]

## 16. Problemas Encontrados y Soluciones

| Problema | Causa | Solucion |
| --- | --- | --- |
| `python3 command not found` | Python no instalado | `sudo dnf install -y python3 python3-pip` |
| Error de permisos en PostgreSQL | usuario Linux distinto al rol DB | usar `sudo -u postgres` y crear `hips_app` |
| Error `ident authentication failed` | `pg_hba.conf` no aceptaba password | cambiar a `scram-sha-256` y recargar PostgreSQL |
| No se podia leer `/var/log/secure` | permisos root | ejecutar `sudo .venv/bin/python3 main.py` |
| Dashboard no accesible desde Mac | puerto/firewall/host | usar `--host 0.0.0.0` y abrir puerto 8000 |
| `tcpdump` quedo corriendo | proceso en segundo plano | matar proceso con `sudo kill <PID>` |
| `.venv` no funcionaba con sudo python global | sudo usa otro Python | ejecutar `sudo .venv/bin/python3 main.py` |

[Completar: agregar otros problemas reales que quieras incluir.]

## 17. Limitaciones y Mejoras Futuras

Limitaciones:

- algunas acciones se dejaron en `dry_run` para evitar romper la VM durante la
  demo;
- algunos modulos requieren datos preparados, como cola de correo o log DNS;
- el dashboard visualiza alarmas, pero la deteccion se ejecuta con `main.py`;
- las credenciales reales no se documentan ni se suben al repositorio.

Mejoras futuras:

- ejecutar el HIPS como servicio `systemd`;
- agregar autenticacion real al dashboard;
- agregar loop permanente;
- agregar graficos en dashboard;
- mejorar baseline cifrada para integridad de archivos;
- agregar mas pruebas automatizadas.

## 18. Conclusion

[Completar: resumir que se logro implementar un HIPS funcional sobre Rocky
Linux, con modulos de deteccion, prevencion, PostgreSQL, dashboard, logs,
emails y hardening.]

[Completar: mencionar que el proyecto permitio practicar Linux, logs,
PostgreSQL, hardening, FastAPI, Python y seguridad defensiva.]

## Anexo A - Comandos Utiles

Ver IP de Rocky:

```bash
ip a
```

Ejecutar HIPS:

```bash
sudo .venv/bin/python3 main.py
```

Levantar dashboard:

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Ver tablas:

```bash
sudo -u postgres psql -d hips -c "\dt"
```

Ver ultimas alarmas:

```bash
sudo -u postgres psql -d hips -c "SELECT id, tipo_alarma, modulo, severidad, detalle FROM alarmas ORDER BY id DESC LIMIT 10;"
```

Ver logs:

```bash
sudo tail -n 5 /var/log/hips/alarmas.log
sudo tail -n 5 /var/log/hips/prevencion.log
```

Ejecutar tests:

```bash
python3 -m pytest -q
```

