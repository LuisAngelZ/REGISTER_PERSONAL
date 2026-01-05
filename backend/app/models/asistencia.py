from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database.db import Base

class Asistencia(Base):
    """Modelo para registros de asistencia (entrada/salida)"""
    __tablename__ = "asistencia"
    
    id = Column(Integer, primary_key=True, index=True)
    personal_id = Column(Integer, ForeignKey("personal.id"), index=True)
    user_id = Column(Integer, index=True)  # ID del dispositivo ZKTeco
    tipo = Column(String(10))  # 'entrada' o 'salida'
    fecha_hora = Column(DateTime, index=True)  # Fecha y hora del marcaje
    dispositivo_ip = Column(String(15))  # IP del dispositivo
    sincronizado = Column(String(1), default='N')  # 'S' o 'N'
    fecha_sincronizacion = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Asistencia(personal_id={self.personal_id}, tipo={self.tipo}, fecha_hora={self.fecha_hora})>"
