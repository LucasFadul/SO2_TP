"""Aplicacion FastAPI del dashboard HIPS."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qs, quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from config.module_settings import MODULE_OPTIONS, SETTINGS, module_label
from db.models import (
    get_web_user,
    list_alarms,
    list_module_configs,
    set_module_config,
    update_web_user_last_login,
)
from web.auth import (
    SESSION_COOKIE_NAME,
    decode_session,
    encode_session,
    session_max_age,
    verify_password,
)


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["module_label"] = module_label
RANGE_OPTIONS = {
    "": "Todo",
    "hora": "Ultima hora",
    "dia": "Ultimo dia",
    "semana": "Ultima semana",
    "mes": "Ultimo mes",
}


def authenticated_username(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return decode_session(token) if token else None


def login_redirect(request: Request) -> RedirectResponse:
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"
    return RedirectResponse(f"/login?next={quote(path, safe='')}", status_code=303)


def safe_next_path(value: str) -> str:
    return value if value.startswith("/") and not value.startswith("//") else "/"


def create_app() -> FastAPI:
    app = FastAPI(title="hips_rocky", version="0.1.0")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, next: str = "/"):
        if authenticated_username(request):
            return RedirectResponse("/", status_code=303)
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": None,
                "next_path": safe_next_path(next),
            },
        )

    @app.post("/login", response_class=HTMLResponse)
    async def login(request: Request):
        raw_body = (await request.body()).decode()
        form = parse_qs(raw_body, keep_blank_values=True)
        username = str(form.get("username", [""])[0]).strip()
        password = str(form.get("password", [""])[0])
        next_path = safe_next_path(str(form.get("next", ["/"])[0]))

        try:
            user = get_web_user(username)
        except Exception:
            user = None
        valid_user = (
            user
            and bool(user.get("activo"))
            and verify_password(str(user.get("password_hash", "")), password)
        )
        if not valid_user:
            return templates.TemplateResponse(
                request,
                "login.html",
                {
                    "error": "Usuario o contraseña incorrectos.",
                    "next_path": next_path,
                },
                status_code=401,
            )

        update_web_user_last_login(int(user["id"]))
        response = RedirectResponse(next_path, status_code=303)
        response.set_cookie(
            SESSION_COOKIE_NAME,
            encode_session(username),
            max_age=session_max_age(),
            httponly=True,
            secure=os.getenv("HIPS_SESSION_HTTPS_ONLY", "false").lower()
            in {"1", "true", "yes", "on"},
            samesite="lax",
        )
        return response

    @app.post("/logout")
    def logout():
        response = RedirectResponse("/login", status_code=303)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, modulo: str = "", rango: str = ""):
        username = authenticated_username(request)
        if not username:
            return login_redirect(request)
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
                "module_options": [
                    {"value": module, "label": module_label(module)}
                    for module in MODULE_OPTIONS
                ],
                "range_options": RANGE_OPTIONS,
                "selected_module": selected_module,
                "selected_range": selected_range,
                "username": username,
            },
        )

    @app.get("/config", response_class=HTMLResponse)
    def config_page(request: Request, saved: str = ""):
        username = authenticated_username(request)
        if not username:
            return login_redirect(request)
        db_error = None
        config_values = {}
        try:
            config_values = list_module_configs()
        except Exception as exc:
            db_error = str(exc)

        settings_by_module: dict[str, list[dict]] = {}
        for setting in SETTINGS:
            settings_by_module.setdefault(setting.modulo, []).append(
                {
                    "setting": setting,
                    "value": config_values.get(
                        (setting.modulo, setting.parametro),
                        setting.default,
                    ),
                }
            )
        grouped_settings = [
            {
                "modulo": modulo,
                "label": module_label(modulo),
                "settings": items,
            }
            for modulo, items in settings_by_module.items()
        ]

        return templates.TemplateResponse(
            request,
            "config.html",
            {
                "db_error": db_error,
                "saved": saved == "1",
                "reset": saved == "reset",
                "grouped_settings": grouped_settings,
                "username": username,
            },
        )

    @app.post("/config")
    async def save_config(request: Request):
        if not authenticated_username(request):
            return login_redirect(request)
        raw_body = (await request.body()).decode()
        form = parse_qs(raw_body, keep_blank_values=True)
        for setting in SETTINGS:
            field_name = f"{setting.modulo}__{setting.parametro}"
            if setting.input_type == "checkbox":
                value = "true" if field_name in form else "false"
            else:
                value = str(form.get(field_name, [setting.default])[0]).strip()
            if not value:
                value = setting.default
            set_module_config(setting.modulo, setting.parametro, value)

        return RedirectResponse("/config?saved=1", status_code=303)

    @app.post("/config/reset")
    def reset_config(request: Request):
        if not authenticated_username(request):
            return login_redirect(request)
        for setting in SETTINGS:
            set_module_config(setting.modulo, setting.parametro, setting.default)

        return RedirectResponse("/config?saved=reset", status_code=303)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
