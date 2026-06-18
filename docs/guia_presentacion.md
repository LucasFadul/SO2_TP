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

### log_analyzer

Analiza logs del sistema, principalmente `/var/log/secure`, para detectar patrones de acceso fallido.

Ejemplo de alarma:

```text
FAILED_LOGIN_MULTIPLE
```

Accion preventiva registrada:

```text
block_ip
```

### users_monitor

Consulta usuarios conectados con el comando `who`.

Detecta usuarios inesperados, conexiones desde redes no permitidas o demasiadas sesiones simultaneas.

Ejemplo de alarma:

```text
USUARIO_SOSPECHOSO
```

Accion preventiva registrada:

```text
lock_user
```

### process_monitor

Consulta procesos del sistema con `ps`.

Si un proceso supera el umbral de CPU o memoria y no esta en whitelist, genera una alarma.

Ejemplo de alarma:

```text
PROCESO_ALTO_CONSUMO
```

Accion preventiva registrada:

```text
kill_process
```

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

La configuracion principal esta en `.env`.

Ejemplos:

```env
HIPS_CPU_LIMIT_PERCENT=90
HIPS_MEMORY_LIMIT_PERCENT=90
HIPS_USERS_MAX_SESSIONS=3
HIPS_FAILED_LOGIN_LIMIT=5
HIPS_PREVENTION_DRY_RUN=true
```

Frase para explicar:

> Las contrasenas reales no se suben al repositorio. El repositorio incluye `.env.example` como plantilla.

## 12. Limitaciones

Puntos honestos para mencionar:

- Esta version implementa funcionalmente tres modulos principales.
- Otros modulos quedan preparados en la estructura del proyecto, pero no todos estan integrados.
- Las acciones preventivas estan en `dry_run`.
- La configuracion actualmente esta en `.env`; la especificacion pide configuracion desde web como mejora pendiente.
- Falta integrar envio real de emails al administrador.
- Falta registrar logs formales en `/var/log/hips/alarmas.log` y `/var/log/hips/prevencion.log`.

## 13. Cierre

Frase final:

> En resumen, el sistema detecta eventos reales en Rocky Linux, los guarda en PostgreSQL, registra acciones preventivas y los muestra en un dashboard web. La demo valida deteccion por logs, usuarios conectados y procesos de alto consumo.

## Orden recomendado para la demo

1. Mostrar estructura del repositorio.
2. Mostrar `.env.example`.
3. Mostrar tablas de PostgreSQL con `\dt`.
4. Levantar o mostrar el dashboard.
5. Ejecutar una prueba real.
6. Refrescar el dashboard.
7. Mostrar hardening.
8. Explicar limitaciones y mejoras futuras.

