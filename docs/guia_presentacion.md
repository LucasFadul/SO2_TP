# Guia de presentacion del HIPS

Esta guia sirve como guion para explicar y demostrar el proyecto durante la entrega.

## 1. Introduccion

Este proyecto es un HIPS, es decir, un Host-based Intrusion Prevention System.

La idea principal es monitorear una maquina Rocky Linux desde adentro, detectar comportamientos sospechosos y registrar una accion preventiva cuando corresponde.

El sistema esta hecho en Python, usa PostgreSQL para guardar alarmas y FastAPI para mostrar un dashboard web.

## 2. Arquitectura general

Flujo general del sistema:

```text
Rocky Linux
  -> Modulos de deteccion en Python
  -> PostgreSQL
  -> Dashboard FastAPI
  -> Acciones preventivas en dry-run
```

Explicacion:

Los modulos revisan usuarios conectados, logs del sistema y procesos. Si encuentran algo anomalo, insertan una alarma en PostgreSQL. El dashboard consulta esa base y muestra las alarmas.

## 3. Modulos implementados

El sistema cubre los 10 modulos pedidos por el TP:

| Modulo | Que detecta | Accion preventiva |
| --- | --- | --- |
| Integridad de Archivos | Cambios en archivos criticos | `protect_file` |
| Usuarios Conectados | Usuarios no esperados, origenes raros o muchas sesiones | `lock_user` |
| Sniffers de Red | `tcpdump`, Wireshark o modo promiscuo | `kill_process` / `disable_promisc` |
| Analisis de Logs | SSH fallido, scanners HTTP y anomalias de mail | `block_ip` |
| Cola de Correo | Cola de mail demasiado grande | `stop_service` |
| Procesos de Alto Consumo | CPU/RAM por encima del umbral | `kill_process` |
| Directorio Temporal | Scripts o ejecutables sospechosos en `/tmp` | `quarantine_file` |
| Deteccion DDoS | Muchas solicitudes DNS desde una IP | `block_ip` |
| Tareas Cron | Cron con comandos sospechosos | `quarantine_file` |
| Accesos Invalidos | Intentos repetidos o credential stuffing | `block_ip` |

Frase para explicar:

> Cada modulo mira una parte distinta del host. Cuando detecta una condicion anomala, genera una alarma, la guarda en PostgreSQL, registra la accion preventiva y envia una notificacion por email.

Para la demo en vivo conviene mostrar los casos mas faciles de reproducir:

```text
log_analyzer / access_monitor -> SSH fallido
users_monitor                 -> sesiones SSH simultaneas
sniffer_detect                -> tcpdump activo
process_monitor               -> proceso yes con CPU alta
tmp_monitor                   -> script en /tmp
```

La explicacion completa de cada modulo esta en `docs/modulos.md`.

## 4. Base de datos

PostgreSQL guarda las alarmas y las acciones preventivas.

Comando para mostrar las tablas:

```bash
sudo -u postgres psql -d hips -c "\dt"
```

Tabla principal:

```text
alarmas
```

Tabla de acciones:

```text
acciones_prevencion
```

Comando para ver ultimas alarmas:

```bash
sudo -u postgres psql -d hips -c "SELECT id, tipo_alarma, modulo, severidad, detalle FROM alarmas ORDER BY id DESC LIMIT 5;"
```

Frase para explicar:

> La tabla `alarmas` guarda cada evento detectado. La tabla `acciones_prevencion` registra que accion tomaria el sistema frente a esa alarma.

## 5. Dashboard

Abrir desde la Mac:

```text
http://<IP_ROCKY>:8000
```

El dashboard muestra:

- ID de la alarma.
- Timestamp.
- Tipo de alarma.
- IP origen, si existe.
- Modulo que la genero.
- Severidad.
- Detalle.
- Accion tomada.
- Estado resuelta.

Frase para explicar:

> El dashboard no detecta por si solo. Visualiza las alarmas que los modulos guardaron en PostgreSQL.

## 6. Prueba 1: SSH fallido

Desde la Mac:

