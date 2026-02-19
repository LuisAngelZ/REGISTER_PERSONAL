from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Numeric
from datetime import datetime, timedelta
from app.database.db import Base


class Personal(Base):
    """Modelo para datos del personal"""
    __tablename__ = "personal"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)  # ID en dispositivo ZKTeco (= id)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    documento = Column(String(20), unique=True, index=True)  # Carnet de Identidad
    puesto = Column(String(100))  # cajero, mesero, cocinero, lavaplatos, servidora, guardia, despacho, otros
    turno = Column(String(20), default="mañana")  # mañana, tarde, especial
    hora_entrada = Column(String(10), default="08:00")
    hora_salida = Column(String(10), default="17:00")
    fecha_inicio = Column(Date, nullable=True)  # Fecha inicio de trabajo
    duracion_contrato = Column(String(20), default="3_meses")  # 3_meses, 6_meses, 1_anio
    fecha_fin = Column(Date, nullable=True)  # Calculado automaticamente
    dia_libre = Column(String(20), default="domingo")  # lunes, martes, ..., domingo
    sueldo = Column(Numeric(10, 2), nullable=True)  # Sueldo mensual en Bs
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calcular_fecha_fin(self):
        """Calcula fecha_fin segun fecha_inicio y duracion_contrato"""
        if not self.fecha_inicio:
            return None
        if self.duracion_contrato == "3_meses":
            self.fecha_fin = self.fecha_inicio + timedelta(days=85)
        elif self.duracion_contrato == "6_meses":
            self.fecha_fin = self.fecha_inicio + timedelta(days=180)
        elif self.duracion_contrato == "1_anio":
            self.fecha_fin = self.fecha_inicio + timedelta(days=365)
        return self.fecha_fin

    def __repr__(self):
        return f"<Personal(id={self.id}, nombre={self.nombre}, documento={self.documento})>"
