# Sistemas Operativos - HIPS

## Taller de Kickoff de Desarrollo

Duracion: 2 horas  
Grupo: 2 alumnos  
Proyecto: `sentinel_hips`

## 1. Stack Tecnologico y Hardening

### 1.1 Decisiones del stack

| Componente | Eleccion | Justificacion |
| ----- | ----- | ----- |
| Lenguaje principal | Python 3.x | Permite desarrollar modulos de monitoreo del sistema, parsing de logs, conexion con PostgreSQL, envio de emails y pruebas automatizadas con `pytest`. Ademas, mantiene el codigo portable y facil de dividir por modulos. |
| Scripts auxiliares | Bash | Se usara solo para instalacion, verificacion de hardening y tareas operativas del sistema donde Bash es mas directo que Python. |
| Web framework | FastAPI | Es liviano, rapido y separa bien API, dashboard y autenticacion. Facilita documentacion automatica, validacion de datos y futuras integraciones con pruebas automatizadas. |
| Base de datos | PostgreSQL | Es robusta, auditable y adecuada para registrar alarmas, usuarios, acciones de prevencion y configuracion. Tiene controles CIS claros y verificables. |
| Sistema operativo | Rocky Linux 10.2 estable | Rocky Linux es compatible con el ecosistema Enterprise Linux y adecuado para servidores. A la fecha del taller, la pagina oficial informa Rocky Linux 10.2 como version disponible. |
| Pruebas | pytest + scripts Bash de verificacion | Permite probar logica de deteccion con fixtures y validar controles de SO/BD con comandos automatizables. |

### 1.2 Hardening del Sistema Operativo - Rocky Linux

| # | Area / Control | Descripcion de lo que se configura | Comando de verificacion o implementacion |
| ----- | ----- | ----- | ----- |
| 1 | SELinux enforcing | Mantener SELinux activo en modo enforcing para limitar acciones de procesos comprometidos. | `getenforce` debe devolver `Enforcing`; implementar con `setenforce 1` y `SELINUX=enforcing` en `/etc/selinux/config`. |
| 2 | firewalld activo | Permitir solo servicios necesarios: SSH, HTTPS/API y PostgreSQL solo si corresponde en red interna. | `systemctl is-active firewalld`; `firewall-cmd --list-all`. |
| 3 | SSH sin root | Deshabilitar login directo como root por SSH. | `sshd -T | grep permitrootlogin` debe mostrar `permitrootlogin no`. |
| 4 | SSH con claves | Restringir acceso SSH a autenticacion por clave, evitando contrasenas remotas. | `sshd -T | grep passwordauthentication` debe mostrar `passwordauthentication no`. |
| 5 | Usuarios con privilegio minimo | Crear usuario operativo sin root y permitir sudo solo a administradores autorizados. | `getent group wheel`; `sudo -l -U hips_admin`. |
| 6 | auditd activo | Registrar eventos relevantes de seguridad y cambios en archivos criticos. | `systemctl is-active auditd`; `auditctl -s`. |
| 7 | Auditoria de `/etc/passwd` y `/etc/shadow` | Monitorear escritura/cambios sobre archivos de identidad del sistema. | `auditctl -l | grep -E '/etc/(passwd|shadow)'`. |
| 8 | `/tmp` con restricciones | Montar `/tmp` con `noexec,nosuid,nodev` para reducir ejecucion de malware temporal. | `findmnt -no OPTIONS /tmp` debe incluir `noexec`, `nosuid`, `nodev`. |
| 9 | Banner legal | Configurar banner de acceso para advertir uso autorizado y auditoria. | `cat /etc/issue`; `sshd -T | grep banner`. |
| 10 | Actualizaciones de seguridad | Mantener paquetes actualizados y aplicar parches de seguridad. | `dnf updateinfo list security`; implementar con `dnf update --security`. |
| 11 | Servicios innecesarios deshabilitados | Reducir superficie de ataque apagando servicios no usados. | `systemctl list-unit-files --state=enabled`; deshabilitar con `systemctl disable --now servicio`. |
| 12 | Permisos de logs HIPS | Proteger `/var/log/hips/` contra escritura no autorizada. | `stat -c '%U %G %a' /var/log/hips`; recomendado `root hips 750`. |

### 1.3 Hardening de la Base de Datos - PostgreSQL CIS

