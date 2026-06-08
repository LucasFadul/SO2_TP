"""Aplicacion Flask del dashboard HIPS."""

from __future__ import annotations

from flask import Flask, render_template


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def dashboard():
        alarms = [
            {
                "timestamp": "pendiente",
                "tipo_alarma": "SIN_DATOS",
                "ip_origen": "N/A",
                "modulo": "dashboard",
                "accion_tomada": "N/A",
            }
        ]
        return render_template("dashboard.html", alarms=alarms)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

