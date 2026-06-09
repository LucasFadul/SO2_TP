**SISTEMAS OPERATIVOS**

**HIPS — Taller de Kickoff de Desarrollo**

Entregables completos — Bloques 1 a 4

**Alumno: Lucas Fadul**

Junio 2026

# **Bloque 1 — Stack Tecnológico y Hardening**

## **1.1 Decisiones del Stack**

| Componente | Opción elegida | Justificación |
| ----- | ----- | ----- |
| Lenguaje principal | Python 3.x | Librería estándar cubre lectura de logs, procesos (psutil), hashing (hashlib) y sockets. Scripts de detección son cortos y mantenibles. Bash queda para wrappers de prueba. |
| Web framework | FastAPI | API REST nativa con validación automática via Pydantic, documentación Swagger/OpenAPI generada automáticamente (útil para endpoints del dashboard). Async permite manejar múltiples consultas al dashboard sin bloquear. Django agrega ORM y admin no requeridos; Flask no tiene validación de tipos integrada. |
| ORM / acceso BD | psycopg2 \+ SQL plano | Queries de inserción de alarmas son simples. Evita overhead de un ORM completo; mantiene legibilidad para el equipo y facilita auditoría de queries. |
| Sistema operativo | Rocky Linux 9 (latest stable) | Requerimiento del enunciado. RHEL-compatible, soporte hasta 2032, SELinux enforcing por defecto, alineado a CIS Benchmark y STIGs de DISA. |
| Base de datos | PostgreSQL 16 | Requerimiento del enunciado. CIS Benchmark disponible, soporte SSL nativo, logging granular, row-level security. Versión 16 en repos RHEL9. |
| Testing | pytest \+ subprocess mocks | Estándar de facto en Python. Permite fixtures para simular archivos de log, salidas de comandos y condiciones de alarma sin root real. |
| Alertas email | smtplib (stdlib) | Sin dependencias externas. Configuración por variable de entorno HIPS\_SMTP\_\*. Suficiente para envío SMTP relay interno. |
| Encriptación config | GPG (gnupg stdlib wrapper) | GPG disponible en Rocky Linux, bien documentado, permite cifrar baseline\_hashes.enc con clave asimétrica. Alternativa: openssl enc AES-256-CBC. |

## **1.2 Hardening del Sistema Operativo — Rocky Linux**

Mínimo 10 controles. Cada uno verificable con comando concreto.

| \# | Área / Control | Qué se configura | Comando de verificación / implementación |
| ----- | ----- | ----- | ----- |
| 1 | SELinux enforcing | SELinux en modo enforcing permanente. Política targeted activa. | getenforce  →  debe retornar Enforcingsed \-i 's/^SELINUX=.\*/SELINUX=enforcing/' /etc/selinux/config |
| 2 | firewalld — zonas y servicios | Zona default: drop. Sólo puertos 22 (SSH), 443 (HTTPS dashboard) y 5432 local habilitados. | firewall-cmd \--list-allfirewall-cmd \--set-default-zone=dropfirewall-cmd \--add-port=22/tcp \--permanent |
| 3 | SSH hardening | Root login deshabilitado, autenticación por clave pública obligatoria, puerto cambiado a 2222, MaxAuthTries 3, Banner activado. | sshd \-T | grep \-E 'permitrootlogin|passwordauth|port'grep \-E 'PermitRootLogin|PasswordAuthentication|Port' /etc/ssh/sshd\_config |
| 4 | Usuarios y privilegios mínimos | Usuario hips\_app sin sudo, sin shell interactiva. Contraseñas de sistema con política: minlen=12, ucredit=-1, dcredit=-1. | id hips\_appgrep hips\_app /etc/passwd  →  shell debe ser /sbin/nologinauthconfig \--test | grep password (o authselect) |
| 5 | auditd configurado | Reglas de auditoría para accesos a /etc/passwd, /etc/shadow, /etc/sudoers y ejecuciones de binarios en /bin, /usr/bin. | auditctl \-lgrep passwd /etc/audit/rules.d/\*.rulesausearch \-f /etc/shadow |
| 6 | Montaje /tmp noexec,nosuid,nodev | /tmp montado con opciones noexec nosuid nodev para impedir ejecución de scripts subidos. | mount | grep /tmpgrep /tmp /etc/fstab  →  debe tener noexec,nosuid,nodev |
| 7 | Banner de login | /etc/issue y /etc/issue.net con banner legal. Parámetro Banner en sshd\_config. | cat /etc/issuegrep Banner /etc/ssh/sshd\_config |
| 8 | Deshabilitar servicios innecesarios | Servicios avahi, bluetooth, cups, rpcbind deshabilitados y no instalados. | systemctl list-unit-files \--state=enabled | grep \-E 'avahi|bluetooth|cups|rpcbind'systemctl is-enabled avahi-daemon |
| 9 | Actualización automática de seguridad (dnf-automatic) | dnf-automatic configurado para aplicar sólo actualizaciones de seguridad diariamente. | systemctl status dnf-automatic.timercat /etc/dnf/automatic.conf | grep upgrade\_type |
| 10 | umask 027 y permisos de home | umask 027 en /etc/profile y /etc/bashrc. Directorios home con permisos 750\. | grep umask /etc/profile /etc/bashrcstat \-c '%a %U' /home/\* |