| # | Control CIS / Area | Descripcion de lo que se configura | Verificacion |
| :---: | ----- | ----- | ----- |
| 1 | Usuario de aplicacion sin superusuario | La app usara `hips_app` sin permisos de superusuario, creacion de roles ni creacion de BD. | `SELECT rolname, rolsuper, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname='hips_app';` |
| 2 | `password_encryption` fuerte | Usar `scram-sha-256` para hashes de password. | `SHOW password_encryption;` debe devolver `scram-sha-256`. |
| 3 | `listen_addresses` restringido | PostgreSQL escuchara solo en `localhost` o IP interna necesaria. | `SHOW listen_addresses;`. |
| 4 | SSL activo | Activar cifrado para conexiones si hay acceso remoto o red interna. | `SHOW ssl;` debe devolver `on`. |
| 5 | Log de conexiones | Registrar inicio de conexiones para auditoria. | `SHOW log_connections;` debe devolver `on`. |
| 6 | Log de desconexiones | Registrar cierre de sesiones y duracion. | `SHOW log_disconnections;` debe devolver `on`. |
| 7 | Acceso por `pg_hba.conf` limitado | Permitir solo usuarios, bases e IPs necesarias; evitar `trust`. | `grep -vE '^#|^$' $PGDATA/pg_hba.conf`; verificar que no exista metodo `trust`. |
| 8 | Permisos de archivos de datos | El directorio de datos debe pertenecer a `postgres` y no ser accesible por otros. | `stat -c '%U %G %a' $PGDATA`; recomendado permisos restrictivos. |
| 9 | No guardar credenciales en codigo | Variables sensibles en `.env` o secret store, nunca en repositorio. | `rg -n "password|HIPS_DB_PASSWORD|postgres://" .` y revisar que no haya secretos reales. |

### 1.4 Esquema inicial de base de datos

| Tabla | Columnas minimas | Proposito |
| ----- | ----- | ----- |
| `alarmas` | `id`, `timestamp`, `tipo_alarma`, `ip_origen`, `modulo`, `severidad`, `detalle`, `resuelta` | Registro central de todas las alarmas detectadas. |
| `acciones_prevencion` | `id`, `alarma_id`, `accion`, `timestamp`, `resultado`, `ejecutada_por` | Log de acciones automaticas o manuales tomadas por prevencion. |
| `usuarios_web` | `id`, `username`, `password_hash`, `rol`, `activo`, `ultimo_login` | Acceso autenticado a dashboard y configuracion. |
| `configuracion_modulos` | `id`, `modulo`, `parametro`, `valor`, `activo`, `actualizado_en` | Umbrales y parametros ajustables de cada modulo. |
| `eventos_sistema` | `id`, `timestamp`, `modulo`, `fuente`, `evento_raw`, `procesado` | Registro normalizado de eventos antes de convertirse o no en alarma. |
| `hosts_bloqueados` | `id`, `ip`, `motivo`, `bloqueado_en`, `expira_en`, `activo` | Control de IPs bloqueadas por prevencion. |

## 2. Mapa de Trabajo

### 2.1 Modulos del sistema

| # | Modulo / Componente | Responsable | Complejidad | Dependencias | Semana |
| :---: | ----- | ----- | ----- | ----- | ----- |
| i | Integridad de archivos | Alumno A | A | baseline hashes, logger, BD | 2 |
| ii | Usuarios conectados | Alumno B | M | comandos `who`, `last`, logger | 2 |
| iii | Sniffers y modo promiscuo | Alumno A | M | `ip`, `ss`, lista de procesos | 1 |
| iv | Analisis de logs | Alumno B | A | parser logs, reglas, BD | 1-2 |
| v | Cola de correo | Alumno A | M | `mailq`, configuracion MTA | 3 |
| vi | Procesos con alto consumo | Alumno B | M | `ps`, umbrales config | 3 |
| vii | Directorio `/tmp` | Alumno A | M | permisos, procesos, hash | 3 |
| viii | Ataques DDoS | Alumno B | A | log DNS del profesor, parser | 4 |
| ix | Cron sospechoso | Alumno A | M | `/etc/crontab`, `/var/spool/cron` | 4 |
| x | Intentos de acceso invalidos | Alumno B | A | logs SSH/web, reglas umbral | 1 |
| - | Modulo de Prevencion | Ambos | A | todos los detectores | 4-5 |
| - | Interfaz web + dashboard | Alumno A | A | FastAPI, PostgreSQL | 3-5 |
| - | Alertas por email + dashboard | Alumno B | M | logger, alarmas, SMTP | 4 |
| - | Logger central `/var/log/hips/` | Alumno A | M | todos | 1 |
| - | PostgreSQL + 7 CIS controls | Alumno B | M | instalacion BD | 1 |
| - | Carpeta encriptada de configuracion | Alumno A | M | `gpg` o `openssl`, permisos | 2 |
| - | Rocky Linux + 10 hardening controls | Ambos | A | VM Rocky Linux | 1 |
| - | Suite de pruebas automatizadas | Ambos | A | modulos implementados | 2-5 |
| - | Manual de uso + instalacion | Ambos | M | proyecto completo | 5 |

