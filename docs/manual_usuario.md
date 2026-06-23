# Manual de usuario

## Dashboard

El dashboard muestra alarmas con:

- timestamp;
- tipo de alarma;
- IP de origen;
- modulo;
- accion tomada.

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