## **1.3 Hardening de la Base de Datos — PostgreSQL (CIS)**

| \# | Control CIS / Área | Qué se configura | Verificación (SQL o comando) |
| ----- | ----- | ----- | ----- |
| 1 | Usuario de aplicación sin superusuario | Rol hips\_app creado con LOGIN, sin SUPERUSER, CREATEDB, CREATEROLE. Solo permisos SELECT/INSERT sobre tablas HIPS. | SELECT rolname, rolsuper, rolcreatedb FROM pg\_roles WHERE rolname='hips\_app';→ rolsuper debe ser false |
| 2 | SSL activo (ssl=on) | ssl=on en postgresql.conf. Certificado autofirmado o CA interna. Conexiones no-SSL rechazadas para hips\_app vía pg\_hba.conf hostssl. | SHOW ssl;SELECT pg\_postmaster\_start\_time(); \-- verificar con psql \-h host (falla sin SSL) |
| 3 | log\_connections y log\_disconnections | log\_connections=on y log\_disconnections=on en postgresql.conf para auditar todas las sesiones. | SHOW log\_connections;SHOW log\_disconnections;grep log\_connections /etc/postgresql/\*/main/postgresql.conf |
| 4 | Contraseñas nunca en código — password\_encryption | password\_encryption=scram-sha-256 en postgresql.conf. Contraseñas de usuarios sólo en variables de entorno (HIPS\_DB\_PASSWORD), no en código. | SHOW password\_encryption;grep password\_encryption postgresql.conf  →  debe ser scram-sha-256 |
| 5 | listen\_addresses restringido | listen\_addresses='localhost' en postgresql.conf. PostgreSQL solo accesible desde la misma máquina; web y detección conectan por socket Unix. | SHOW listen\_addresses;ss \-tlnp | grep 5432  →  debe mostrar 127.0.0.1 únicamente |
| 6 | log\_failed\_logins / log\_min\_duration | log\_min\_duration\_statement=1000 para queries lentas. log\_line\_prefix='%t \[%p\]: \[%l-1\] user=%u,db=%d,app=%a,client=%h ' para trazabilidad. | SHOW log\_min\_duration\_statement;SHOW log\_line\_prefix; |
| 7 | Revocación de permisos públicos en pg\_catalog | REVOKE ALL ON SCHEMA public FROM PUBLIC. Sólo hips\_app y hips\_admin tienen acceso al esquema hips. | SELECT grantee, privilege\_type FROM information\_schema.role\_table\_grants WHERE table\_schema='public';\\dn+ (psql)  →  verificar permisos de esquema |

