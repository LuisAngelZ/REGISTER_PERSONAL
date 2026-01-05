from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database.db import Base

class Personal(Base):
    """Modelo para datos del personal"""
    __tablename__ = "personal"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)  # ID en dispositivo ZKTeco
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    documento = Column(String(20), unique=True, index=True)
    email = Column(String(255), unique=True, nullable=True)
    puesto = Column(String(100))
    departamento = Column(String(100))
    dias_trabajo = Column(String(50), default="Lunes,Martes,Miércoles,Jueves,Viernes")  # Días de trabajo
    hora_entrada = Column(String(10), default="08:00")  # Hora de entrada esperada
    hora_salida = Column(String(10), default="17:00")   # Hora de salida esperada
    activo = Column(Boolean, default=True)
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Personal(id={self.id}, nombre={self.nombre}, documento={self.documento})>"
