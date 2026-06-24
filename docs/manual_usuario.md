# Manual de usuario

El manual completo, preparado para entrega impresa y digital, se encuentra en:

```text
docs/manual_instalacion_y_uso.md
```

Las secciones siguientes se conservan como referencia rapida.

## Dashboard

El dashboard muestra alarmas con:

- timestamp;
- tipo de alarma;
- IP de origen;
- modulo;
- severidad;
- detalle;
- accion tomada;
- estado resuelta.

Tambien permite filtrar por modulo y rango de tiempo.

## Configuracion

La pantalla `/config` permite modificar parametros operativos de los modulos
desde la interfaz web. Esos valores se guardan en PostgreSQL, en la tabla
`configuracion_modulos`.

Desde esta pantalla tambien se puede restaurar la configuracion original del
proyecto con el boton `Restaurar`.

## Modulos de deteccion

El HIPS incluye 10 modulos de deteccion:

| Modulo | Que detecta | Alarma principal |
| --- | --- | --- |
| Integridad de Archivos | Cambios en archivos criticos comparando hashes | `MODIFICACION_ARCHIVO` |
| Usuarios Conectados | Usuarios inesperados, origenes no permitidos o muchas sesiones | `USUARIO_SOSPECHOSO` |
| Sniffers de Red | Procesos como tcpdump o interfaces en modo promiscuo | `SNIFFER_DETECTADO` |
| Analisis de Logs | Fallos de autenticacion, scanners HTTP y anomalias de mail | `FAILED_LOGIN_MULTIPLE` |
| Cola de Correo | Acumulacion anormal de mensajes en cola | `MAIL_QUEUE_ALTA` |
| Procesos de Alto Consumo | Procesos con CPU/RAM superior al umbral | `PROCESO_ALTO_CONSUMO` |
| Directorio Temporal | Scripts o ejecutables sospechosos en `/tmp` | `ARCHIVO_TMP_SOSPECHOSO` |
| Deteccion DDoS | Muchas solicitudes desde una misma IP en log DNS | `DDOS_DETECTADO` |
| Tareas Cron | Tareas programadas con comandos sospechosos | `CRON_SOSPECHOSO` |
| Accesos Invalidos | Accesos fallidos repetidos o credential stuffing | `ACCESO_INVALIDO_REPETIDO` |

La explicacion completa de cada modulo esta en:

```text
docs/modulos.md
```

## Tipos de alarma principales

- `MODIFICACION_ARCHIVO`
- `USUARIO_SOSPECHOSO`
- `SNIFFER_DETECTADO`
- `FAILED_LOGIN_MULTIPLE`
- `SCANNER_HTTP`
- `MAIL_QUEUE_ALTA`
- `PROCESO_ALTO_CONSUMO`
- `ARCHIVO_TMP_SOSPECHOSO`
- `DDOS_DETECTADO`
- `CRON_SOSPECHOSO`
- `ACCESO_INVALIDO_REPETIDO`
- `CREDENTIAL_STUFFING`

## Consultar logs del HIPS

El HIPS guarda sus logs formales en:

```text
/var/log/hips/
```

Los archivos principales son:

```text
/var/log/hips/alarmas.log
/var/log/hips/prevencion.log
```

`alarmas.log` registra las alarmas detectadas por los modulos. `prevencion.log` registra las acciones preventivas tomadas o simuladas.

Para ver las ultimas alarmas:

```bash
sudo tail -n 5 /var/log/hips/alarmas.log
```

Para ver las ultimas acciones preventivas:

```bash
sudo tail -n 5 /var/log/hips/prevencion.log
```

Para leer todo el archivo:

```bash
sudo cat /var/log/hips/alarmas.log
```

Para leerlo de forma paginada:

```bash
sudo less /var/log/hips/alarmas.log
```

Dentro de `less`, se sale con `q`.

Para monitorear alarmas en tiempo real:

```bash
sudo tail -f /var/log/hips/alarmas.log
```

Para migrar registros historicos al formato obligatorio sin eliminarlos:

```bash
cd ~/SO2_TP
sudo .venv/bin/python3 scripts/migrate_hips_logs.py
```

El script crea copias `.bak` y no modifica los archivos `.jsonl`.