## **1.4 Esquema inicial de base de datos**

| Tabla | Columnas | Propósito |
| ----- | ----- | ----- |
| alarmas | id SERIAL PK, timestamp TIMESTAMPTZ NOT NULL, tipo\_alarma VARCHAR(50), ip\_origen INET, modulo VARCHAR(30), resuelta BOOLEAN DEFAULT false, severidad SMALLINT (1-3) | Registro central de todas las alarmas detectadas por cualquier módulo. |
| acciones\_prevencion | id SERIAL PK, alarma\_id INT FK→alarmas, accion VARCHAR(80), timestamp TIMESTAMPTZ, resultado VARCHAR(20) (OK/FAIL/SKIP), detalle TEXT | Log de cada acción ejecutada por el módulo de prevención. |
| usuarios\_web | id SERIAL PK, username VARCHAR(50) UNIQUE, password\_hash VARCHAR(200), rol VARCHAR(20) (admin/viewer), ultimo\_login TIMESTAMPTZ, activo BOOLEAN DEFAULT true | Acceso autenticado al dashboard FastAPI. |
| configuracion\_modulos | id SERIAL PK, modulo VARCHAR(30), parametro VARCHAR(60), valor TEXT, activo BOOLEAN DEFAULT true, actualizado\_en TIMESTAMPTZ | Umbrales y parámetros configurables por módulo desde la interfaz web. |
| baseline\_hashes | id SERIAL PK, ruta TEXT UNIQUE, hash\_sha256 CHAR(64), registrado\_en TIMESTAMPTZ, algoritmo VARCHAR(20) DEFAULT 'sha256' | Hashes de referencia para el módulo de integridad de archivos (Módulo i). |
| eventos\_login | id SERIAL PK, timestamp TIMESTAMPTZ, ip\_origen INET, usuario\_intento VARCHAR(100), servicio VARCHAR(20) (ssh/web), exitoso BOOLEAN, alarma\_id INT FK→alarmas | Detalle de intentos de login para Módulo x (brute force / credential stuffing). |

# **Bloque 2 — Mapa de Trabajo**

## **2.1 Módulos del sistema**

| \# | Módulo / Componente | Responsable | Complejidad | Dependencias | Semana |
| ----- | ----- | ----- | ----- | ----- | ----- |
| i | Integridad de archivos (/etc/passwd · /etc/shadow · binarios) | Lucas Fadul | Alta | hashlib, logger, BD (baseline\_hashes) | 2 |
| ii | Usuarios conectados (who / last / origen de conexión) | Lucas Fadul | Media | who, last, logger, BD | 2 |
| iii | Sniffers y modo promiscuo (tcpdump · wireshark · ethereal) | Lucas Fadul | Media | ip link, ps, logger | 1 |
| iv | Análisis de logs (/var/log/secure · httpd/access.log · maillog) | Lucas Fadul | Alta | parser, logger, BD | 1 |
| v | Cola de correo (mailq · detección spam masivo) | Lucas Fadul | Media | mailq, MTA (postfix) | 3 |
| vi | Procesos con alto consumo de recursos (CPU / RAM) | Lucas Fadul | Media | psutil, umbrales config, logger | 3 |
| vii | Directorio /tmp (procesos · scripts ejecutables) | Lucas Fadul | Media | os, stat, ps, logger | 3 |
| viii | Ataques DDoS (log DNS provisto por el profesor) | Lucas Fadul | Alta | log DNS externo, parser, BD | 4 |
| ix | Archivos cron sospechosos (/etc/crontab · /var/spool/cron) | Lucas Fadul | Media | /etc/crontab, cron spool, logger | 4 |
| x | Intentos de acceso inválidos (brute force · credential stuffing) | Lucas Fadul | Alta | logs SSH/web, eventos\_login, BD | 1 |
| — | Módulo de Prevención (30% nota) | Lucas Fadul | Alta | todos los módulos de detección | 5 |
| — | Interfaz web \+ dashboard | Lucas Fadul | Alta | FastAPI, PostgreSQL, alarmas | 4 |
| — | Sistema de alertas por email | Lucas Fadul | Media | smtplib, alarmas, web | 4 |
| — | Logger central (/var/log/hips/) | Lucas Fadul | Media | todos los módulos | 1 |
| — | PostgreSQL \+ 7 controles CIS | Lucas Fadul | Media | VM Rocky Linux | 2 |
| — | Carpeta encriptada de configuración | Lucas Fadul | Media | GPG/OpenSSL, permisos | 1 |
| — | Rocky Linux \+ 10 controles hardening | Lucas Fadul | Alta | VM base | 1 |
| — | Suite de pruebas automatizadas | Lucas Fadul | Alta | pytest, todos los módulos | 5 |
| — | Manual de uso \+ manual de instalación | Lucas Fadul | Media | proyecto completo | 5 |

