# Pruebas

Este documento describe las pruebas usadas para validar los tres modulos implementados del HIPS:

- `log_analyzer`
- `process_monitor`
- `users_monitor`

Las acciones preventivas se ejecutan con `HIPS_PREVENTION_DRY_RUN=true`, por lo que el sistema registra la accion que tomaria sin bloquear IPs, usuarios o procesos reales durante la demo.

## Pruebas automaticas

Desde Rocky, dentro del repositorio:

```bash
cd ~/SO2_TP
source .venv/bin/activate
python3 -m pytest -q
```

Resultado esperado:

```text
tests passed
```

Estas pruebas validan la logica interna de deteccion sin depender de eventos reales del sistema.

## Dashboard FastAPI

Levantar el dashboard:

```bash
cd ~/SO2_TP
source .venv/bin/activate
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Desde la Mac abrir:

```text
http://<IP_ROCKY>:8000
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

Resultado esperado:

```json
{"status":"ok"}
```

## Prueba 1: log_analyzer con SSH fallido

Objetivo: validar que el modulo `log_analyzer` detecta multiples intentos fallidos de autenticacion SSH.

Desde la Mac:

```bash
ssh usuario_falso@<IP_ROCKY>
```

Ingresar una contrasena incorrecta varias veces.

En Rocky ejecutar el HIPS:

```bash
cd ~/SO2_TP
sudo .venv/bin/python main.py
```

Resultado esperado en terminal:

```text
Modulo log_analyzer: fuentes=/var/log/secure ... alarmas=1
Insertada: FAILED_LOGIN_MULTIPLE | <IP_MAC> | log_analyzer | ...
Prevencion registrada: accion_id=... | alarma_id=... | block_ip | dry_run=True
```

Resultado esperado en dashboard:

```text
Tipo: FAILED_LOGIN_MULTIPLE
Modulo: log_analyzer
IP origen: <IP_MAC>
Accion tomada: block_ip
```

## Prueba 2: process_monitor con proceso de alto consumo

Objetivo: validar que el modulo `process_monitor` detecta un proceso con CPU alta.

En Rocky generar consumo de CPU:

```bash
yes > /dev/null &
```

El comando devuelve un PID. Luego ejecutar:

```bash
sudo .venv/bin/python main.py
```

Resultado esperado en terminal:

```text
Modulo process_monitor: ... alarmas=1
Insertada: PROCESO_ALTO_CONSUMO | N/A | process_monitor | PID ... comando yes CPU ...
Prevencion registrada: accion_id=... | alarma_id=... | kill_process | dry_run=True
```

Resultado esperado en dashboard:

```text
Tipo: PROCESO_ALTO_CONSUMO
Modulo: process_monitor
Detalle: PID ... comando yes CPU ...
Accion tomada: kill_process
```

Como la prevencion esta en `dry_run=true`, el proceso no se mata automaticamente. Finalizarlo manualmente:

```bash
pkill yes
```

## Prueba 3: users_monitor con sesiones SSH simultaneas

Objetivo: validar que el modulo `users_monitor` detecta multiples sesiones simultaneas del mismo usuario.

Desde la Mac abrir tres terminales y conectarse en cada una:

```bash
ssh lucasfadul@<IP_ROCKY>
```

Dejar las tres sesiones abiertas.

En Rocky verificar las sesiones:

```bash
who
```

Resultado esperado:

```text
lucasfadul pts/0 ...
lucasfadul pts/1 ...
lucasfadul pts/2 ...
```

Ejecutar el HIPS:

```bash
sudo .venv/bin/python main.py
```

Resultado esperado en terminal:

```text
Modulo users_monitor: ... alarmas=1
Insertada: USUARIO_SOSPECHOSO | N/A | users_monitor | Usuario con 3 sesiones simultaneas: lucasfadul
Prevencion registrada: accion_id=... | alarma_id=... | lock_user | dry_run=True
```

Resultado esperado en dashboard:

```text
Tipo: USUARIO_SOSPECHOSO
Modulo: users_monitor
Detalle: Usuario con 3 sesiones simultaneas: lucasfadul
Accion tomada: lock_user
```

Cerrar las sesiones SSH al terminar:

```bash
exit
```

## Verificacion en base de datos

Para ver las alarmas registradas:

```bash
sudo -u postgres psql -d hips -c "SELECT id, tipo_alarma, modulo, severidad, detalle, resuelta FROM alarmas ORDER BY id DESC LIMIT 10;"
```

Para ver las acciones preventivas:

```bash
sudo -u postgres psql -d hips -c "SELECT id, alarma_id, accion, resultado FROM acciones_prevencion ORDER BY id DESC LIMIT 10;"
```

## Resultado esperado de la demo

Al finalizar, el dashboard debe mostrar alarmas de los tres modulos:

```text
log_analyzer     -> FAILED_LOGIN_MULTIPLE
process_monitor  -> PROCESO_ALTO_CONSUMO
users_monitor    -> USUARIO_SOSPECHOSO
```
