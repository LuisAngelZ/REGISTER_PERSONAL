"""
Rutas CRUD para gestionar Personal
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.personal import Personal
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/personal", tags=["Personal"])

# Schemas Pydantic
class PersonalCreate(BaseModel):
    nombre: str
    apellido: str
    documento: str
    email: Optional[str] = None
    puesto: Optional[str] = None
    departamento: Optional[str] = None
    user_id: Optional[int] = None
    dias_trabajo: Optional[str] = "Lunes,Martes,Miércoles,Jueves,Viernes"
    hora_entrada: Optional[str] = "08:00"
    hora_salida: Optional[str] = "17:00"

class PersonalUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    documento: Optional[str] = None
    email: Optional[str] = None
    puesto: Optional[str] = None
    departamento: Optional[str] = None
    dias_trabajo: Optional[str] = None
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    activo: Optional[bool] = None

class PersonalResponse(BaseModel):
    id: int
    user_id: Optional[int]
    nombre: str
    apellido: str
    documento: str
    email: Optional[str]
    puesto: Optional[str]
    departamento: Optional[str]
    dias_trabajo: str
    hora_entrada: str
    hora_salida: str
    activo: bool
    fecha_ingreso: datetime

    class Config:
        from_attributes = True

# CREATE - Crear nuevo personal
@router.post("/", response_model=PersonalResponse)
def crear_personal(personal: PersonalCreate, db: Session = Depends(get_db)):
    """Crear un nuevo registro de personal"""
    try:
        # Verificar si el documento ya existe
        db_personal = db.query(Personal).filter(Personal.documento == personal.documento).first()
        if db_personal:
            raise HTTPException(status_code=400, detail="El documento ya existe")
        
        nuevo_personal = Personal(
            nombre=personal.nombre,
            apellido=personal.apellido,
            documento=personal.documento,
            email=personal.email,
            puesto=personal.puesto,
            departamento=personal.departamento,
            user_id=personal.user_id,
            dias_trabajo=personal.dias_trabajo,
            hora_entrada=personal.hora_entrada,
            hora_salida=personal.hora_salida
        )
        db.add(nuevo_personal)
        db.commit()
        db.refresh(nuevo_personal)
        return nuevo_personal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# READ - Obtener todos los registros
@router.get("/", response_model=List[PersonalResponse])
def obtener_todos(
    skip: int = 0,
    limit: int = 100,
    activos: bool = True,
    db: Session = Depends(get_db)
):
    """Obtener lista de personal"""
    try:
        query = db.query(Personal)
        if activos:
            query = query.filter(Personal.activo == True)
        
        personal = query.offset(skip).limit(limit).all()
        return personal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# READ - Obtener por ID
@router.get("/{personal_id}", response_model=PersonalResponse)
def obtener_personal(personal_id: int, db: Session = Depends(get_db)):
    """Obtener un personal específico por ID"""
    try:
        personal = db.query(Personal).filter(Personal.id == personal_id).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado")
        return personal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# READ - Obtener por documento
@router.get("/documento/{documento}", response_model=PersonalResponse)
def obtener_por_documento(documento: str, db: Session = Depends(get_db)):
    """Obtener personal por número de documento"""
    try:
        personal = db.query(Personal).filter(Personal.documento == documento).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado")
        return personal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE - Actualizar personal
@router.put("/{personal_id}", response_model=PersonalResponse)
def actualizar_personal(
    personal_id: int,
    personal_update: PersonalUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar datos de un personal"""
    try:
        personal = db.query(Personal).filter(Personal.id == personal_id).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado")
        
        # Actualizar solo los campos proporcionados
        update_data = personal_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(personal, field, value)
        
        personal.fecha_actualizacion = datetime.utcnow()
        db.commit()
        db.refresh(personal)
        return personal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# DELETE - Desactivar personal (soft delete)
@router.delete("/{personal_id}")
def eliminar_personal(personal_id: int, db: Session = Depends(get_db)):
    """Desactivar un personal (no elimina del BD)"""
    try:
        personal = db.query(Personal).filter(Personal.id == personal_id).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado")
        
        personal.activo = False
        personal.fecha_actualizacion = datetime.utcnow()
        db.commit()
        return {"mensaje": "Personal desactivado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Estadísticas
@router.get("/stats/total", response_model=dict)
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Obtener estadísticas del personal"""
    try:
        total = db.query(Personal).count()
        activos = db.query(Personal).filter(Personal.activo == True).count()
        inactivos = db.query(Personal).filter(Personal.activo == False).count()
        
        return {
            "total": total,
            "activos": activos,
            "inactivos": inactivos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ASISTENCIA
@router.get("/{personal_id}/asistencia")
def obtener_asistencia_personal(personal_id: int, db: Session = Depends(get_db)):
    """Obtener registros de asistencia de un personal"""
    from app.models.asistencia import Asistencia
    
    try:
        # Verificar que el personal existe
        personal = db.query(Personal).filter(Personal.id == personal_id).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado")
        
        # Obtener registros de asistencia
        registros = db.query(Asistencia).filter(
            Asistencia.personal_id == personal_id
        ).order_by(Asistencia.fecha_hora.desc()).limit(30).all()
        
        registros_formateados = []
        for reg in registros:
            registros_formateados.append({
                "id": reg.id,
                "tipo": reg.tipo,
                "fecha_hora": reg.fecha_hora.isoformat() if reg.fecha_hora else None,
                "dispositivo_ip": reg.dispositivo_ip
            })
        
        return {
            "personal_id": personal_id,
            "nombre": f"{personal.nombre} {personal.apellido}",
            "total_registros": len(registros),
            "registros": registros_formateados
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