```bash
ssh usuario_falso@<IP_ROCKY>
```

Ingresar una contrasena incorrecta varias veces.

En Rocky:

```bash
cd ~/SO2_TP
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
FAILED_LOGIN_MULTIPLE | log_analyzer
```

Explicacion:

> El modulo detecta varios intentos fallidos desde una IP y registra como accion preventiva `block_ip`.

## 7. Prueba 2: usuario sospechoso

Abrir varias sesiones SSH validas desde la Mac:

```bash
ssh lucasfadul@<IP_ROCKY>
```

En Rocky:

```bash
who
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
USUARIO_SOSPECHOSO | users_monitor
```

Explicacion:

> El sistema detecta mas sesiones simultaneas que el umbral configurado.

## 8. Prueba 3: proceso de alto consumo

En Rocky:

```bash
yes > /dev/null &
sudo .venv/bin/python3 main.py
```

Resultado esperado:

```text
PROCESO_ALTO_CONSUMO | process_monitor
```

Luego finalizar el proceso de prueba:

```bash
pkill yes
```

Explicacion:

> El proceso `yes` genera consumo alto de CPU. El HIPS lo detecta y registra que la accion preventiva seria `kill_process`.

## 9. Dry-run

Las acciones preventivas estan configuradas en modo `dry_run`.

Esto significa que el sistema registra que accion tomaria, pero no bloquea realmente IPs, usuarios ni procesos durante la demo.

Frase para explicar:

> Use `dry_run=true` para demostrar la respuesta del sistema sin arriesgarme a bloquear la VM o cortar servicios durante la presentacion.

## 10. Hardening

Scripts de auditoria:

```bash
bash scripts/audit_rocky_hardening.sh
bash scripts/audit_postgres_hardening.sh
```

Rocky Linux:

- SELinux en modo enforcing.
- firewalld activo.
- SSH root deshabilitado.
- auditd activo.
- reglas auditd para archivos criticos.

PostgreSQL:

- usuario de aplicacion `hips_app`.
- permisos limitados.
- autenticacion segura.
- `listen_addresses=localhost`.
- logs de conexion/desconexion.

## 11. Configuracion

La configuracion operativa de los modulos esta en PostgreSQL y se modifica
desde `/config`.

La configuracion de infraestructura queda en `.env`, por ejemplo datos de base
de datos, modo `dry_run` y SMTP.

Ejemplos:

```env
HIPS_PREVENTION_DRY_RUN=true
HIPS_EMAIL_DRY_RUN=false
HIPS_SMTP_HOST=smtp.gmail.com
```

Frase para explicar:

> Los parametros de deteccion se pueden cambiar desde el dashboard. Las credenciales reales quedan fuera del repositorio y se cargan desde `.env`.

## 12. Limitaciones

Puntos honestos para mencionar:

- Las acciones preventivas pueden ejecutarse en `dry_run` para evitar bloquear la VM durante la demo.
- Algunos modulos requieren escenario preparado para demostrarse, por ejemplo cola de correo, log DNS o baseline de integridad.
- El dashboard no ejecuta deteccion por si solo: muestra alarmas ya registradas por `main.py`.
- Los logs formales se guardan a partir de la integracion del logger central; alarmas antiguas pueden existir solo en PostgreSQL.

## 13. Cierre

Frase final:

> En resumen, el sistema detecta eventos reales en Rocky Linux, los guarda en PostgreSQL, registra acciones preventivas y los muestra en un dashboard web. La demo valida deteccion por logs, usuarios conectados y procesos de alto consumo.

## Orden recomendado para la demo

La secuencia operativa completa y los comandos de contingencia estan en:

```text
docs/escenario_entrega.md
```

Orden resumido:

1. Ejecutar el preflight.
2. Mostrar `10 passed` de los modulos.
3. Mostrar tablas de PostgreSQL.
4. Levantar o mostrar el dashboard.
5. Ejecutar las pruebas reales preparadas.
6. Mostrar logs, email y acciones preventivas.
7. Mostrar hardening.
8. Explicar limitaciones y mejoras futuras.
