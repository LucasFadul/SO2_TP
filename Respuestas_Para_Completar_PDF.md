# Respuestas para completar el PDF - Taller HIPS

Proyecto sugerido: `sentinel_hips`  
Integrantes: Alumno A / Alumno B  
Sistema operativo: Rocky Linux, ultima version estable disponible al momento de instalar la VM.

## Bloque 1 - Stack + Hardening

### 1.1 Decisiones del stack

| Componente | Eleccion + justificacion |
| ----- | ----- |
| Lenguaje principal | Python 3.x. Se elige porque permite crear modulos de deteccion independientes, leer comandos del sistema, parsear logs, conectarse a PostgreSQL, enviar alertas por email y automatizar pruebas con `pytest`. Es adecuado para un HIPS modular y mantenible. |
| Web framework | FastAPI. Se elige porque es liviano, rapido y facilita crear una API para dashboard, autenticacion y configuracion de modulos. Tambien genera documentacion automatica y valida datos de entrada, lo que ayuda a reducir errores. |

### 1.2 Hardening del sistema operativo - Rocky Linux

| # | Area / Control | Descripcion | Comando de verificacion o implementacion |
| ----- | ----- | ----- | ----- |
| 1 | SELinux enforcing | Mantener SELinux en modo enforcing para limitar acciones de procesos comprometidos. | `getenforce`; debe devolver `Enforcing`. |
| 2 | Firewall activo | Activar `firewalld` y permitir solo puertos necesarios: SSH administrado, HTTP/HTTPS del dashboard y servicios internos. | `systemctl is-active firewalld`; `firewall-cmd --list-all`. |
| 3 | SSH sin login root | Evitar acceso remoto directo como root. | `sshd -T | grep permitrootlogin`; debe mostrar `permitrootlogin no`. |
| 4 | SSH con claves | Deshabilitar passwords remotas y usar claves publicas. | `sshd -T | grep passwordauthentication`; debe mostrar `passwordauthentication no`. |
| 5 | Privilegios minimos | Crear usuarios operativos sin permisos root y usar `sudo` solo para administradores autorizados. | `getent group wheel`; `sudo -l -U hips_admin`. |
| 6 | Auditd activo | Registrar eventos de seguridad y cambios importantes del sistema. | `systemctl is-active auditd`; `auditctl -s`. |
| 7 | Auditoria de archivos criticos | Auditar cambios en `/etc/passwd`, `/etc/shadow` y archivos sensibles. | `auditctl -l | grep -E '/etc/(passwd|shadow)'`. |
| 8 | `/tmp` restringido | Montar `/tmp` con `noexec,nosuid,nodev` para reducir ejecucion de malware temporal. | `findmnt -no OPTIONS /tmp`; debe incluir `noexec,nosuid,nodev`. |
| 9 | Banner de acceso | Mostrar advertencia legal antes del login. | `cat /etc/issue`; `sshd -T | grep banner`. |
| 10 | Actualizaciones de seguridad | Aplicar parches de seguridad del sistema. | `dnf updateinfo list security`; implementar con `dnf update --security`. |

### 1.3 Hardening PostgreSQL - 7 controles CIS

| # | Control | Descripcion | Verificacion |
| ----- | ----- | ----- | ----- |
| 1 | Usuario de aplicacion sin superusuario | La app usa `hips_app` sin permisos de superusuario, creacion de roles ni creacion de bases. | `SELECT rolname, rolsuper, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname='hips_app';` |
| 2 | Password encryption fuerte | Usar `scram-sha-256` para proteger hashes de contrasenas. | `SHOW password_encryption;` |
| 3 | `listen_addresses` restringido | PostgreSQL escucha solo en `localhost` o red interna necesaria. | `SHOW listen_addresses;` |
| 4 | SSL activo | Cifrar conexiones cuando haya acceso remoto o red interna. | `SHOW ssl;` |
| 5 | Log de conexiones | Registrar inicios de sesion para auditoria. | `SHOW log_connections;` |
| 6 | Log de desconexiones | Registrar cierres de sesion y duracion. | `SHOW log_disconnections;` |
| 7 | `pg_hba.conf` restrictivo | Permitir solo usuarios, bases e IPs necesarias. Evitar metodo `trust`. | `grep -vE '^#|^$' $PGDATA/pg_hba.conf`. |