# **Bloque 3 — Protocolo de Nomenclatura**

## **3.1 Nombre del proyecto**

| Ítem | Decisión |
| ----- | ----- |
| Nombre del proyecto (código) | hips\_rocky |
| Prefijo del sistema (logs, variables) | HIPS\_ |

## **3.2 Archivos y carpetas**

| Ítem | Convención elegida | Ejemplo |
| ----- | ----- | ----- |
| Módulos Python | snake\_case | sniffer\_detect.py |
| Carpetas | snake\_case | detection/, prevention/, tests/ |
| Archivos de config | snake\_case con extensión | hips.conf, .env.example |
| Templates HTML | kebab-case | dashboard-alerts.html, login-form.html |
| Archivos de test | test\_ prefijo \+ snake\_case | test\_sniffer\_detect.py |

## **3.3 Código Python**

| Ítem | Convención elegida | Ejemplo |
| ----- | ----- | ----- |
| Funciones | snake\_case | detect\_sniffer(), block\_ip(), parse\_log\_line() |
| Clases | PascalCase | SnifferDetector, LogAnalyzer, AlarmDispatcher |
| Constantes | UPPER\_SNAKE\_CASE | MAX\_FAILED\_ATTEMPTS \= 5, CHECK\_INTERVAL\_SEC \= 60 |
| Variables de entorno | UPPER\_SNAKE con prefijo HIPS\_ | HIPS\_DB\_PASSWORD, HIPS\_SMTP\_HOST |
| Parámetros de módulo (config BD) | lower\_snake con prefijo módulo | sniffer\_check\_interval, access\_max\_attempts |
| Archivos de test | test\_ \+ nombre del módulo | test\_sniffer\_detect.py, test\_access\_monitor.py |

## **3.4 Base de datos (PostgreSQL)**

| Ítem | Convención elegida | Ejemplo |
| ----- | ----- | ----- |
| Tablas | snake\_case · plural | alarmas, acciones\_prevencion, eventos\_login |
| Columnas | snake\_case | ip\_origen, tipo\_alarma, password\_hash |
| Índices | idx\_tabla\_columna | idx\_alarmas\_timestamp, idx\_eventos\_ip\_origen |
| Claves foráneas | fk\_tabla\_ref | fk\_acciones\_alarma, fk\_eventos\_alarma |
| Usuario de aplicación | nombre restrictivo, sin superusuario | hips\_app |

## **3.5 GIT — Ramas y commits**

| Ítem | Convención elegida |
| ----- | ----- |
| Rama principal | main |
| Ramas de módulos | feat/modulo-nombre  (ej: feat/sniffer-detection, feat/access-monitor) |
| Ramas de fix | fix/descripcion  (ej: fix/log-format, fix/alarm-timestamp) |
| Formato de commit | tipo(módulo): descripción  (ej: feat(sniffer): detección modo promiscuo) |
| Tipos de commit | feat · fix · docs · test · refactor · chore |
| Frecuencia mínima de commit | Al terminar cada función \+ al fin de cada sesión de trabajo |

