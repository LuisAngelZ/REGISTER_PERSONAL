from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)

# Crear engine con reintentos para esperar a que PostgreSQL inicie
def _crear_engine(max_retries=5, retry_delay=3):
    for intento in range(max_retries):
        try:
            if "sqlite" in settings.database_url:
                eng = create_engine(
                    settings.database_url,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            else:
                eng = create_engine(
                    settings.database_url,
                    echo=False,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                )
            # Verificar conexion
            from sqlalchemy import text
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Conexion a BD exitosa")
            return eng
        except Exception as e:
            if intento < max_retries - 1:
                logger.warning(f"BD no disponible (intento {intento + 1}/{max_retries}): {e}. Reintentando en {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.warning(f"No se pudo verificar BD tras {max_retries} intentos, continuando de todos modos...")
                if "sqlite" in settings.database_url:
                    return create_engine(
                        settings.database_url,
                        connect_args={"check_same_thread": False},
                        echo=False
                    )
                else:
                    return create_engine(
                        settings.database_url,
                        echo=False,
                        pool_size=10,
                        max_overflow=20,
                        pool_pre_ping=True,
                    )

engine = _crear_engine()

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """Dependency para obtener sesion de BD en rutas"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
