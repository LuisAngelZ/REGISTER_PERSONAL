from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Crear engine
# Si uses SQLite, no necesitas driver especial
if "sqlite" in settings.database_url:
    engine = create_engine(
        settings.database_url, 
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # Para PostgreSQL u otros
    engine = create_engine(settings.database_url, echo=False)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de BD en rutas"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
