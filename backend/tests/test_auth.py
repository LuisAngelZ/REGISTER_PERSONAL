"""
Tests para endpoints de autenticacion
"""


def test_check_sin_usuarios(client):
    """Sin usuarios registrados, auth_required debe ser False"""
    resp = client.get("/api/auth/check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth_required"] is False
    assert data["total_usuarios"] == 0


def test_registro_exitoso(client, usuario_data):
    """Registrar un usuario nuevo"""
    resp = client.post("/api/auth/registro", json=usuario_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["usuario"]["username"] == "testuser"
    assert data["usuario"]["rol"] == "admin"


def test_registro_duplicado(client, usuario_data):
    """No permitir username duplicado"""
    client.post("/api/auth/registro", json=usuario_data)
    resp = client.post("/api/auth/registro", json=usuario_data)
    assert resp.status_code == 400
    assert "ya existe" in resp.json()["detail"]


def test_registro_password_corto(client):
    """Rechazar password menor a 8 caracteres"""
    resp = client.post("/api/auth/registro", json={
        "username": "testuser",
        "password": "1234",
        "nombre": "Test",
    })
    assert resp.status_code == 422  # Validation error


def test_login_exitoso(client, usuario_data):
    """Login con credenciales correctas"""
    client.post("/api/auth/registro", json=usuario_data)
    resp = client.post("/api/auth/login", json={
        "username": usuario_data["username"],
        "password": usuario_data["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["usuario"]["username"] == "testuser"


def test_login_password_incorrecto(client, usuario_data):
    """Login con password incorrecto"""
    client.post("/api/auth/registro", json=usuario_data)
    resp = client.post("/api/auth/login", json={
        "username": usuario_data["username"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_usuario_inexistente(client):
    """Login con usuario que no existe"""
    resp = client.post("/api/auth/login", json={
        "username": "noexiste",
        "password": "password1234",
    })
    assert resp.status_code == 401


def test_check_con_usuarios(client, usuario_data):
    """Con usuarios registrados, auth_required debe ser True"""
    client.post("/api/auth/registro", json=usuario_data)
    resp = client.get("/api/auth/check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth_required"] is True
    assert data["total_usuarios"] == 1


def test_registro_username_invalido(client):
    """Rechazar username con caracteres especiales"""
    resp = client.post("/api/auth/registro", json={
        "username": "user<script>",
        "password": "password1234",
        "nombre": "Test",
    })
    assert resp.status_code == 422


def test_registro_password_largo(client):
    """Rechazar password mayor a 128 caracteres"""
    resp = client.post("/api/auth/registro", json={
        "username": "testuser",
        "password": "a" * 129,
        "nombre": "Test",
    })
    assert resp.status_code == 422


def test_rate_limit_login(client, usuario_data):
    """Bloquear IP despues de 5 intentos fallidos"""
    from app.routes.auth import _login_attempts
    _login_attempts.clear()

    for i in range(5):
        client.post("/api/auth/login", json={
            "username": "noexiste",
            "password": "wrongpass1234",
        })

    # El 6to intento debe ser rechazado con 429
    resp = client.post("/api/auth/login", json={
        "username": "noexiste",
        "password": "wrongpass1234",
    })
    assert resp.status_code == 429
    assert "Demasiados intentos" in resp.json()["detail"]
    _login_attempts.clear()