## **3.6 Tipos de alarma (log)**

| Módulo | Nombre del tipo de alarma | Ejemplo en log |
| ----- | ----- | ----- |
| i — Integridad archivos | MODIFICACION\_ARCHIVO | 29/05/2026 :: MODIFICACION\_ARCHIVO :: /etc/passwd |
| ii — Usuarios conectados | USUARIO\_SOSPECHOSO | 29/05/2026 :: USUARIO\_SOSPECHOSO :: 192.168.1.10 |
| iii — Sniffers | SNIFFER\_DETECTADO | 29/05/2026 :: SNIFFER\_DETECTADO :: eth0 |
| iv — Análisis de logs | FAILED\_LOGIN\_MULTIPLE · SCANNER\_HTTP | 29/05/2026 :: FAILED\_LOGIN\_MULTIPLE :: 10.0.0.25 |
| v — Cola de correo | MAIL\_QUEUE\_ALTA | 29/05/2026 :: MAIL\_QUEUE\_ALTA :: queue=487 |
| vi — Procesos CPU/RAM | PROCESO\_ALTO\_CONSUMO | 29/05/2026 :: PROCESO\_ALTO\_CONSUMO :: pid=3912 cpu=97% |
| vii — Directorio /tmp | ARCHIVO\_TMP\_SOSPECHOSO | 29/05/2026 :: ARCHIVO\_TMP\_SOSPECHOSO :: /tmp/rev.sh |
| viii — DDoS DNS | DDOS\_DETECTADO | 29/05/2026 :: DDOS\_DETECTADO :: 203.0.113.5 |
| ix — Cron sospechoso | CRON\_SOSPECHOSO | 29/05/2026 :: CRON\_SOSPECHOSO :: /var/spool/cron/root |
| x — Accesos inválidos | ACCESO\_INVALIDO\_REPETIDO · CREDENTIAL\_STUFFING | 29/05/2026 :: ACCESO\_INVALIDO\_REPETIDO :: 10.0.0.8 |

# **Bloque 4 — Análisis de Requerimientos**

**Módulos seleccionados: ii (Usuarios conectados — simple), vi (Procesos CPU/RAM — simple), iv (Análisis de logs — complejo).**

## **Módulo ii — Usuarios Conectados (who / last / origen de conexión)**

