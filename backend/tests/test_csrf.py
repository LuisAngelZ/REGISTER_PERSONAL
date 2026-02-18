"""
Tests para protección CSRF
"""
from fastapi.testclient import TestClient


def test_csrf_token_endpoint(client):
    """Obtener un CSRF token"""
    resp = client.get("/api/csrf-token")
    assert resp.status_code == 200
    data = resp.json()
    assert "csrf_token" in data
    assert len(data["csrf_token"]) == 64  # hex de 32 bytes


def test_post_sin_csrf_rechazado(client, personal_data):
    """POST sin CSRF token debe ser rechazado"""
    # Quitar CSRF token del header
    client.headers.pop("X-CSRF-Token", None)
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 403
    assert "CSRF" in resp.json()["detail"]


def test_post_con_csrf_invalido_rechazado(client, personal_data):
    """POST con CSRF token inválido debe ser rechazado"""
    client.headers["X-CSRF-Token"] = "token-falso-invalido"
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 403


def test_login_sin_csrf_permitido(client):
    """Login no requiere CSRF"""
    client.headers.pop("X-CSRF-Token", None)
    resp = client.post("/api/auth/login", json={
        "username": "test",
        "password": "password1234",
    })
    # 401 porque no existe el usuario, pero NO 403 (CSRF no aplica)
    assert resp.status_code == 401


def test_registro_sin_csrf_permitido(client):
    """Registro no requiere CSRF"""
    client.headers.pop("X-CSRF-Token", None)
    resp = client.post("/api/auth/registro", json={
        "username": "newuser",
        "password": "password1234",
        "nombre": "New User",
    })
    assert resp.status_code == 200
