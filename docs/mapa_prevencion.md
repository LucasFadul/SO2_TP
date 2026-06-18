# Mapa de prevencion por modulo

Este documento resume que accion preventiva registra el HIPS cuando cada
modulo genera una alarma. En el entorno de prueba se usa
`HIPS_PREVENTION_DRY_RUN=true`, por lo que las acciones quedan registradas en
PostgreSQL sin aplicar cambios destructivos reales sobre el sistema.

| Modulo | Alarma principal | Accion preventiva |
| --- | --- | --- |
| Integridad de Archivos | `MODIFICACION_ARCHIVO` | `protect_file`: quita permisos de escritura a grupo/otros sobre el archivo afectado. |
| Usuarios Conectados | `USUARIO_SOSPECHOSO` | `lock_user`: bloquea la cuenta del usuario sospechoso. |
| Sniffers de Red | `SNIFFER_DETECTADO` | `kill_process` si detecta proceso sniffer; `disable_promisc` si detecta interfaz en modo promiscuo. |
| Analisis de Logs | `FAILED_LOGIN_MULTIPLE`, `SCANNER_HTTP`, `MAIL_ANOMALY` | `block_ip`: bloquea la IP origen con firewalld. |
| Cola de Correo | `MAIL_QUEUE_ALTA` | `stop_service`: detiene el servicio de correo configurado, por defecto `postfix`. |
| Procesos de Alto Consumo | `PROCESO_ALTO_CONSUMO` | `kill_process`: finaliza el proceso por PID. |
| Directorio Temporal | `ARCHIVO_TMP_SOSPECHOSO` | `quarantine_file`: mueve el archivo sospechoso a cuarentena. |
| Deteccion DDoS | `DDOS_DETECTADO` | `block_ip`: bloquea la IP origen con firewalld. |
| Tareas Cron | `CRON_SOSPECHOSO` | `quarantine_file`: mueve el archivo cron sospechoso a cuarentena. |
| Accesos Invalidos | `ACCESO_INVALIDO_REPETIDO`, `CREDENTIAL_STUFFING` | `block_ip`: bloquea la IP origen con firewalld. |

Las acciones se guardan en la tabla `acciones_prevencion` y se visualizan en
el dashboard junto con la alarma correspondiente.
