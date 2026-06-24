# Escenario reproducible para la entrega

Este documento define el orden recomendado para demostrar el HIPS sin
improvisar ni modificar recursos criticos de Rocky Linux.

## Objetivo

La entrega debe demostrar cuatro capas:

1. los diez modulos contienen logica de deteccion verificable;
2. los eventos reales de Rocky son detectados por el runner;
3. las alarmas y acciones llegan a PostgreSQL, logs, email y dashboard;
4. el sistema esta configurado de forma segura para la demostracion.

Las pruebas automatizadas cubren los diez modulos. La parte en vivo utiliza los
eventos que son seguros y reproducibles en una maquina virtual.

## 1. Preparacion previa

Realizar esta preparacion antes del dia de la entrega.

### 1.1 Actualizar el proyecto

```bash
cd ~/SO2_TP
git pull
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 1.2 Configuracion segura

Comprobar en `.env`:

```dotenv
HIPS_PREVENTION_DRY_RUN=true
HIPS_EMAIL_DRY_RUN=false
```

`dry-run` evita bloquear la Mac, cerrar usuarios o terminar servicios durante
la presentacion. El correo puede mantenerse real para demostrar la alerta.

No mostrar las contraseñas de `.env`.

### 1.3 Restaurar configuracion y preparar fixtures

Desde `/config`, usar `Restaurar` y luego configurar:

| Modulo | Parametro para la demo |
| --- | --- |
| Usuarios Conectados | Sesiones maximas: `2` |
| Directorio Temporal | Directorio: `/tmp/hips_demo` |
| Deteccion DDoS | Log: `data/dns.log`; limite: `1000` |
| Tareas Cron | Archivos: `/tmp/hips_demo/cron_test` |

Crear los datos controlados:

```bash
cd ~/SO2_TP
bash scripts/demo_fixtures.sh prepare
```

### 1.4 Ejecutar el preflight

```bash
bash scripts/demo_preflight.sh
```

Resolver los `[WARN]` importantes antes de la entrega.

### 1.5 Verificar toda la suite

```bash
python3 -m pytest -q
```

Resultado actual esperado:

```text
28 passed
```

## 2. Disposicion de la demostracion

Preparar:

- Terminal A: dashboard;
- Terminal B: ejecutar `main.py`;
- Terminal C: observar logs y comandos de prueba;
- navegador de la Mac: dashboard;
- otras terminales de la Mac: conexiones SSH.

### Terminal A - Dashboard

```bash
cd ~/SO2_TP
source .venv/bin/activate
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

### Terminal C - Logs en tiempo real

```bash
sudo tail -f /var/log/hips/alarmas.log
```

Desde la Mac abrir:

```text
http://<IP_ROCKY>:8000
```

## 3. Primera demostracion: los 10 modulos

Esta es la prueba automatizada y reproducible de toda la logica de deteccion:

```bash
python3 -m pytest tests/test_all_modules.py -v
```

La opcion `-v` muestra el nombre de cada prueba. Deben aparecer diez resultados
`PASSED`, uno por cada modulo:

1. integridad de archivos;
2. usuarios conectados;
3. sniffers;
4. analisis de logs;
5. cola de correo;
6. procesos;
7. `/tmp`;
8. DDoS;
9. cron;
10. accesos invalidos.

Frase para explicar:

> Estas pruebas utilizan datos controlados y directorios temporales. Validan
> los diez detectores sin modificar `/etc`, bloquear IP, cerrar usuarios ni
> terminar procesos reales.

## 4. Segunda demostracion: integracion real

En esta parte se muestra el recorrido completo:

```text
evento -> detector -> PostgreSQL -> prevencion -> log -> email -> dashboard
```

### 4.1 SSH fallido: modulos 4 y 10

Desde la Mac:

```bash
ssh usuario_falso@<IP_ROCKY>
```

Ingresar una contraseña incorrecta varias veces.

En Terminal B:

```bash
sudo .venv/bin/python3 main.py
```

Esperado:

```text
FAILED_LOGIN_MULTIPLE | log_analyzer
ACCESO_INVALIDO_REPETIDO | access_monitor
```

Mostrar en el dashboard:

- IP de la Mac;
- severidad;
- detalle;
- accion `block_ip`;
- correo recibido.

### 4.2 Usuarios conectados: modulo 2

Abrir tres sesiones desde terminales separadas de la Mac:

```bash
ssh lucasfadul@<IP_ROCKY>
```

En Rocky:

```bash
who
sudo .venv/bin/python3 main.py
```

Esperado:

```text
USUARIO_SOSPECHOSO | users_monitor
```

Mostrar la cantidad de sesiones y la accion `lock_user`.

### 4.3 Sniffer: modulo 3

En Terminal C:

```bash
sudo tcpdump -i enp0s1 > /dev/null &
ps aux | grep '[t]cpdump'
```

En Terminal B:

