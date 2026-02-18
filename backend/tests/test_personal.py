"""
Tests para endpoints CRUD de personal
"""


def test_crear_personal(client, personal_data):
    """Crear un nuevo registro de personal"""
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "Juan"
    assert data["apellido"] == "Perez"
    assert data["documento"] == "12345678"
    assert data["puesto"] == "cajero"
    assert data["activo"] is True


def test_crear_personal_documento_duplicado(client, personal_data):
    """No permitir documento duplicado"""
    client.post("/api/personal/", json=personal_data)
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 400
    assert "ya existe" in resp.json()["detail"]


def test_crear_personal_nombre_vacio(client, personal_data):
    """Rechazar nombre vacío"""
    personal_data["nombre"] = ""
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 422


def test_crear_personal_puesto_invalido(client, personal_data):
    """Rechazar puesto no válido"""
    personal_data["puesto"] = "astronauta"
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 422


def test_crear_personal_turno_invalido(client, personal_data):
    """Rechazar turno no válido"""
    personal_data["turno"] = "noche"
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 422


def test_crear_personal_hora_invalida(client, personal_data):
    """Rechazar formato de hora inválido"""
    personal_data["hora_entrada"] = "25:00"
    resp = client.post("/api/personal/", json=personal_data)
    assert resp.status_code == 422


def test_listar_personal(client, personal_data):
    """Listar personal activo"""
    client.post("/api/personal/", json=personal_data)
    resp = client.get("/api/personal/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Juan"


def test_obtener_por_id(client, personal_data):
    """Obtener personal por ID"""
    create_resp = client.post("/api/personal/", json=personal_data)
    pid = create_resp.json()["id"]
    resp = client.get(f"/api/personal/{pid}")
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Juan"


def test_obtener_por_id_no_existe(client):
    """404 si el ID no existe"""
    resp = client.get("/api/personal/999")
    assert resp.status_code == 404


def test_obtener_por_documento(client, personal_data):
    """Obtener personal por documento"""
    client.post("/api/personal/", json=personal_data)
    resp = client.get(f"/api/personal/documento/{personal_data['documento']}")
    assert resp.status_code == 200
    assert resp.json()["documento"] == "12345678"


def test_actualizar_personal(client, personal_data):
    """Actualizar datos de personal"""
    create_resp = client.post("/api/personal/", json=personal_data)
    pid = create_resp.json()["id"]
    resp = client.put(f"/api/personal/{pid}", json={"nombre": "Carlos"})
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Carlos"


def test_eliminar_personal(client, personal_data):
    """Soft delete de personal"""
    create_resp = client.post("/api/personal/", json=personal_data)
    pid = create_resp.json()["id"]
    resp = client.delete(f"/api/personal/{pid}")
    assert resp.status_code == 200
    # Verificar que ya no aparece en listado de activos
    lista = client.get("/api/personal/").json()
    assert len(lista) == 0


def test_estadisticas(client, personal_data):
    """Obtener estadísticas de personal"""
    client.post("/api/personal/", json=personal_data)
    resp = client.get("/api/personal/stats/total")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["activos"] == 1
    assert data["inactivos"] == 0


def test_dashboard(client, personal_data):
    """Obtener dashboard stats"""
    client.post("/api/personal/", json=personal_data)
    resp = client.get("/api/personal/stats/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_personal"] == 1
    assert "por_puesto" in data
    assert "top_retrasos" in data
    assert "top_faltas" in data
