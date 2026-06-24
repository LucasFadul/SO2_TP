import asyncio
from dataclasses import dataclass
from urllib.parse import urlencode

from web.app import create_app
from web.auth import decode_session, encode_session, hash_password, verify_password


@dataclass
class AsgiResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8")


def request(app, method, path, data=None, headers=None):
    body = urlencode(data or {}).encode("utf-8")
    request_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    if data is not None:
        request_headers.append(
            (b"content-type", b"application/x-www-form-urlencoded")
        )
        request_headers.append((b"content-length", str(len(body)).encode("ascii")))

    messages = []
    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": request_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "app": app,
    }
    asyncio.run(app(scope, receive, send))

    start = next(message for message in messages if message["type"] == "http.response.start")
    response_headers = {
        name.decode("latin-1"): value.decode("latin-1")
        for name, value in start["headers"]
    }
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return AsgiResponse(start["status"], response_headers, response_body)


def test_password_hash_is_not_plain_text():
    password = "ClaveSegura123"
    password_hash = hash_password(password)

    assert password not in password_hash
    assert verify_password(password_hash, password)
    assert not verify_password(password_hash, "incorrecta")


def test_signed_session_rejects_tampering_and_expiration(monkeypatch):
    monkeypatch.setenv("HIPS_SESSION_SECRET", "test-secret-for-signed-cookies")
    monkeypatch.setenv("HIPS_SESSION_MAX_AGE", "60")
    token = encode_session("admin", now=1000)

    assert decode_session(token, now=1050) == "admin"
    assert decode_session(f"{token}alterado", now=1050) is None
    assert decode_session(token, now=1060) is None


def test_dashboard_redirects_to_login_without_session(monkeypatch):
    monkeypatch.setenv("HIPS_SESSION_SECRET", "test-secret-for-signed-cookies")

    response = request(create_app(), "GET", "/")

    assert response.status_code == 303
    assert response.headers["location"].startswith("/login?next=")


def test_login_allows_access_and_logout(monkeypatch):
    monkeypatch.setenv("HIPS_SESSION_SECRET", "test-secret-for-signed-cookies")
    password_hash = hash_password("ClaveSegura123")
    monkeypatch.setattr(
        "web.app.get_web_user",
        lambda username: {
            "id": 1,
            "username": username,
            "password_hash": password_hash,
            "rol": "administrador",
            "activo": True,
        }
        if username == "admin"
        else None,
    )
    monkeypatch.setattr("web.app.update_web_user_last_login", lambda user_id: None)
    monkeypatch.setattr("web.app.list_alarms", lambda **kwargs: [])
    app = create_app()

    login_response = request(
        app,
        "POST",
        "/login",
        data={
            "username": "admin",
            "password": "ClaveSegura123",
            "next": "/",
        },
    )

    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/"
    assert "hips_session=" in login_response.headers["set-cookie"]

    cookie = login_response.headers["set-cookie"].split(";", 1)[0]
    dashboard_response = request(
        app,
        "GET",
        "/",
        headers={"cookie": cookie},
    )
    assert dashboard_response.status_code == 200
    assert "admin" in dashboard_response.text

    logout_response = request(
        app,
        "POST",
        "/logout",
        headers={"cookie": cookie},
    )
    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"


def test_login_rejects_invalid_password(monkeypatch):
    monkeypatch.setenv("HIPS_SESSION_SECRET", "test-secret-for-signed-cookies")
    password_hash = hash_password("ClaveSegura123")
    monkeypatch.setattr(
        "web.app.get_web_user",
        lambda username: {
            "id": 1,
            "username": username,
            "password_hash": password_hash,
            "rol": "administrador",
            "activo": True,
        },
    )

    response = request(
        create_app(),
        "POST",
        "/login",
        data={"username": "admin", "password": "incorrecta", "next": "/"},
    )

    assert response.status_code == 401
    assert "Usuario o contraseña incorrectos" in response.text