### 1.4 Esquema inicial de base de datos

| Tabla | Columnas | Proposito |
| ----- | ----- | ----- |
| `alarmas` | `id`, `timestamp`, `tipo_alarma`, `ip_origen`, `modulo`, `severidad`, `detalle`, `resuelta` | Registro de alarmas detectadas por los modulos. |
| `acciones_prevencion` | `id`, `alarma_id`, `accion`, `timestamp`, `resultado`, `ejecutada_por` | Historial de respuestas automaticas o manuales. |
| `usuarios_web` | `id`, `username`, `password_hash`, `rol`, `activo`, `ultimo_login` | Usuarios autorizados para ingresar al dashboard. |
| `configuracion_modulos` | `id`, `modulo`, `parametro`, `valor`, `activo` | Umbrales y opciones configurables desde la interfaz web. |
| `eventos_sistema` | `id`, `timestamp`, `modulo`, `fuente`, `evento_raw`, `procesado` | Eventos leidos antes de convertirse en alarma. |
| `hosts_bloqueados` | `id`, `ip`, `motivo`, `bloqueado_en`, `expira_en`, `activo` | IPs bloqueadas por el modulo de prevencion. |

## Bloque 2 - Mapa de trabajo

| # | Modulo / Componente | Responsable | Complejidad | Dependencias | Semana |
| ----- | ----- | ----- | ----- | ----- | ----- |
| i | Integridad de archivos | Alumno A | A | hashes base, logger, BD | 2 |
| ii | Usuarios conectados | Alumno B | M | `who`, `last`, logger | 2 |
| iii | Sniffers y modo promiscuo | Alumno A | M | `ip`, `ps`, reglas | 1 |
| iv | Analisis de logs | Alumno B | A | logs, parser, BD | 1-2 |
| v | Cola de correo | Alumno A | M | `mailq`, MTA | 3 |
| vi | Procesos alto consumo | Alumno B | M | `ps`, umbrales | 3 |
| vii | Directorio `/tmp` | Alumno A | M | permisos, procesos | 3 |
| viii | Ataques DDoS | Alumno B | A | log DNS profesor | 4 |
| ix | Cron sospechoso | Alumno A | M | `/etc/crontab`, cron spool | 4 |
| x | Accesos invalidos | Alumno B | A | logs SSH/web | 1 |
| - | Modulo de prevencion | Ambos | A | todos | 4-5 |
| - | Interfaz web + dashboard | Alumno A | A | PostgreSQL | 3-5 |
| - | Alertas email + dashboard | Alumno B | M | alarmas, SMTP | 4 |
| - | Logger central `/var/log/hips/` | Alumno A | M | todos | 1 |
| - | PostgreSQL + CIS | Alumno B | M | BD | 1 |
| - | Configuracion encriptada | Alumno A | M | permisos, GPG/OpenSSL | 2 |
| - | Rocky Linux hardening | Ambos | A | VM | 1 |
| - | Pruebas automatizadas | Ambos | A | modulos | 2-5 |
| - | Manuales | Ambos | M | proyecto completo | 5 |

## Bloque 3 - Protocolo de nomenclatura

