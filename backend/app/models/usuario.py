from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database.db import Base


class Usuario(Base):
    """Modelo para usuarios del sistema (login)"""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(String(20), default="operador")  # admin, operador
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
