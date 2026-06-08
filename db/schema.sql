CREATE TABLE IF NOT EXISTS alarmas (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    tipo_alarma VARCHAR(80) NOT NULL,
    ip_origen INET,
    modulo VARCHAR(80) NOT NULL,
    severidad VARCHAR(20) NOT NULL DEFAULT 'media',
    detalle TEXT NOT NULL DEFAULT '',
    resuelta BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_alarmas_timestamp ON alarmas (timestamp);
CREATE INDEX IF NOT EXISTS idx_alarmas_tipo_alarma ON alarmas (tipo_alarma);
CREATE INDEX IF NOT EXISTS idx_alarmas_modulo ON alarmas (modulo);

CREATE TABLE IF NOT EXISTS acciones_prevencion (
    id BIGSERIAL PRIMARY KEY,
    alarma_id BIGINT REFERENCES alarmas(id),
    accion VARCHAR(120) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    resultado TEXT NOT NULL DEFAULT '',
    ejecutada_por VARCHAR(80) NOT NULL DEFAULT 'sistema'
);

CREATE TABLE IF NOT EXISTS usuarios_web (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol VARCHAR(40) NOT NULL DEFAULT 'operador',
    activo BOOLEAN NOT NULL DEFAULT true,
    ultimo_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS configuracion_modulos (
    id BIGSERIAL PRIMARY KEY,
    modulo VARCHAR(80) NOT NULL,
    parametro VARCHAR(120) NOT NULL,
    valor TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (modulo, parametro)
);

CREATE TABLE IF NOT EXISTS eventos_sistema (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    modulo VARCHAR(80) NOT NULL,
    fuente TEXT NOT NULL,
    evento_raw TEXT NOT NULL,
    procesado BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS hosts_bloqueados (
    id BIGSERIAL PRIMARY KEY,
    ip INET NOT NULL,
    motivo TEXT NOT NULL,
    bloqueado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en TIMESTAMPTZ,
    activo BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_hosts_bloqueados_ip ON hosts_bloqueados (ip);