```bash
sudo .venv/bin/python3 main.py
```

Esperado:

```text
SNIFFER_DETECTADO | sniffer_detect
```

Detener la prueba:

```bash
sudo pkill tcpdump
```

### 4.4 Proceso de alto consumo: modulo 6

```bash
yes > /dev/null &
sudo .venv/bin/python3 main.py
pkill yes
```

Esperado:

```text
PROCESO_ALTO_CONSUMO | process_monitor
```

Mostrar PID, CPU y accion `kill_process`.

### 4.5 Directorio temporal: modulo 7

El fixture ya contiene:

```text
/tmp/hips_demo/suspicious.sh
```

Ejecutar:

```bash
sudo .venv/bin/python3 main.py
```

Esperado:

```text
ARCHIVO_TMP_SOSPECHOSO | tmp_monitor
```

### 4.6 DDoS: modulo 8

El fixture contiene 1001 solicitudes DNS desde `10.10.10.10`.

```bash
wc -l data/dns.log
sudo .venv/bin/python3 main.py
```

Esperado:

```text
DDOS_DETECTADO | ddos_detect
```

Mostrar la IP y accion `block_ip`.

### 4.7 Cron: modulo 9

Mostrar el archivo controlado:

```bash
cat /tmp/hips_demo/cron_test
sudo .venv/bin/python3 main.py
```

Esperado:

```text
CRON_SOSPECHOSO | cron_monitor
```

Mostrar la accion `quarantine_file`.

## 5. Modulos demostrados de forma controlada

### 5.1 Integridad de archivos: modulo 1

No modificar `/etc/passwd` ni `/etc/shadow` durante la entrega. Mostrar su
prueba automatizada:

```bash
python3 -m pytest \
  tests/test_all_modules.py::test_module_01_file_integrity_detects_modified_file \
  -v
```

La prueba crea un archivo temporal, calcula su SHA-256, lo modifica y verifica
`MODIFICACION_ARCHIVO`.

### 5.2 Cola de correo: modulo 5

Si no existe una cola real de Postfix, mostrar:

```bash
python3 -m pytest \
  tests/test_all_modules.py::test_module_05_mail_queue_detects_excess_messages \
  -v
```

La prueba simula la salida de `mailq` y verifica `MAIL_QUEUE_ALTA`.

Explicacion:

> La logica esta automatizada, pero no se generaron cien correos reales para
> evitar abusar del servicio SMTP durante la demostracion.

## 6. Evidencia final

Después de generar alarmas, mostrar:

### PostgreSQL

```bash
sudo -u postgres psql -d hips -c \
"SELECT id, tipo_alarma, modulo, severidad, detalle
 FROM alarmas ORDER BY id DESC LIMIT 10;"
```

### Acciones preventivas

```bash
sudo -u postgres psql -d hips -c \
"SELECT id, alarma_id, accion, resultado
 FROM acciones_prevencion ORDER BY id DESC LIMIT 10;"
```

### Logs formales

```bash
sudo tail -n 10 /var/log/hips/alarmas.log
sudo tail -n 10 /var/log/hips/prevencion.log
```

### Dashboard y email

- refrescar el dashboard;
- filtrar por modulo;
- mostrar al menos un email con alarma y prevencion.

## 7. Hardening

```bash
bash scripts/audit_rocky_hardening.sh
bash scripts/audit_postgres_hardening.sh
```

Explicar los controles cumplidos y los pendientes documentados.

## 8. Limpieza

Cerrar las sesiones SSH adicionales con:

```bash
exit
```

Detener procesos de prueba:

```bash
sudo pkill tcpdump 2>/dev/null || true
pkill yes 2>/dev/null || true
```

Eliminar solamente los fixtures creados para la demo:

```bash
bash scripts/demo_fixtures.sh cleanup
```

Restaurar los valores desde `/config` si fueron modificados.

## 9. Plan de contingencia

Si falla Internet:

- el dashboard, PostgreSQL y las detecciones locales siguen funcionando;
- mostrar el email recibido previamente como evidencia;
- mantener capturas de una ejecucion correcta.

Si falla una prueba real:

- ejecutar `python3 -m pytest tests/test_all_modules.py -v`;
- mostrar la entrada correspondiente en PostgreSQL y logs;
- explicar la fuente real que consume el modulo.

Si cambia la IP de Rocky:

```bash
ip a
```

Si el dashboard no abre:

```bash
curl http://127.0.0.1:8000/health
sudo firewall-cmd --list-all
```

## 10. Capturas recomendadas

Antes de la entrega guardar:

1. `28 passed` de la suite completa;
2. `10 passed` de los diez modulos;
3. dashboard con alarmas variadas;
4. tabla `alarmas`;
5. tabla `acciones_prevencion`;
6. `alarmas.log` y `prevencion.log`;
7. correo real recibido;
8. auditoria de Rocky Linux;
9. auditoria de PostgreSQL.
