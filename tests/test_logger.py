from alerts.logger import format_alarm_line, write_alarm, write_prevention


def test_alarm_line_uses_required_format():
    alarm = {
        "timestamp": "2026-05-29T18:25:09+00:00",
        "tipo_alarma": "FAILED_LOGIN_MULTIPLE",
        "ip_origen": "10.0.0.25",
        "modulo": "log_analyzer",
        "severidad": "alta",
        "detalle": "6 fallos de autenticacion",
    }

    assert format_alarm_line(alarm) == "29/05/2026 :: FAILED_LOGIN_MULTIPLE :: 10.0.0.25"


def test_alarm_line_uses_na_without_source_ip():
    alarm = {
        "timestamp": "2026-05-29T18:25:09+00:00",
        "tipo_alarma": "SNIFFER_DETECTADO",
        "ip_origen": None,
    }

    assert format_alarm_line(alarm) == "29/05/2026 :: SNIFFER_DETECTADO :: N/A"


def test_write_alarm_creates_text_and_json_logs(tmp_path):
    alarm = {
        "tipo_alarma": "FAILED_LOGIN_MULTIPLE",
        "ip_origen": "192.168.64.1",
        "modulo": "log_analyzer",
        "severidad": "alta",
        "detalle": "6 fallos de autenticacion",
    }

    log_path = write_alarm(alarm, log_dir=str(tmp_path))

    assert log_path.name == "alarmas.log"
    text = log_path.read_text()
    assert "FAILED_LOGIN_MULTIPLE :: 192.168.64.1" in text
    assert "log_analyzer" not in text
    assert "6 fallos de autenticacion" not in text
    assert (tmp_path / "alarmas.jsonl").exists()


def test_write_prevention_creates_text_and_json_logs(tmp_path):
    alarm = {
        "tipo_alarma": "PROCESO_ALTO_CONSUMO",
        "ip_origen": None,
        "modulo": "process_monitor",
        "severidad": "media",
        "detalle": "PID 123 CPU 99%",
    }
    prevention_result = {
        "accion": "kill_process",
        "pid": 123,
        "dry_run": True,
        "ok": True,
    }

    log_path = write_prevention(alarm, prevention_result, log_dir=str(tmp_path))

    assert log_path.name == "prevencion.log"
    text = log_path.read_text()
    assert "PROCESO_ALTO_CONSUMO :: process_monitor :: kill_process" in text
    assert "dry_run=True" in text
    assert (tmp_path / "prevencion.jsonl").exists()
