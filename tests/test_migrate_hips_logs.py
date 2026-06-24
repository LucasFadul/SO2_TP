from scripts.migrate_hips_logs import (
    migrate_alarm_line,
    migrate_prevention_line,
)


def test_migrate_old_alarm_line_to_required_format():
    old_line = (
        "2026-06-22T18:25:09.155844+00:00 :: PROCESO_ALTO_CONSUMO :: "
        "N/A :: process_monitor :: media :: PID 1912"
    )

    assert (
        migrate_alarm_line(old_line)
        == "22/06/2026 :: PROCESO_ALTO_CONSUMO :: N/A"
    )


def test_migrate_alarm_line_is_idempotent():
    line = "29/05/2026 :: FAILED_LOGIN_MULTIPLE :: 10.0.0.25"

    assert migrate_alarm_line(line) == line


def test_migrate_prevention_keeps_action_details():
    old_line = (
        "2026-06-22T18:25:09.162320+00:00 :: PROCESO_ALTO_CONSUMO :: "
        "process_monitor :: kill_process :: dry_run=True :: ok=True"
    )

    assert migrate_prevention_line(old_line) == (
        "22/06/2026 :: PROCESO_ALTO_CONSUMO :: process_monitor :: "
        "kill_process :: dry_run=True :: ok=True"
    )
