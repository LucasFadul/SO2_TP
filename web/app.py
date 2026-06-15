"""Aplicacion FastAPI del dashboard HIPS."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from db.models import list_alarms


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(title="hips_rocky", version="0.1.0")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        db_error = None
        try:
            alarms = list_alarms()
        except Exception as exc:
            alarms = []
            db_error = str(exc)

        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"alarms": alarms, "db_error": db_error},
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
