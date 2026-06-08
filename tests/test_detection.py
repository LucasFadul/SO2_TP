from detection.access_monitor import analyze_access_lines
from detection.log_analyzer import analyze_lines
from detection.sniffer_detect import detect_promiscuous_interfaces


def test_access_monitor_detects_repeated_failed_logins():
    lines = [
        f"Jun 08 host sshd[123]: Failed password for root from 10.0.0.8 port {2200 + i} ssh2"
        for i in range(6)
    ]

    alarms = analyze_access_lines(lines, failed_limit=5)

    assert alarms
    assert alarms[0]["tipo_alarma"] == "ACCESO_INVALIDO_REPETIDO"


def test_log_analyzer_detects_failed_logins():
    lines = [
        f"Jun 08 host sshd[123]: Failed password for admin from 10.0.0.25 port {2200 + i} ssh2"
        for i in range(6)
    ]

    alarms = analyze_lines(lines, failed_login_limit=5)

    assert alarms
    assert alarms[0]["ip_origen"] == "10.0.0.25"


def test_sniffer_detects_promiscuous_interface():
    output = "2: eth0: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000"

    interfaces = detect_promiscuous_interfaces(output)

    assert interfaces == ["eth0"]