| Item | Decision |
| ----- | ----- |
| Nombre del proyecto | `sentinel_hips` |
| Prefijo del sistema | `HIPS_` para variables de entorno; `hips.` para logs/configuracion |
| Modulos Python | `snake_case`, ejemplo `sniffer_detect.py` |
| Carpetas | `snake_case`, ejemplo `detection/`, `prevention/` |
| Configuracion | `snake_case`, ejemplo `settings.env`, `hips.conf` |
| Templates HTML | `kebab-case`, ejemplo `dashboard-alerts.html` |
| Funciones | `snake_case`, ejemplo `detect_sniffer()` |
| Clases | `PascalCase`, ejemplo `SnifferDetector` |
| Constantes | `UPPER_SNAKE`, ejemplo `MAX_FAILED_ATTEMPTS` |
| Variables de entorno | `UPPER_SNAKE` con prefijo, ejemplo `HIPS_DB_PASSWORD` |
| Tablas | `snake_case` plural, ejemplo `alarmas` |
| Columnas | `snake_case`, ejemplo `ip_origen` |
| Indices | `idx_tabla_columna`, ejemplo `idx_alarmas_timestamp` |
| Claves foraneas | `fk_tabla_ref`, ejemplo `fk_acciones_alarma` |
| Usuario BD | `hips_app`, sin superusuario |
| Rama principal | `main` |
| Ramas de modulo | `feat/modulo-nombre`, ejemplo `feat/sniffer-detection` |
| Ramas de fix | `fix/descripcion` |
| Commits | `tipo(modulo): descripcion`, ejemplo `feat(sniffer): detectar modo promiscuo` |
| Tipos de commit | `feat`, `fix`, `docs`, `test`, `refactor`, `chore` |

### Tipos de alarma

| Modulo | Tipo de alarma |
| ----- | ----- |
| i | `MODIFICACION_ARCHIVO` |
| ii | `USUARIO_SOSPECHOSO` |
| iii | `SNIFFER_DETECTADO` |
| iv | `FAILED_LOGIN_MULTIPLE`, `SCANNER_HTTP` |
| v | `MAIL_QUEUE_ALTA` |
| vi | `PROCESO_ALTO_CONSUMO` |
| vii | `ARCHIVO_TMP_SOSPECHOSO` |
| viii | `DDOS_DETECTADO` |
| ix | `CRON_SOSPECHOSO` |
| x | `ACCESO_INVALIDO_REPETIDO`, `CREDENTIAL_STUFFING` |

## Bloque 4 - Analisis de 3 modulos

### Modulo iii - Sniffers y modo promiscuo

| Campo | Respuesta |
| ----- | ----- |
| Nombre del modulo | Modulo iii: `sniffer_detect` |
| Objetivo concreto | Detectar interfaces en modo promiscuo y procesos de captura de trafico no autorizados. |
| Fuentes de datos | `ip link`, `/sys/class/net/*/flags`, `ps aux`, lista de usuarios/procesos permitidos. |
| Condicion de alarma | Interfaz en modo promiscuo sin autorizacion o proceso `tcpdump`, `wireshark`, `tshark`, `dumpcap` o `ethereal` ejecutandose fuera de ventana autorizada. |
| Comportamiento normal | Captura de trafico aprobada por administrador durante diagnostico. |
| Comportamiento ANOMALO | Captura no autorizada, usuario no permitido o proceso desconocido usando modo promiscuo. |
| Parametros configurables | Interfaces permitidas, usuarios autorizados, procesos permitidos, tiempo maximo de excepcion. |
| Pseudocodigo | 1. Leer interfaces. 2. Detectar flag `PROMISC`. 3. Buscar procesos de sniffing. 4. Comparar con excepciones. 5. Generar alarma si no esta autorizado. |
| Accion de prevencion | Matar proceso no autorizado y registrar accion; en severidad alta, desactivar interfaz temporalmente. |
| Tipo de alarma | `SNIFFER_DETECTADO` |
| Email al admin | Asunto: `[HIPS ALERTA] Sniffer detectado`. Cuerpo: interfaz, proceso, usuario, PID, hora y accion tomada. |
| Dashboard | `timestamp`, `tipo`, `ip_origen`, `modulo`, `accion_tomada`, `pid`, `usuario`. |
| Casos borde | Diagnosticos autorizados, laboratorios, herramientas de monitoreo legitimas. |
| Test automatizable | Mockear salida de `ip link` con `PROMISC` y salida de `ps` con `tcpdump`; verificar alarma. |

### Modulo iv - Analisis de logs

