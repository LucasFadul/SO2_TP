from alerts.logger import write_alarm, write_prevention


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
    assert "FAILED_LOGIN_MULTIPLE :: 192.168.64.1" in log_path.read_text()
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
