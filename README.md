# sentinel_hips

Proyecto HIPS para Sistemas Operativos.

El objetivo es detectar eventos sospechosos en Rocky Linux, registrar alarmas, ejecutar acciones preventivas controladas y mostrar el estado en una interfaz web.

## Estructura

```text
detection/      Modulos de deteccion i-x
prevention/     Acciones preventivas reutilizables
alerts/         Logger central y email
web/            Aplicacion Flask y dashboard
db/             Esquema PostgreSQL y conexion
config/         Configuracion cifrada o plantillas
tests/          Pruebas automatizadas
docs/           Manuales y documentacion
```

## Puesta en marcha local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app web.app run --debug
```

## Flujo esperado

```text
evento -> detector -> alarma -> /var/log/hips/alarmas.log -> PostgreSQL -> dashboard -> prevencion
```

## Prioridad de desarrollo

1. Logger central y base de datos.
2. Modulo iv `log_analyzer`.
3. Modulo x `access_monitor`.
4. Modulo iii `sniffer_detect`.
5. Prevencion con `firewalld` y control de procesos.
6. Dashboard y alertas por email.
7. Modulos restantes, tests y manuales.

## Seguridad

No subir `.env` ni archivos `*.enc` reales. El repositorio incluye solo ejemplos sin secretos.