## 3. Protocolo de Nomenclatura

### 3.1 Nombre del proyecto

| Item | Decision del grupo |
| ----- | ----- |
| Nombre del proyecto | `sentinel_hips` |
| Prefijo del sistema | `HIPS_` para variables de entorno y `hips.` para logs/configuracion |

### 3.2 Archivos y carpetas

| Item | Convencion elegida | Ejemplo |
| ----- | ----- | ----- |
| Modulos Python | `snake_case` | `sniffer_detect.py` |
| Carpetas | `snake_case` | `detection/`, `prevention/` |
| Archivos de config | `snake_case` con extension clara | `settings.env`, `hips.conf` |
| Templates HTML | `kebab-case` | `dashboard-alerts.html` |
| Tests | `test_*.py` | `test_log_analyzer.py` |
| Documentacion | `snake_case` | `manual_instalacion.md` |

### 3.3 Codigo Python

| Item | Convencion elegida | Ejemplo |
| ----- | ----- | ----- |
| Funciones | `snake_case` | `detect_sniffer()` |
| Clases | `PascalCase` | `SnifferDetector` |
| Constantes | `UPPER_SNAKE` | `MAX_FAILED_ATTEMPTS = 5` |
| Variables de entorno | `UPPER_SNAKE` con prefijo | `HIPS_DB_PASSWORD` |
| Parametros de modulo | `lower_snake_case` con nombre del modulo | `sniffer_check_interval = 60` |

### 3.4 Base de datos

| Item | Convencion elegida | Ejemplo |
| ----- | ----- | ----- |
| Tablas | `snake_case` plural | `alarmas`, `acciones_prevencion` |
| Columnas | `snake_case` | `ip_origen`, `tipo_alarma` |
| Indices | `idx_tabla_columna` | `idx_alarmas_timestamp` |
| Claves foraneas | `fk_tabla_ref` | `fk_acciones_alarma` |
| Usuario de aplicacion | nombre restrictivo | `hips_app` sin superusuario |

### 3.5 GIT

| Item | Convencion elegida |
| ----- | ----- |
| Rama principal | `main` |
| Ramas de modulos | `feat/modulo-nombre`, ejemplo `feat/sniffer-detection` |
| Ramas de fix | `fix/descripcion`, ejemplo `fix/log-format` |
| Formato de commit | `tipo(modulo): descripcion`, ejemplo `feat(sniffer): detectar modo promiscuo` |
| Tipos de commit | `feat`, `fix`, `docs`, `test`, `refactor`, `chore` |
| Frecuencia minima | Al terminar cada funcion o al final de cada sesion |

### 3.6 Tipos de alarma