| Campo | Detalle |
| ----- | ----- |
| Nombre del módulo | Módulo ii: users\_monitor.py |
| Objetivo concreto | Detectar sesiones de usuarios activas o recientes que resulten sospechosas: usuarios que no deberían tener sesión interactiva, conexiones desde IPs externas inesperadas, o múltiples sesiones simultáneas del mismo usuario. |
| Fuentes de datos | 1\. who (sesiones activas con usuario, terminal, IP de origen)2. last \-n 50 (últimos 50 logins, incluyendo reboots)3. /var/log/wtmp (archivo binario leído por who/last)4. /etc/passwd (lista de usuarios del sistema con shell válida) |
| Condición de alarma | Se dispara si:(a) Usuario con shell /sbin/nologin o /bin/false aparece en who → sesión imposible según configuración.(b) Conexión SSH desde IP no perteneciente a rango de red local (configurado en whitelist\_redes).(c) Mismo usuario con \>2 sesiones simultáneas activas.Umbral: inmediato, sin ventana temporal. |
| Comportamiento NORMAL (no alarmar) | Administrador conectado desde IP de la red local configurada.Un único usuario con una sola sesión SSH activa.Usuario root sin sesión interactiva (sólo sudo desde otro usuario). |
| Comportamiento ANÓMALO (alarmar) | Usuario hips\_app (shell=/sbin/nologin) aparece en who → escalación de privilegios o bypass.Conexión SSH desde IP pública no en whitelist → acceso externo no autorizado.Mismo usuario con 3 o más sesiones simultáneas → posible sesión secuestrada o script automatizado. |
| Parámetros configurables (interfaz web) | users\_check\_interval (seg, default: 60)users\_whitelist\_redes (CIDR, default: 192.168.0.0/16, 10.0.0.0/8)users\_max\_sesiones (default: 2)users\_usuarios\_excluidos (default: vacío) |
| Lógica de detección (pseudocódigo) | 1\. output \= run('who')  →  parsear líneas: usuario, terminal, timestamp, ip\_origen2. Para cada sesión:   a. Si usuario in nologin\_users (leer /etc/passwd) → ALARMA USUARIO\_SOSPECHOSO   b. Si ip\_origen NOT IN whitelist\_redes → ALARMA USUARIO\_SOSPECHOSO3. Contar sesiones por usuario → si count \> max\_sesiones → ALARMA USUARIO\_SOSPECHOSO4. Registrar en BD, disparar prevención si corresponde |
| Acción de prevención | 1\. pkill \-KILL \-u {usuario} (cerrar todas las sesiones del usuario sospechoso)2. Registrar en acciones\_prevencion con resultado OK/FAIL3. Enviar email al admin con usuario, IP y terminal afectados |
| Tipo de alarma en log | USUARIO\_SOSPECHOSO |
| Contenido del email al admin | Asunto: \[HIPS ALERTA\] Sesión sospechosa — usuario {usuario}Cuerpo: Usuario: {usuario}IP origen: {ip}Terminal: {tty}Timestamp: {ts}Motivo: {motivo (nologin / IP externa / sesiones multiples)}Acción: {accion\_tomada}Ver dashboard: https://localhost/dashboard |
| Visibilidad en dashboard | timestamp | USUARIO\_SOSPECHOSO | ip\_origen | módulo=ii | accion\_tomada |
| Casos borde / falsos positivos | 1\. Cron ejecuta script bajo usuario de servicio → aparece momentáneamente en who con pseudo-terminal; filtrar por terminal pts/tty.2. Usuario de monitoreo (zabbix, prometheus) puede tener sesión temporal legítima → agregar a usuarios\_excluidos.3. IP de VPN puede estar fuera del rango local por diseño → ampliar whitelist\_redes con rango VPN. |
| Test automatizable | pytest: mockear salida de who con usuario hips\_app (shell nologin) y verificar que check\_sessions() genera alarma.Test IP externa: mockear sesión con IP 203.0.113.5 → verificar alarma.Test multi-sesión: mockear 3 líneas del mismo usuario → verificar alarma.Test negativo: sesión normal desde 192.168.1.10 → sin alarma. |

## **Módulo vi — Procesos con Alto Consumo de Recursos (CPU / RAM)**

