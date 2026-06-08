# Manual de instalacion

## Requisitos

- Rocky Linux.
- Python 3.
- PostgreSQL.
- Git.

## Instalacion

```bash
git clone <URL_DEL_REPOSITORIO>
cd <REPOSITORIO>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Base de datos

```bash
createdb hips
psql -d hips -f db/schema.sql
```

Crear un usuario de aplicacion sin superusuario:

```sql
CREATE USER hips_app WITH PASSWORD 'cambiar';
GRANT CONNECT ON DATABASE hips TO hips_app;
```

## Ejecutar dashboard

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```
