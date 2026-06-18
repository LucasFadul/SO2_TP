"""Aplicacion FastAPI del dashboard HIPS."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from config.module_settings import MODULE_OPTIONS, SETTINGS
from db.models import list_alarms, list_module_configs, set_module_config


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
RANGE_OPTIONS = {
    "": "Todo",
    "hora": "Ultima hora",
    "dia": "Ultimo dia",
    "semana": "Ultima semana",
    "mes": "Ultimo mes",
}


def create_app() -> FastAPI:
    app = FastAPI(title="hips_rocky", version="0.1.0")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, modulo: str = "", rango: str = ""):
        db_error = None
        selected_module = modulo if modulo in MODULE_OPTIONS else ""
        selected_range = rango if rango in RANGE_OPTIONS else ""
        try:
            alarms = list_alarms(
                modulo=selected_module or None,
                rango=selected_range or None,
            )
        except Exception as exc:
            alarms = []
            db_error = str(exc)

        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "alarms": alarms,
                "db_error": db_error,
                "module_options": MODULE_OPTIONS,
                "range_options": RANGE_OPTIONS,
                "selected_module": selected_module,
                "selected_range": selected_range,
            },
        )

    @app.get("/config", response_class=HTMLResponse)
    def config_page(request: Request, saved: str = ""):
        db_error = None
        config_values = {}
        try:
            config_values = list_module_configs()
        except Exception as exc:
            db_error = str(exc)

        grouped_settings: dict[str, list[dict]] = {}
        for setting in SETTINGS:
            grouped_settings.setdefault(setting.modulo, []).append(
                {
                    "setting": setting,
                    "value": config_values.get(
                        (setting.modulo, setting.parametro),
                        setting.default,
                    ),
                }
            )

        return templates.TemplateResponse(
            request,
            "config.html",
            {
                "db_error": db_error,
                "saved": saved == "1",
                "grouped_settings": grouped_settings,
            },
        )

    @app.post("/config")
    async def save_config(request: Request):
        form = await request.form()
        for setting in SETTINGS:
            field_name = f"{setting.modulo}__{setting.parametro}"
            if setting.input_type == "checkbox":
                value = "true" if field_name in form else "false"
            else:
                value = str(form.get(field_name, setting.default)).strip()
            if not value:
                value = setting.default
            set_module_config(setting.modulo, setting.parametro, value)

        return RedirectResponse("/config?saved=1", status_code=303)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
