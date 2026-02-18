"""
Fixtures compartidos para tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db import Base, get_db
from app.models.personal import Personal
from app.models.usuario import Usuario

# BD en memoria para tests
TEST_DATABASE_URL = "sqlite:///./test_registro.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Crea tablas frescas para cada test"""
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """TestClient con BD de prueba y CSRF deshabilitado"""
    from main import app, _csrf_tokens
    import time

    app.dependency_overrides[get_db] = override_get_db

    # Generar CSRF token válido para tests
    test_token = "test-csrf-token-for-testing"
    _csrf_tokens[test_token] = time.time()

    c = TestClient(app)
    c.headers["X-CSRF-Token"] = test_token
    yield c

    app.dependency_overrides.clear()
    _csrf_tokens.clear()


@pytest.fixture
def personal_data():
    """Datos base para crear personal"""
    return {
        "nombre": "Juan",
        "apellido": "Perez",
        "documento": "12345678",
        "puesto": "cajero",
        "turno": "mañana",
        "hora_entrada": "08:00",
        "hora_salida": "17:00",
        "duracion_contrato": "3_meses",
        "dia_libre": "domingo",
    }


@pytest.fixture
def usuario_data():
    """Datos base para crear usuario"""
    return {
        "username": "testuser",
        "password": "password1234",
        "nombre": "Test User",
        "rol": "admin",
    }
