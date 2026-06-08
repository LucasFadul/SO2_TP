"""Acciones de firewall usando firewalld."""

from __future__ import annotations

import subprocess
from typing import List


def build_block_command(ip: str) -> List[str]:
    return ["firewall-cmd", "--add-rich-rule", f"rule family='ipv4' source address='{ip}' drop"]


def block_ip(ip: str, dry_run: bool = True) -> dict:
    command = build_block_command(ip)
    if dry_run:
        return {"accion": "block_ip", "ip": ip, "dry_run": True, "command": command, "ok": True}

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "accion": "block_ip",
        "ip": ip,
        "dry_run": False,
        "command": command,
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def unblock_ip(ip: str, dry_run: bool = True) -> dict:
    command = ["firewall-cmd", "--remove-rich-rule", f"rule family='ipv4' source address='{ip}' drop"]
    if dry_run:
        return {"accion": "unblock_ip", "ip": ip, "dry_run": True, "command": command, "ok": True}

    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "accion": "unblock_ip",
        "ip": ip,
        "dry_run": False,
        "command": command,
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

