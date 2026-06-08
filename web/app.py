"""Aplicacion FastAPI del dashboard HIPS."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(title="sentinel_hips", version="0.1.0")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        alarms = [
            {
                "timestamp": "pendiente",
                "tipo_alarma": "SIN_DATOS",
                "ip_origen": "N/A",
                "modulo": "dashboard",
                "accion_tomada": "N/A",
            }
        ]
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"alarms": alarms},
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
