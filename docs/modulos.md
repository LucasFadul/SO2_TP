# Modulos de deteccion HIPS

Este documento resume los 10 modulos de deteccion implementados en el HIPS,
sus fuentes de datos, condiciones de alarma, accion preventiva asociada y forma
de prueba recomendada.

El flujo general es:

```text
Modulo de deteccion -> alarma -> PostgreSQL -> prevencion -> email -> dashboard
```

Las acciones preventivas pueden ejecutarse en modo seguro con:

```text
HIPS_PREVENTION_DRY_RUN=true
```

En ese modo el HIPS registra la accion que tomaria, pero no bloquea ni elimina
recursos reales del sistema.

## Resumen general

| Modulo | Fuente de datos | Alarma principal | Prevencion |
| --- | --- | --- | --- |
| Integridad de Archivos | Hashes SHA-256 de archivos criticos | `MODIFICACION_ARCHIVO` | `protect_file` |
| Usuarios Conectados | `who`, `/etc/passwd` | `USUARIO_SOSPECHOSO` | `lock_user` |
| Sniffers de Red | `ip link`, `ps aux` | `SNIFFER_DETECTADO` | `kill_process` / `disable_promisc` |
| Analisis de Logs | `/var/log/secure`, logs web/mail, `journalctl` fallback | `FAILED_LOGIN_MULTIPLE`, `SCANNER_HTTP`, `MAIL_ANOMALY` | `block_ip` |
| Cola de Correo | `mailq` | `MAIL_QUEUE_ALTA` | `stop_service` |
| Procesos de Alto Consumo | `ps -eo pid,user,pcpu,pmem,comm` | `PROCESO_ALTO_CONSUMO` | `kill_process` |
| Directorio Temporal | Archivos bajo `/tmp` | `ARCHIVO_TMP_SOSPECHOSO` | `quarantine_file` |
| Deteccion DDoS | Log DNS configurado | `DDOS_DETECTADO` | `block_ip` |
| Tareas Cron | `/etc/crontab`, `/var/spool/cron/root` | `CRON_SOSPECHOSO` | `quarantine_file` |
| Accesos Invalidos | `/var/log/secure` con offset | `ACCESO_INVALIDO_REPETIDO`, `CREDENTIAL_STUFFING` | `block_ip` |

## 1. Integridad de Archivos

Archivo: `detection/file_integrity.py`

Objetivo: detectar cambios no autorizados en archivos criticos del sistema,
por ejemplo `/etc/passwd` y `/etc/shadow`.

Fuente de datos:

- archivos configurados en `file_integrity.paths`;
- hash SHA-256 actual del archivo;
- baseline de hashes esperados.

Condicion de alarma:

- se calcula el hash actual del archivo;
- si existe un hash esperado en la baseline y no coincide, se genera
  `MODIFICACION_ARCHIVO`.

Prevencion:

- `protect_file`: quita permisos de escritura a grupo/otros sobre el archivo
  afectado.

Nota de demo:

- no conviene modificar `/etc/passwd` o `/etc/shadow` en vivo;
- para una prueba segura se debe usar una baseline controlada o un archivo de
  prueba.

## 2. Usuarios Conectados

Archivo: `detection/users_monitor.py`

Objetivo: detectar sesiones sospechosas en el host.

Fuente de datos:

- comando `who`;
- archivo `/etc/passwd` para identificar shells no interactivas;
- parametros configurables: usuarios permitidos, redes permitidas y cantidad
  maxima de sesiones.

Condiciones de alarma:

- usuario conectado que no esta en la lista permitida;
- usuario con shell no interactiva conectado;
- origen fuera de las redes permitidas;
- cantidad de sesiones simultaneas mayor al umbral configurado.

Tipo de alarma:

```text
USUARIO_SOSPECHOSO
```

Prevencion:

- `lock_user`: bloquearia el usuario sospechoso.

Prueba recomendada:

- abrir varias sesiones SSH desde la Mac hacia Rocky;
- ejecutar `who`;
- correr `sudo .venv/bin/python3 main.py`;
- verificar la alarma en el dashboard.

## 3. Sniffers de Red

Archivo: `detection/sniffer_detect.py`

Objetivo: detectar herramientas de captura de paquetes o interfaces en modo
promiscuo.

Fuente de datos:

- `ip link`;
- `ps aux`;
- lista configurable de procesos sniffer: `tcpdump`, `wireshark`, `tshark`,
  `dumpcap`, `ethereal`.

Condiciones de alarma:

- una interfaz aparece con flag `PROMISC`;
- existe un proceso sniffer activo y no esta autorizado.

Tipo de alarma:

```text
SNIFFER_DETECTADO
```

Prevencion:

- `kill_process` si se detecta un proceso sniffer;
- `disable_promisc` si se detecta una interfaz en modo promiscuo.

Prueba recomendada:

- iniciar `tcpdump`;
- correr el HIPS;
- verificar `SNIFFER_DETECTADO`;
- detener `tcpdump` al terminar.

## 4. Analisis de Logs

Archivo: `detection/log_analyzer.py`

Objetivo: analizar logs del sistema para detectar patrones de autenticacion
fallida, scanning HTTP y eventos sospechosos de correo.

Fuente de datos:

- rutas configuradas en `log_analyzer.paths`;
- normalmente `/var/log/secure`, logs de Apache/Nginx y `/var/log/maillog`;
- si no hay archivos legibles, se usa `journalctl -u sshd` como fallback.

Condiciones de alarma:

