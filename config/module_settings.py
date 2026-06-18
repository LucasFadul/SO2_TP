"""Definicion de parametros configurables por modulo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSetting:
    modulo: str
    parametro: str
    env_name: str
    default: str
    label: str
    input_type: str = "text"


SETTINGS: tuple[ModuleSetting, ...] = (
    ModuleSetting("file_integrity", "paths", "HIPS_FILE_INTEGRITY_PATHS", "/etc/passwd,/etc/shadow", "Archivos criticos"),
    ModuleSetting("users_monitor", "allowed_users", "HIPS_ALLOWED_USERS", "lucasfadul", "Usuarios permitidos"),
    ModuleSetting("users_monitor", "allowed_networks", "HIPS_ALLOWED_NETWORKS", "192.168.0.0/16,10.0.0.0/8,172.16.0.0/12", "Redes permitidas"),
    ModuleSetting("users_monitor", "max_sessions", "HIPS_USERS_MAX_SESSIONS", "2", "Sesiones maximas", "number"),
    ModuleSetting("sniffer_detect", "authorized", "HIPS_SNIFFER_AUTHORIZED", "false", "Sniffers autorizados", "checkbox"),
    ModuleSetting("sniffer_detect", "process_names", "HIPS_SNIFFER_PROCESS_NAMES", "tcpdump,wireshark,tshark,dumpcap,ethereal", "Procesos sniffer"),
    ModuleSetting("log_analyzer", "paths", "HIPS_LOG_ANALYZER_PATHS", "/var/log/secure,/var/log/httpd/access_log,/var/log/httpd/access.log,/var/log/nginx/access.log,/var/log/maillog", "Logs analizados"),
    ModuleSetting("log_analyzer", "ssh_journal_since", "HIPS_SSH_JOURNAL_SINCE", "10 minutes ago", "Ventana journal sshd"),
    ModuleSetting("log_analyzer", "failed_login_limit", "HIPS_FAILED_LOGIN_LIMIT", "5", "Limite fallos SSH", "number"),
    ModuleSetting("log_analyzer", "http_404_limit", "HIPS_HTTP_404_LIMIT", "30", "Limite eventos HTTP", "number"),
    ModuleSetting("log_analyzer", "mail_anomaly_limit", "HIPS_MAIL_ANOMALY_LIMIT", "10", "Limite anomalias mail", "number"),
    ModuleSetting("mail_queue", "queue_limit", "HIPS_MAIL_QUEUE_LIMIT", "100", "Limite cola de correo", "number"),
    ModuleSetting("process_monitor", "cpu_limit_percent", "HIPS_CPU_LIMIT_PERCENT", "90", "Limite CPU %", "number"),
    ModuleSetting("process_monitor", "memory_limit_percent", "HIPS_MEMORY_LIMIT_PERCENT", "90", "Limite RAM %", "number"),
    ModuleSetting("process_monitor", "process_whitelist", "HIPS_PROCESS_WHITELIST", "postgres,rsync,find,dnf,python,python3", "Whitelist procesos"),
    ModuleSetting("tmp_monitor", "tmp_dir", "HIPS_TMP_DIR", "/tmp", "Directorio temporal"),
    ModuleSetting("ddos_detect", "log_path", "HIPS_DDOS_LOG_PATH", "data/dns.log", "Log DNS"),
    ModuleSetting("ddos_detect", "request_limit", "HIPS_DDOS_REQUEST_LIMIT", "1000", "Limite solicitudes DNS", "number"),
    ModuleSetting("cron_monitor", "paths", "HIPS_CRON_PATHS", "/etc/crontab,/var/spool/cron/root", "Archivos cron"),
    ModuleSetting("access_monitor", "log_path", "HIPS_ACCESS_LOG_PATH", "/var/log/secure", "Log de accesos"),
    ModuleSetting("access_monitor", "failed_limit", "HIPS_ACCESS_FAILED_LIMIT", "5", "Limite accesos fallidos", "number"),
    ModuleSetting("access_monitor", "distinct_user_limit", "HIPS_ACCESS_DISTINCT_USER_LIMIT", "5", "Limite usuarios por IP", "number"),
)

SETTINGS_BY_KEY = {(setting.modulo, setting.parametro): setting for setting in SETTINGS}
MODULE_OPTIONS = tuple(dict.fromkeys(setting.modulo for setting in SETTINGS))

MODULE_LABELS = {
    "file_integrity": "Integridad de Archivos",
    "users_monitor": "Usuarios Conectados",
    "sniffer_detect": "Sniffers de Red",
    "log_analyzer": "Analisis de Logs",
    "mail_queue": "Cola de Correo",
    "process_monitor": "Procesos de Alto Consumo",
    "tmp_monitor": "Directorio Temporal",
    "ddos_detect": "Deteccion DDoS",
    "cron_monitor": "Tareas Cron",
    "access_monitor": "Accesos Invalidos",
}


def module_label(modulo: str) -> str:
    return MODULE_LABELS.get(modulo, modulo.replace("_", " ").title())
