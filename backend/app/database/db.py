from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)


def _crear_engine(max_retries=5, retry_delay=3):
    """Crea el engine PostgreSQL con reintentos (para esperar que el contenedor inicie)"""
    for intento in range(max_retries):
        try:
            eng = create_engine(
                settings.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
            )
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Conexion a PostgreSQL exitosa")
            return eng
        except Exception as e:
            if intento < max_retries - 1:
                logger.warning(
                    f"BD no disponible (intento {intento + 1}/{max_retries}): {e}. "
                    f"Reintentando en {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                logger.warning(f"No se pudo conectar tras {max_retries} intentos, continuando...")
                return create_engine(
                    settings.database_url,
                    echo=False,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                )


engine = _crear_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency para obtener sesion de BD en rutas"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
