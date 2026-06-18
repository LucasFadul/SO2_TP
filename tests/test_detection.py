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


def test_users_monitor_detects_nologin_user(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: "svc pts/0 2026-06-08 10:00 (192.168.1.20)\n",
    )

    alarms = run_users_check(
        allowed_users={"svc"},
        user_shells={"svc": "/sbin/nologin"},
    )

    assert alarms
    assert "shell no interactiva" in alarms[0]["detalle"]


def test_users_monitor_detects_multiple_sessions(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: (
            "lucas pts/0 2026-06-08 10:00 (192.168.1.20)\n"
            "lucas pts/1 2026-06-08 10:01 (192.168.1.20)\n"
            "lucas pts/2 2026-06-08 10:02 (192.168.1.20)\n"
        ),
    )

    alarms = run_users_check(allowed_users={"lucas"}, max_sessions=2)

    assert alarms
    assert "3 sesiones" in alarms[0]["detalle"]


def test_users_monitor_counts_local_tty_for_session_limit(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: (
            "lucas tty1 2026-06-08 09:59\n"
            "lucas pts/0 2026-06-08 10:00 (192.168.1.20)\n"
            "lucas pts/1 2026-06-08 10:01 (192.168.1.20)\n"
            "lucas pts/2 2026-06-08 10:02 (192.168.1.20)\n"
        ),
    )

    alarms = run_users_check(allowed_users={"lucas"}, max_sessions=2)

    assert alarms
    assert "4 sesiones" in alarms[0]["detalle"]
    assert "tty1" in alarms[0]["detalle"]
    assert "pts/2" in alarms[0]["detalle"]


def test_users_monitor_counts_unique_session_names(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: (
            "lucas tty1 2026-06-08 09:59\n"
            "lucas pts/0 2026-06-08 10:00 (192.168.1.20)\n"
            "lucas pts/0 2026-06-08 10:00 (192.168.1.20)\n"
            "lucas pts/1 2026-06-08 10:01 (192.168.1.20)\n"
        ),
    )

    alarms = run_users_check(allowed_users={"lucas"}, max_sessions=3)

    assert alarms == []


def test_users_monitor_ignores_inactive_sessions(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: (
            "lucas tty1 2026-06-08 09:59\n"
            "lucas pts/0 2026-06-08 10:00 (192.168.1.20)\n"
            "lucas pts/1 2026-06-08 10:01 (192.168.1.20)\n"
            "lucas pts/2 2026-06-08 10:02 (192.168.1.20)\n"
        ),
    )
    monkeypatch.setattr(
        "detection.users_monitor.session_is_active",
        lambda session: session != "pts/2",
    )

    alarms = run_users_check(
        allowed_users={"lucas"},
        max_sessions=3,
        validate_sessions=True,
    )

    assert alarms == []


def test_users_monitor_detects_external_ip(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: "lucas pts/0 2026-06-08 10:00 (203.0.113.5)\n",
    )

    alarms = run_users_check(
        allowed_users={"lucas"},
        allowed_networks={"192.168.0.0/16"},
    )

    assert alarms
    assert alarms[0]["ip_origen"] == "203.0.113.5"


def test_log_analyzer_detects_failed_logins():
    lines = [
        f"Jun 08 host sshd[123]: Failed password for admin from 10.0.0.25 port {2200 + i} ssh2"
        for i in range(6)
    ]

    alarms = analyze_lines(lines, failed_login_limit=5)

    assert alarms
    assert alarms[0]["ip_origen"] == "10.0.0.25"


def test_log_analyzer_detects_mail_anomaly():
    lines = [
        f"Jun 08 host postfix/smtpd[123]: warning: 10.0.0.30: SASL authentication failed"
        for _ in range(11)
    ]

    alarms = analyze_lines(lines, mail_anomaly_limit=10)

    assert alarms
    assert alarms[0]["tipo_alarma"] == "MAIL_ANOMALY"
    assert alarms[0]["ip_origen"] == "10.0.0.30"


def test_process_monitor_detects_high_cpu(monkeypatch):
    monkeypatch.setattr(
        "detection.process_monitor.get_process_table",
        lambda: "PID USER %CPU %MEM COMMAND\n123 root 95.0 1.0 stress\n",
    )

    alarms = run_process_check(cpu_limit=90.0, memory_limit=90.0)

    assert alarms
    assert alarms[0]["tipo_alarma"] == "PROCESO_ALTO_CONSUMO"
    assert alarms[0]["modulo"] == "process_monitor"


def test_process_monitor_ignores_whitelisted_process(monkeypatch):
    monkeypatch.setattr(
        "detection.process_monitor.get_process_table",
        lambda: "PID USER %CPU %MEM COMMAND\n123 postgres 95.0 1.0 postgres\n",
    )

    alarms = run_process_check(
        cpu_limit=90.0,
        memory_limit=90.0,
        process_whitelist={"postgres"},
    )

    assert alarms == []
