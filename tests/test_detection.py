from detection.log_analyzer import analyze_lines
from detection.process_monitor import run_check as run_process_check
from detection.users_monitor import run_check as run_users_check


def test_users_monitor_detects_unexpected_user(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: "intruso pts/0 2026-06-08 10:00 (10.0.0.9)\n",
    )

    alarms = run_users_check(allowed_users={"lucas"})

    assert alarms
    assert alarms[0]["tipo_alarma"] == "USUARIO_SOSPECHOSO"
    assert alarms[0]["modulo"] == "users_monitor"


def test_log_analyzer_detects_failed_logins():
    lines = [
        f"Jun 08 host sshd[123]: Failed password for admin from 10.0.0.25 port {2200 + i} ssh2"
        for i in range(6)
    ]

    alarms = analyze_lines(lines, failed_login_limit=5)

    assert alarms
    assert alarms[0]["ip_origen"] == "10.0.0.25"


def test_process_monitor_detects_high_cpu(monkeypatch):
    monkeypatch.setattr(
        "detection.process_monitor.get_process_table",
        lambda: "PID USER %CPU %MEM COMMAND\n123 root 95.0 1.0 stress\n",
    )

    alarms = run_process_check(cpu_limit=90.0, memory_limit=90.0)

    assert alarms
    assert alarms[0]["tipo_alarma"] == "PROCESO_ALTO_CONSUMO"
    assert alarms[0]["modulo"] == "process_monitor"