| Modulo | Tipo de alarma | Ejemplo en log |
| ----- | ----- | ----- |
| i | `MODIFICACION_ARCHIVO` | `29/05/2026 :: MODIFICACION_ARCHIVO :: N/A` |
| ii | `USUARIO_SOSPECHOSO` | `29/05/2026 :: USUARIO_SOSPECHOSO :: 192.168.1.10` |
| iii | `SNIFFER_DETECTADO` | `29/05/2026 :: SNIFFER_DETECTADO :: N/A` |
| iv | `FAILED_LOGIN_MULTIPLE`, `SCANNER_HTTP` | `29/05/2026 :: FAILED_LOGIN_MULTIPLE :: 10.0.0.25` |
| v | `MAIL_QUEUE_ALTA` | `29/05/2026 :: MAIL_QUEUE_ALTA :: N/A` |
| vi | `PROCESO_ALTO_CONSUMO` | `29/05/2026 :: PROCESO_ALTO_CONSUMO :: N/A` |
| vii | `ARCHIVO_TMP_SOSPECHOSO` | `29/05/2026 :: ARCHIVO_TMP_SOSPECHOSO :: N/A` |
| viii | `DDOS_DETECTADO` | `29/05/2026 :: DDOS_DETECTADO :: 203.0.113.5` |
| ix | `CRON_SOSPECHOSO` | `29/05/2026 :: CRON_SOSPECHOSO :: N/A` |
| x | `ACCESO_INVALIDO_REPETIDO`, `CREDENTIAL_STUFFING` | `29/05/2026 :: ACCESO_INVALIDO_REPETIDO :: 10.0.0.8` |

## 4. Analisis de Requerimientos

### Modulo iii - Sniffers y modo promiscuo

| Campo | Completar |
| ----- | ----- |
| Nombre del modulo | Modulo iii: `sniffer_detect` |
| Objetivo concreto | Detectar interfaces en modo promiscuo y procesos asociados a captura de trafico no autorizada. |
| Fuentes de datos | `ip link`, `/sys/class/net/*/flags`, `ps aux`, `ss -lntup`, lista de procesos permitidos. |
| Condicion de alarma | Se dispara si una interfaz no autorizada esta en modo promiscuo o si aparece un proceso como `tcpdump`, `wireshark`, `tshark`, `dumpcap` o `ethereal` fuera de ventana autorizada. |
| Comportamiento NORMAL | Captura autorizada por administrador durante diagnostico, registrada en configuracion como excepcion temporal. |
| Comportamiento ANOMALO | Interfaz promiscuous activa sin autorizacion o proceso de sniffing ejecutado por usuario no permitido. |
| Parametros configurables | Lista de interfaces permitidas, procesos permitidos, usuarios autorizados, duracion maxima de excepcion. |
| Logica de deteccion | 1. Leer interfaces y flags. 2. Buscar procesos de sniffing. 3. Comparar contra excepciones. 4. Generar alarma si no hay autorizacion. |
| Accion de prevencion | Matar proceso no autorizado y registrar accion; opcionalmente bajar interfaz si el riesgo es alto. |
| Tipo de alarma en log | `SNIFFER_DETECTADO` |
| Contenido del email | Asunto: `[HIPS ALERTA] Sniffer detectado`. Cuerpo: interfaz/proceso, usuario, PID, timestamp y accion tomada. |
| Visibilidad en dashboard | `timestamp`, `tipo`, `ip_origen`, `modulo`, `accion_tomada`, `pid`, `usuario`. |
| Casos borde / excepciones | Herramientas de monitoreo legitimas, practicas de laboratorio, procesos con nombre similar. |
| Test automatizable | Mockear salida de `ip link` con flag `PROMISC` y salida de `ps` con `tcpdump`; verificar alarma y accion esperada. |

### Modulo iv - Analisis de logs

| Campo | Completar |
| ----- | ----- |
| Nombre del modulo | Modulo iv: `log_analyzer` |
| Objetivo concreto | Detectar patrones sospechosos en logs del sistema y servicios, como fuerza bruta, scanners HTTP o errores repetitivos. |
| Fuentes de datos | `/var/log/secure`, `/var/log/messages`, `/var/log/httpd/access_log`, `/var/log/httpd/error_log`, `journalctl`. |
| Condicion de alarma | Mas de 5 fallos SSH desde la misma IP en 10 minutos; mas de 30 requests HTTP 404/403 desde la misma IP en 5 minutos; patrones de scanner como `/wp-admin`, `.env`, `/phpmyadmin`. |
| Comportamiento NORMAL | Errores aislados de usuarios legitimos, monitoreo interno o pruebas autorizadas desde IP permitida. |
| Comportamiento ANOMALO | Repeticion de fallos, muchas rutas inexistentes, user agents sospechosos o intentos sobre endpoints sensibles. |
| Parametros configurables | Ventana temporal, cantidad maxima de fallos, lista blanca de IPs, patrones HTTP sospechosos. |
| Logica de deteccion | 1. Leer incrementalmente logs nuevos. 2. Parsear timestamp, IP, servicio y resultado. 3. Agrupar por IP y ventana. 4. Comparar contra umbrales. 5. Crear alarma. |
| Accion de prevencion | Bloquear IP temporalmente con firewalld y registrar en `hosts_bloqueados`. |
| Tipo de alarma en log | `FAILED_LOGIN_MULTIPLE` o `SCANNER_HTTP` |
| Contenido del email | Asunto: `[HIPS ALERTA] Patron sospechoso en logs`. Cuerpo: IP, regla activada, cantidad de eventos, ventana temporal y accion aplicada. |
| Visibilidad en dashboard | `timestamp`, `tipo`, `ip_origen`, `modulo`, `accion_tomada`, `cantidad_eventos`. |
| Casos borde / excepciones | NAT con muchos usuarios, pentest autorizado, crawler legitimo, rotacion de logs. |
| Test automatizable | Usar archivos de log de prueba con eventos sinteticos; ejecutar parser y verificar que solo dispara al superar umbral. |