| Campo | Detalle |
| ----- | ----- |
| Nombre del módulo | Módulo vi: process\_monitor.py |
| Objetivo concreto | Detectar procesos que consumen CPU o memoria por encima de umbrales configurados. Un proceso con consumo anormal puede indicar minería de criptomonedas, un exploit en ejecución, o un loop descontrolado producto de un ataque. |
| Fuentes de datos | 1\. psutil.process\_iter() — librería Python, lee /proc directamente2. Alternativamente: salida de ps aux (cpu%, mem%, pid, nombre, usuario)No requiere archivos de log: consulta el estado del sistema en tiempo real. |
| Condición de alarma | Se dispara si cualquier proceso supera:(a) CPU \> 80% sostenido por más de process\_cpu\_window\_sec segundos (default: 30 seg), O(b) RAM \> process\_mem\_threshold\_pct % de la memoria total (default: 70%).Ambos umbrales configurables. Se excluyen procesos en whitelist. |
| Comportamiento NORMAL (no alarmar) | Compilación o tarea batch programada con alto consumo momentáneo (\< 30 seg).Proceso en whitelist (ej: postgres durante vacuum, rsync durante backup).CPU alta pero proceso es del usuario hips\_admin y está en whitelist de procesos permitidos. |
| Comportamiento ANÓMALO (alarmar) | Proceso desconocido (no en whitelist) sosteniendo CPU \> 80% por más de 30 seg → posible miner o exploit.Proceso corriendo bajo usuario de servicio (hips\_app, postgres) con RAM \> 70% → comportamiento inesperado.Múltiples instancias del mismo proceso desconocido spawneadas en corto tiempo. |
| Parámetros configurables (interfaz web) | process\_cpu\_threshold (%, default: 80)process\_cpu\_window\_sec (seg sostenido, default: 30)process\_mem\_threshold\_pct (%, default: 70)process\_check\_interval (seg, default: 15)process\_whitelist (nombres de proceso separados por coma, default: postgres,rsync,find) |
| Lógica de detección (pseudocódigo) | 1\. Cada process\_check\_interval segundos:   procesos \= psutil.process\_iter(\['pid','name','username','cpu\_percent','memory\_percent'\])2. Para cada proceso:   a. Si nombre NOT IN whitelist y cpu\_percent \> cpu\_threshold:      contador\_cpu\[pid\] \+= check\_interval      Si contador\_cpu\[pid\] \>= cpu\_window → ALARMA PROCESO\_ALTO\_CONSUMO   b. Si nombre NOT IN whitelist y memory\_percent \> mem\_threshold → ALARMA inmediata3. Limpiar contadores de procesos que ya no existen |
| Acción de prevención | 1\. os.kill(pid, signal.SIGTERM)  →  si no termina en 5 seg: os.kill(pid, signal.SIGKILL)2. Registrar en acciones\_prevencion con pid, nombre, usuario, cpu%, mem%3. Enviar email al admin |
| Tipo de alarma en log | PROCESO\_ALTO\_CONSUMO |
| Contenido del email al admin | Asunto: \[HIPS ALERTA\] Proceso con alto consumo — PID {pid}Cuerpo: PID: {pid}Nombre: {nombre}Usuario: {usuario}CPU: {cpu}%  RAM: {mem}%Tiempo sostenido: {seg} segundosAcción: proceso terminado (SIGKILL)Timestamp: {ts}Ver dashboard: https://localhost/dashboard |
| Visibilidad en dashboard | timestamp | PROCESO\_ALTO\_CONSUMO | ip\_origen=localhost | módulo=vi | accion=PROCESO\_TERMINADO |
| Casos borde / falsos positivos | 1\. Backup nocturno (rsync, tar) consume CPU/RAM legítimamente → agregar a whitelist.2. PostgreSQL durante VACUUM o reindex → agregar postgres a whitelist.3. Proceso de corta duración que puntualmente spikea CPU pero termina solo antes de la ventana → no alarma (por diseño del contador). |
| Test automatizable | pytest: mockear psutil.process\_iter() con proceso 'minerd' al 95% CPU por 35 seg → verificar alarma PROCESO\_ALTO\_CONSUMO.Test negativo: proceso 'postgres' al 90% → sin alarma (en whitelist).Test RAM: mockear proceso con memory\_percent=75 → verificar alarma inmediata.Integración: lanzar 'yes \> /dev/null &' en VM de test, verificar que el módulo lo detecta y mata. |

## **Módulo iv — Análisis de Logs**