- mas fallos de login que el limite configurado;
- muchos eventos HTTP sospechosos como `/.env`, `/wp-admin`, `404` o `403`;
- muchos eventos sospechosos de correo como errores SASL o relay denegado.

Tipos de alarma:

```text
FAILED_LOGIN_MULTIPLE
SCANNER_HTTP
MAIL_ANOMALY
```

Prevencion:

- `block_ip`: bloquearia la IP origen.

Prueba recomendada:

- intentar ingresar por SSH con usuario falso o contrasena incorrecta;
- correr el HIPS;
- verificar la alarma en dashboard y en `/var/log/hips/alarmas.log`.

## 5. Cola de Correo

Archivo: `detection/mail_queue.py`

Objetivo: detectar acumulacion anormal de correos en cola.

Fuente de datos:

- comando `mailq`.

Condicion de alarma:

- cantidad de mensajes en cola mayor al parametro `mail_queue.queue_limit`.

Tipo de alarma:

```text
MAIL_QUEUE_ALTA
```

Prevencion:

- `stop_service`: detendria temporalmente el servicio de correo, por defecto
  `postfix`.

Nota de demo:

- requiere que el sistema tenga correo local/Postfix y mensajes en cola;
- si `mailq` no existe o la cola esta vacia, no genera alarma.

## 6. Procesos de Alto Consumo

Archivo: `detection/process_monitor.py`

Objetivo: detectar procesos que consumen CPU o memoria por encima de los
umbrales configurados.

Fuente de datos:

- comando `ps -eo pid,user,pcpu,pmem,comm --sort=-pcpu`.

Condiciones de alarma:

- CPU mayor o igual a `process_monitor.cpu_limit_percent`;
- memoria mayor o igual a `process_monitor.memory_limit_percent`;
- el proceso no esta en la whitelist.

Tipo de alarma:

```text
PROCESO_ALTO_CONSUMO
```

Prevencion:

- `kill_process`: terminaria el proceso detectado.

Prueba recomendada:

```bash
yes > /dev/null &
sudo .venv/bin/python3 main.py
pkill yes
```

## 7. Directorio Temporal

Archivo: `detection/tmp_monitor.py`

Objetivo: detectar scripts o ejecutables sospechosos dentro de `/tmp`.

Fuente de datos:

- recorrido de archivos bajo el directorio configurado en `tmp_monitor.tmp_dir`.

Condiciones de alarma:

- archivo ejecutable;
- archivo con extension de script: `.sh`, `.py`, `.pl`, `.php`.

Tipo de alarma:

```text
ARCHIVO_TMP_SOSPECHOSO
```

Prevencion:

- `quarantine_file`: moveria el archivo sospechoso a cuarentena.

Prueba recomendada:

```bash
echo "curl http://malicious.example" > /tmp/suspicious.sh
sudo .venv/bin/python3 main.py
rm -f /tmp/suspicious.sh
```

## 8. Deteccion DDoS

Archivo: `detection/ddos_detect.py`

Objetivo: detectar muchas solicitudes desde una misma IP en un log DNS.

Fuente de datos:

- archivo configurado en `ddos_detect.log_path`, por defecto `data/dns.log`.

Condicion de alarma:

- una IP aparece mas veces que `ddos_detect.request_limit`.

Tipo de alarma:

```text
DDOS_DETECTADO
```

Prevencion:

- `block_ip`: bloquearia la IP atacante.

Prueba recomendada:

- usar un log DNS de muestra provisto por el profesor;
- o generar un archivo de prueba con muchas lineas desde la misma IP.

## 9. Tareas Cron

Archivo: `detection/cron_monitor.py`

Objetivo: detectar tareas programadas sospechosas.

Fuente de datos:

- rutas configuradas en `cron_monitor.paths`, por defecto `/etc/crontab` y
  `/var/spool/cron/root`.

Condiciones de alarma:

- presencia de tokens sospechosos como `curl`, `wget`, `nc`, `bash -i`,
  `/tmp/`, `python -c` o `base64`.

Tipo de alarma:

```text
CRON_SOSPECHOSO
```

Prevencion:

- `quarantine_file`: moveria el archivo cron sospechoso a cuarentena.

Nota de demo:

- no conviene modificar cron real sin necesidad;
- para demo se puede usar un archivo de prueba y configurar `cron_monitor.paths`
  desde el dashboard.

## 10. Accesos Invalidos

Archivo: `detection/access_monitor.py`

Objetivo: detectar intentos repetidos de acceso invalido y credential stuffing.

Fuente de datos:

- `/var/log/secure`;
- lectura incremental con offset guardado en PostgreSQL para evitar releer todo
  el archivo en cada ejecucion.

Condiciones de alarma:

- mas intentos fallidos desde una misma IP que el umbral configurado;
- multiples usuarios distintos probados desde una misma IP.

Tipos de alarma:

```text
ACCESO_INVALIDO_REPETIDO
CREDENTIAL_STUFFING
```

Prevencion:

- `block_ip`: bloquearia la IP origen.

Prueba recomendada:

- realizar varios intentos SSH fallidos desde la Mac;
- correr el HIPS;
- verificar la alarma en dashboard.

## Configuracion desde dashboard

La pantalla `/config` permite cambiar los parametros operativos de los modulos,
por ejemplo:

- umbrales de CPU/RAM;
- cantidad maxima de sesiones;
- rutas de logs;
- limite de solicitudes DNS;
- whitelist de procesos;
- rutas de cron y `/tmp`.

Los valores se guardan en PostgreSQL, en la tabla `configuracion_modulos`.
El boton `Restaurar` vuelve a cargar los valores originales definidos en
`config/module_settings.py`.

