"""
Rutas CRUD para gestionar Personal
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.db import get_db
from app.models.personal import Personal
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, timedelta
from calendar import monthrange
from collections import defaultdict

router = APIRouter(prefix="/api/personal", tags=["Personal"])

# Schemas Pydantic
class PersonalCreate(BaseModel):
    nombre: str
    apellido: str
    documento: str
    puesto: Optional[str] = None
    turno: Optional[str] = "mañana"
    hora_entrada: Optional[str] = "08:00"
    hora_salida: Optional[str] = "17:00"
    fecha_inicio: Optional[date] = None
    duracion_contrato: Optional[str] = "3_meses"
    dia_libre: Optional[str] = "domingo"

class PersonalUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    documento: Optional[str] = None
    puesto: Optional[str] = None
    turno: Optional[str] = None
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    fecha_inicio: Optional[date] = None
    duracion_contrato: Optional[str] = None
    dia_libre: Optional[str] = None
    activo: Optional[bool] = None

class PersonalResponse(BaseModel):
    id: int
    user_id: Optional[int]
    nombre: str
    apellido: str
    documento: str
    puesto: Optional[str]
    turno: Optional[str]
    hora_entrada: str
    hora_salida: str
    fecha_inicio: Optional[date]
    duracion_contrato: Optional[str]
    fecha_fin: Optional[date]
    dia_libre: Optional[str]
    activo: bool

    class Config:
        from_attributes = True

# CREATE - Crear nuevo personal
@router.post("/", response_model=PersonalResponse)
def crear_personal(personal: PersonalCreate, db: Session = Depends(get_db)):
    """Crear un nuevo registro de personal"""
    try:
        db_personal = db.query(Personal).filter(Personal.documento == personal.documento).first()
        if db_personal:
            raise HTTPException(status_code=400, detail="El documento ya existe")

        nuevo_personal = Personal(
            nombre=personal.nombre,
            apellido=personal.apellido,
            documento=personal.documento,
            puesto=personal.puesto,
            turno=personal.turno,
            hora_entrada=personal.hora_entrada,
            hora_salida=personal.hora_salida,
            fecha_inicio=personal.fecha_inicio,
            duracion_contrato=personal.duracion_contrato,
            dia_libre=personal.dia_libre,
        )
        # Calcular fecha_fin automaticamente
        nuevo_personal.calcular_fecha_fin()

        db.add(nuevo_personal)
        db.commit()
        db.refresh(nuevo_personal)

        # user_id = id (auto-incremental)
        nuevo_personal.user_id = nuevo_personal.id
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

        update_data = personal_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(personal, field, value)

        # Recalcular fecha_fin si cambio fecha_inicio o duracion_contrato
        if "fecha_inicio" in update_data or "duracion_contrato" in update_data:
            personal.calcular_fecha_fin()

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
def obtener_asistencia_personal(
    personal_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Obtener registros de asistencia de un personal"""
    from app.models.asistencia import Asistencia

    try:
        personal = db.query(Personal).filter(Personal.id == personal_id).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado")

        total = db.query(Asistencia).filter(
            Asistencia.personal_id == personal_id
        ).count()

        registros = db.query(Asistencia).filter(
            Asistencia.personal_id == personal_id
        ).order_by(Asistencia.fecha_hora.desc()).limit(limit).all()

        registros_formateados = []
        for reg in registros:
            registros_formateados.append({
                "id": reg.id,
                "tipo": reg.tipo,
                "fecha_hora": reg.fecha_hora.isoformat() if reg.fecha_hora else None,
                "dispositivo_ip": reg.dispositivo_ip,
            })

        return {
            "personal_id": personal_id,
            "nombre": f"{personal.nombre} {personal.apellido}",
            "total_registros": total,
            "registros": registros_formateados,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# REPORTE MENSUAL
@router.get("/{personal_id}/reporte-mensual")
def reporte_mensual(
    personal_id: int,
    mes: int = None,
    anio: int = None,
    db: Session = Depends(get_db),
):
    """Genera reporte mensual de asistencia con horas de ingreso/salida por dia"""
    from app.models.asistencia import Asistencia

    if mes is None:
        mes = datetime.now().month
    if anio is None:
        anio = datetime.now().year

    personal = db.query(Personal).filter(Personal.id == personal_id).first()
    if not personal:
        raise HTTPException(status_code=404, detail="Personal no encontrado")

    dias_en_mes = monthrange(anio, mes)[1]
    fecha_inicio = datetime(anio, mes, 1)
    fecha_fin = datetime(anio, mes, dias_en_mes, 23, 59, 59)

    registros = db.query(Asistencia).filter(
        and_(
            Asistencia.personal_id == personal_id,
            Asistencia.fecha_hora >= fecha_inicio,
            Asistencia.fecha_hora <= fecha_fin,
        )
    ).order_by(Asistencia.fecha_hora.asc()).all()

    por_fecha = defaultdict(list)
    for reg in registros:
        fecha_str = reg.fecha_hora.strftime("%Y-%m-%d")
        por_fecha[fecha_str].append({
            "id": reg.id,
            "tipo": reg.tipo,
            "hora": reg.fecha_hora.strftime("%H:%M"),
            "fecha_hora": reg.fecha_hora.isoformat(),
        })

    dias = []
    dias_trabajados = 0
    dias_falta = 0
    total_minutos_retraso = 0
    total_minutos_extra = 0
    hora_entrada_esperada = personal.hora_entrada or "08:00"
    hora_salida_esperada = personal.hora_salida or "17:00"
    dia_libre = personal.dia_libre or "domingo"

    DIAS_SEMANA_MAP = {0: "lunes", 1: "martes", 2: "miercoles", 3: "jueves", 4: "viernes", 5: "sabado", 6: "domingo"}

    for dia in range(1, dias_en_mes + 1):
        fecha = date(anio, mes, dia)
        fecha_str = fecha.strftime("%Y-%m-%d")
        dow = DIAS_SEMANA_MAP[fecha.weekday()]
        es_libre = (dow == dia_libre)

        regs = por_fecha.get(fecha_str, [])
        entradas = [r for r in regs if r["tipo"] == "entrada"]
        salidas = [r for r in regs if r["tipo"] == "salida"]

        hora_ingreso = entradas[0]["hora"] if entradas else None
        hora_salida_real = salidas[-1]["hora"] if salidas else None

        minutos_retraso = 0
        minutos_extra = 0
        if hora_ingreso and not es_libre:
            try:
                entrada_real = datetime.strptime(hora_ingreso, "%H:%M")
                entrada_esperada = datetime.strptime(hora_entrada_esperada, "%H:%M")
                diff = (entrada_real - entrada_esperada).total_seconds() / 60
                if diff > 0:
                    minutos_retraso = int(diff)
            except Exception:
                pass

        if hora_salida_real and not es_libre:
            try:
                salida_real = datetime.strptime(hora_salida_real, "%H:%M")
                salida_esperada = datetime.strptime(hora_salida_esperada, "%H:%M")
                diff = (salida_real - salida_esperada).total_seconds() / 60
                if diff > 0:
                    minutos_extra = int(diff)
            except Exception:
                pass

        trabajo = bool(hora_ingreso or hora_salida_real)
        if trabajo and not es_libre:
            dias_trabajados += 1
            total_minutos_retraso += minutos_retraso
            total_minutos_extra += minutos_extra
        elif not es_libre and fecha <= date.today():
            dias_falta += 1

        dias.append({
            "fecha": fecha_str,
            "dia_semana": dow,
            "es_libre": es_libre,
            "hora_ingreso": hora_ingreso,
            "hora_salida": hora_salida_real,
            "minutos_retraso": minutos_retraso,
            "minutos_extra": minutos_extra,
            "trabajo": trabajo,
        })

    return {
        "personal_id": personal.id,
        "nombre": f"{personal.nombre} {personal.apellido}",
        "puesto": personal.puesto,
        "turno": personal.turno,
        "hora_entrada": hora_entrada_esperada,
        "hora_salida": hora_salida_esperada,
        "dia_libre": dia_libre,
        "mes": mes,
        "anio": anio,
        "dias_en_mes": dias_en_mes,
        "dias_trabajados": dias_trabajados,
        "dias_falta": dias_falta,
        "total_minutos_retraso": total_minutos_retraso,
        "total_minutos_extra": total_minutos_extra,
        "dias": dias,
    }


class AsistenciaManualRequest(BaseModel):
    personal_id: int
    fecha: str  # YYYY-MM-DD
    hora_ingreso: Optional[str] = None  # HH:MM
    hora_salida: Optional[str] = None  # HH:MM


@router.post("/asistencia-manual")
def registrar_asistencia_manual(data: AsistenciaManualRequest, db: Session = Depends(get_db)):
    """Registra o actualiza manualmente la asistencia de un dia"""
    from app.models.asistencia import Asistencia

    personal = db.query(Personal).filter(Personal.id == data.personal_id).first()
    if not personal:
        raise HTTPException(status_code=404, detail="Personal no encontrado")

    fecha_date = datetime.strptime(data.fecha, "%Y-%m-%d").date()
    fecha_inicio_dt = datetime(fecha_date.year, fecha_date.month, fecha_date.day, 0, 0, 0)
    fecha_fin_dt = datetime(fecha_date.year, fecha_date.month, fecha_date.day, 23, 59, 59)

    db.query(Asistencia).filter(
        and_(
            Asistencia.personal_id == data.personal_id,
            Asistencia.fecha_hora >= fecha_inicio_dt,
            Asistencia.fecha_hora <= fecha_fin_dt,
        )
    ).delete()

    registros_creados = 0

    if data.hora_ingreso:
        h, m = data.hora_ingreso.split(":")
        db.add(Asistencia(
            personal_id=data.personal_id,
            user_id=personal.user_id,
            tipo="entrada",
            fecha_hora=datetime(fecha_date.year, fecha_date.month, fecha_date.day, int(h), int(m)),
            dispositivo_ip="manual",
            sincronizado="S",
            fecha_sincronizacion=datetime.utcnow(),
        ))
        registros_creados += 1

    if data.hora_salida:
        h, m = data.hora_salida.split(":")
        db.add(Asistencia(
            personal_id=data.personal_id,
            user_id=personal.user_id,
            tipo="salida",
            fecha_hora=datetime(fecha_date.year, fecha_date.month, fecha_date.day, int(h), int(m)),
            dispositivo_ip="manual",
            sincronizado="S",
            fecha_sincronizacion=datetime.utcnow(),
        ))
        registros_creados += 1

    db.commit()
    return {
        "status": "ok",
        "registros_creados": registros_creados,
        "mensaje": f"Asistencia del {data.fecha} actualizada correctamente",
    }