| Campo | Detalle |
| ----- | ----- |
| Nombre del módulo | Módulo iv: log\_analyzer.py |
| Objetivo concreto | Analizar en tiempo casi-real los logs del sistema (/var/log/secure, /var/log/httpd/access.log, /var/log/maillog) para detectar: múltiples intentos de login fallido SSH, escaneos HTTP (4xx repetidos), y actividad anómala de correo. Es el módulo de mayor volumen de datos y mayor riesgo de falsos positivos. |
| Fuentes de datos | 1\. /var/log/secure (autenticación SSH, sudo, PAM)2. /var/log/httpd/access.log (si Apache instalado) o /var/log/nginx/access.log3. /var/log/maillog (postfix/sendmail)4. journalctl \-u sshd (alternativo)Lectura: tail \-F con seek al último offset guardado en BD (evitar releer todo el archivo) |
| Condición de alarma | FAILED\_LOGIN\_MULTIPLE: \>5 intentos fallidos SSH desde la misma IP en ventana de 10 minutos.SCANNER\_HTTP: \>50 respuestas 4xx desde la misma IP en ventana de 5 minutos.Ambos umbrales configurables desde interfaz web. |
| Comportamiento NORMAL (no alarmar) | Usuario legítimo olvida contraseña: 1-3 intentos fallidos aislados.Crawler de Google/Bing: User-Agent conocido \+ patrón regular de 404.Monitoreo de salud (healthcheck): IPs internas en whitelist con 404 esperado. |
| Comportamiento ANÓMALO (alarmar) | FAILED\_LOGIN\_MULTIPLE: misma IP intenta \>5 usuarios distintos en 10 min → credential stuffing.SCANNER\_HTTP: IP desconocida genera \>50 errores 4xx/5xx en 5 min → escaneo de vulnerabilidades.Patrones de log corruptos o truncados inesperadamente → posible evidence tampering. |
| Parámetros configurables (interfaz web) | log\_ssh\_max\_fails (default: 5)log\_ssh\_window\_sec (default: 600)log\_http\_max\_4xx (default: 50)log\_http\_window\_sec (default: 300)log\_whitelist\_ips (IPs internas excluidas del análisis)log\_check\_interval (seg, default: 30\) |
| Lógica de detección (pseudocódigo) | 1\. Leer nuevas líneas de /var/log/secure desde último\_offset\_guardado   Regex: 'Failed password for .\* from (IP) port'   Actualizar contador\[IP\] con timestamp   Si contador\[IP\] en ventana \> max\_fails → ALARMA FAILED\_LOGIN\_MULTIPLE2. Leer nuevas líneas de access.log   Regex: '(IP) .\* " \[45\]\\d\\d '   Si contador\_4xx\[IP\] en ventana \> max\_4xx → ALARMA SCANNER\_HTTP3. Guardar offset actual en BD para próxima ejecución4. Limpiar contadores expirados (fuera de ventana temporal) |
| Acción de prevención | 1\. firewalld: firewall-cmd \--add-rich-rule='rule family=ipv4 source address={IP} drop' \--timeout=36002. Registrar en acciones\_prevencion3. Enviar email al admin con detalles de IP y conteo |
| Tipo de alarma en log | FAILED\_LOGIN\_MULTIPLE · SCANNER\_HTTP |
| Contenido del email al admin | Asunto: \[HIPS ALERTA\] {tipo\_alarma} desde {ip}Cuerpo: IP origen: {ip}Intentos/Errores detectados: {conteo} en {ventana} segundosPrimer intento: {timestamp\_inicio}Último intento: {timestamp\_fin}Acción: IP bloqueada por 1 hora vía firewalldVer dashboard: https://localhost/dashboard |
| Visibilidad en dashboard | timestamp | FAILED\_LOGIN\_MULTIPLE | ip\_origen | módulo=iv | accion=IP\_BLOQUEADA |
| Casos borde / falsos positivos | 1\. VPN corporativa: múltiples usuarios detrás de una IP → agregar IP a whitelist.2. Script de CI/CD: hace peticiones 404 legítimas → agregar a whitelist.3. Rotación de logs (logrotate): offset guardado apunta a archivo viejo → manejar ENOENT y resetear offset.4. Log con encoding incorrecto: líneas con bytes inválidos → usar errors='replace' en open(). |
| Test automatizable | pytest: crear fixture con archivo de log sintético con 6 intentos fallidos desde 10.0.0.1 en 5 min.Verificar que parse\_secure\_log() retorna alarma con ip='10.0.0.1'.Test negativo: 4 intentos en 10 min → no alarma.Integración: generar intentos SSH fallidos reales con ssh user@localhost (contraseña incorrecta) en VM de test. |