### Modulo x - Intentos de acceso invalidos

| Campo | Completar |
| ----- | ----- |
| Nombre del modulo | Modulo x: `access_monitor` |
| Objetivo concreto | Detectar fuerza bruta y credential stuffing contra SSH o login web. |
| Fuentes de datos | `/var/log/secure`, tabla de intentos web, logs de FastAPI, eventos de autenticacion. |
| Condicion de alarma | Mas de 5 intentos fallidos desde una IP en 10 minutos, o intentos contra mas de 5 usuarios distintos desde la misma IP en 10 minutos. |
| Comportamiento NORMAL | Usuario que olvida su contrasena una o dos veces, error de teclado o prueba interna autorizada. |
| Comportamiento ANOMALO | Muchas credenciales fallidas, muchos usuarios probados, intentos distribuidos o repetidos en poco tiempo. |
| Parametros configurables | Maximo de intentos, ventana temporal, duracion del bloqueo, lista blanca, cantidad maxima de usernames distintos. |
| Logica de deteccion | 1. Recibir evento fallido. 2. Agrupar por IP y ventana. 3. Contar intentos y usuarios distintos. 4. Si supera umbral, generar alarma. 5. Solicitar accion preventiva. |
| Accion de prevencion | Bloquear IP por tiempo definido, marcar cuenta para revision si hay ataques a un usuario especifico. |
| Tipo de alarma en log | `ACCESO_INVALIDO_REPETIDO` o `CREDENTIAL_STUFFING` |
| Contenido del email | Asunto: `[HIPS ALERTA] Intentos de acceso invalidos`. Cuerpo: IP, usuarios afectados, cantidad de intentos, ventana, bloqueo aplicado. |
| Visibilidad en dashboard | `timestamp`, `tipo`, `ip_origen`, `modulo`, `accion_tomada`, `usuarios_afectados`. |
| Casos borde / excepciones | Usuarios detras de la misma IP publica, laboratorios, sistemas automatizados mal configurados. |
| Test automatizable | Insertar eventos de login fallido simulados y verificar que no alarme con 5 o menos, pero si con 6 en la ventana. |

## Estructura de carpetas propuesta

```text
sentinel_hips/
  detection/
    file_integrity.py
    users_monitor.py
    sniffer_detect.py
    log_analyzer.py
    mail_queue.py
    process_monitor.py
    tmp_monitor.py
    ddos_detect.py
    cron_monitor.py
    access_monitor.py
  prevention/
    firewall.py
    user_actions.py
    process_kill.py
    service_mgmt.py
  alerts/
    logger.py
    mailer.py
  web/
    app.py
    auth.py
    templates/
    static/
  db/
    models.py
    migrations/
  config/
    baseline_hashes.enc
  tests/
    test_sniffer_detect.py
    test_log_analyzer.py
    test_access_monitor.py
  docs/
    manual_usuario.md
    manual_instalacion.md
  .env.example
  requirements.txt
  README.md
```

## Entregables finales

| Entregable | Estado |
| ----- | ----- |
| Stack + controles de hardening identificados | Completo |
| Mapa de trabajo | Completo |
| Protocolo de nomenclatura | Completo |
| Analisis de 3 modulos | Completo |
| Git repo creado y compartido | Pendiente: crear remoto y compartir URL con el profesor |
