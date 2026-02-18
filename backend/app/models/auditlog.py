from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database.db import Base


class AuditLog(Base):
    """Registro de cambios realizados en el sistema"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    accion = Column(String(50), nullable=False)  # crear, actualizar, desactivar, login, sync
    entidad = Column(String(50))  # personal, usuario, asistencia, dispositivo
    entidad_id = Column(Integer, nullable=True)
    detalle = Column(Text, nullable=True)
    usuario = Column(String(100), nullable=True)  # quien realizo la accion
    ip = Column(String(50), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)
