# Pruebas

## Pruebas automaticas

Ejecutar:

```bash
python3 -m pytest -q
```

Resultado esperado:

```text
3 passed
```

## Prueba manual de FastAPI

Levantar el dashboard:

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Verificar healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

Resultado esperado:

```json
{"status":"ok"}
```

## Prueba manual Python -> PostgreSQL

Requisitos:

- PostgreSQL instalado y activo.
- Base `hips` creada.
- Usuario `hips_app` creado.
- Archivo `.env` configurado con `HIPS_DB_PASSWORD`.

Ejecutar:

```bash
python3 scripts/test_db_insert.py
```

Resultado esperado:

```text
Insercion Python -> PostgreSQL OK
(..., 'TEST_PYTHON', 'manual', 'baja', 'insert desde scripts/test_db_insert.py')
```

## Prueba real de accesos SSH invalidos

Desde la Mac generar varios intentos fallidos contra Rocky:

```bash
ssh usuario_falso@<IP_ROCKY>
```

Ingresar una contrasena incorrecta varias veces.

En Rocky ejecutar:

```bash
python3 scripts/run_real_ssh_monitor.py
```

Resultado esperado:

```text
Lineas sshd leidas: ...
Alarmas detectadas: 1
Insertada: ACCESO_INVALIDO_REPETIDO | <IP_MAC> | access_monitor | ...
```

Luego refrescar el dashboard y verificar que la alarma aparezca en la tabla `alarmas`.
