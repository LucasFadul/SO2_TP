from alerts.mailer import build_alert_message, send_alert


def test_build_alert_message_includes_alarm_and_prevention(monkeypatch):
    monkeypatch.setenv("HIPS_ALERT_FROM", "hips@test.local")
    monkeypatch.setenv("HIPS_ALERT_TO", "admin@test.local")

    alarm = {
        "tipo_alarma": "FAILED_LOGIN_MULTIPLE",
        "modulo": "log_analyzer",
        "ip_origen": "192.168.64.1",
        "severidad": "alta",
        "detalle": "6 fallos de autenticacion",
    }
    prevention = {
        "accion": "block_ip",
        "dry_run": True,
        "ip": "192.168.64.1",
    }

    message = build_alert_message(alarm, prevention_result=prevention)
    body = message.get_content()

    assert message["From"] == "hips@test.local"
    assert message["To"] == "admin@test.local"
    assert message["Subject"] == "[HIPS ALERTA] FAILED_LOGIN_MULTIPLE"
    assert "Modulo: log_analyzer" in body
    assert "IP origen: 192.168.64.1" in body
    assert "Accion: block_ip" in body
    assert "Dry run: True" in body


def test_send_alert_dry_run_does_not_require_smtp(monkeypatch):
    monkeypatch.setenv("HIPS_ALERT_TO", "admin@test.local")

    result = send_alert(
        {"tipo_alarma": "TEST_ALERT", "modulo": "manual"},
        dry_run=True,
    )

    assert result["accion"] == "send_email"
    assert result["dry_run"] is True
    assert result["ok"] is True
    assert result["to"] == "admin@test.local"