| Campo | Respuesta |
| ----- | ----- |
| Nombre del modulo | Modulo iv: `log_analyzer` |
| Objetivo concreto | Detectar patrones sospechosos en logs del sistema y servicios. |
| Fuentes de datos | `/var/log/secure`, `/var/log/messages`, `/var/log/httpd/access_log`, `/var/log/httpd/error_log`, `journalctl`. |
| Condicion de alarma | Mas de 5 fallos SSH desde la misma IP en 10 minutos, o mas de 30 respuestas HTTP 403/404 desde una IP en 5 minutos, o rutas sospechosas como `.env`, `/wp-admin`, `/phpmyadmin`. |
| Comportamiento normal | Errores aislados, pruebas internas autorizadas o crawler permitido. |
| Comportamiento ANOMALO | Fuerza bruta, scanner HTTP, busqueda de archivos sensibles o errores repetidos desde la misma IP. |
| Parametros configurables | Ventana temporal, maximo de fallos, lista blanca de IPs, patrones HTTP sospechosos. |
| Pseudocodigo | 1. Leer logs nuevos. 2. Parsear timestamp, IP y resultado. 3. Agrupar por IP y ventana. 4. Comparar contra umbrales. 5. Crear alarma. |
| Accion de prevencion | Bloquear IP temporalmente con `firewalld` y registrar en `hosts_bloqueados`. |
| Tipo de alarma | `FAILED_LOGIN_MULTIPLE` o `SCANNER_HTTP` |
| Email al admin | Asunto: `[HIPS ALERTA] Patron sospechoso en logs`. Cuerpo: IP, regla activada, cantidad de eventos, ventana y accion aplicada. |
| Dashboard | `timestamp`, `tipo`, `ip_origen`, `modulo`, `accion_tomada`, `cantidad_eventos`. |
| Casos borde | NAT con muchos usuarios, pentest autorizado, rotacion de logs, crawler legitimo. |
| Test automatizable | Usar logs sinteticos y verificar que el modulo alarma solo al superar el umbral. |

### Modulo x - Intentos de acceso invalidos

| Campo | Respuesta |
| ----- | ----- |
| Nombre del modulo | Modulo x: `access_monitor` |
| Objetivo concreto | Detectar fuerza bruta y credential stuffing contra SSH o login web. |
| Fuentes de datos | `/var/log/secure`, logs de FastAPI, tabla de intentos web, eventos de autenticacion. |
| Condicion de alarma | Mas de 5 intentos fallidos desde una IP en 10 minutos, o intentos contra mas de 5 usuarios distintos desde la misma IP en 10 minutos. |
| Comportamiento normal | Usuario legitimo que falla una o dos veces al escribir su contrasena. |
| Comportamiento ANOMALO | Muchos intentos fallidos, muchos usuarios probados o repeticion de intentos desde la misma IP. |
| Parametros configurables | Maximo de intentos, ventana temporal, duracion del bloqueo, lista blanca, cantidad de usuarios distintos. |
| Pseudocodigo | 1. Registrar intento fallido. 2. Agrupar por IP y ventana. 3. Contar intentos y usuarios distintos. 4. Si supera umbral, generar alarma. 5. Ejecutar prevencion. |
| Accion de prevencion | Bloquear IP por tiempo definido; marcar cuenta para revision si el ataque se concentra en un usuario. |
| Tipo de alarma | `ACCESO_INVALIDO_REPETIDO` o `CREDENTIAL_STUFFING` |
| Email al admin | Asunto: `[HIPS ALERTA] Intentos de acceso invalidos`. Cuerpo: IP, usuarios afectados, cantidad de intentos, ventana y bloqueo aplicado. |
| Dashboard | `timestamp`, `tipo`, `ip_origen`, `modulo`, `accion_tomada`, `usuarios_afectados`. |
| Casos borde | Usuarios detras de NAT, laboratorios, servicios automatizados mal configurados. |
| Test automatizable | Simular 6 intentos fallidos en 10 minutos desde la misma IP y verificar alarma/bloqueo. |
