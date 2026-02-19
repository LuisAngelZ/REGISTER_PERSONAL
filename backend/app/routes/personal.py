"""
Rutas CRUD para gestionar Personal
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.db import get_db
from app.models.personal import Personal
from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal
from datetime import datetime, date, timedelta
from calendar import monthrange
from collections import defaultdict
import re
import io
import csv
import logging

logger = logging.getLogger("personal")

router = APIRouter(prefix="/api/personal", tags=["Personal"])


def registrar_audit(db: Session, accion: str, entidad: str, entidad_id: int = None, detalle: str = None):
    """Registra una entrada en el audit log"""
    from app.models.auditlog import AuditLog
    try:
        db.add(AuditLog(accion=accion, entidad=entidad, entidad_id=entidad_id, detalle=detalle))
        db.commit()
    except Exception:
        pass  # No falla la operación principal si falla el audit

# Valores permitidos
PUESTOS_VALIDOS = {"cajero", "mesero", "cocinero", "lavaplatos", "servidora", "guardia", "despacho", "otros"}
TURNOS_VALIDOS = {"mañana", "tarde", "especial"}
DIAS_VALIDOS = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"}
DURACIONES_VALIDAS = {"3_meses", "6_meses", "1_anio"}
HORA_REGEX = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
DOCUMENTO_REGEX = re.compile(r"^[a-zA-Z0-9\-]+$")

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
    sueldo: Optional[float] = None

    @field_validator("nombre", "apellido")
    @classmethod
    def validar_nombre(cls, v):
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("Debe tener entre 1 y 100 caracteres")
        return v

    @field_validator("documento")
    @classmethod
    def validar_documento(cls, v):
        v = v.strip()
        if not v or len(v) > 20:
            raise ValueError("Documento debe tener entre 1 y 20 caracteres")
        if not DOCUMENTO_REGEX.match(v):
            raise ValueError("Documento solo permite letras, numeros y guiones")
        return v

    @field_validator("puesto")
    @classmethod
    def validar_puesto(cls, v):
        if v is not None and v not in PUESTOS_VALIDOS:
            raise ValueError(f"Puesto debe ser uno de: {', '.join(PUESTOS_VALIDOS)}")
        return v

    @field_validator("turno")
    @classmethod
    def validar_turno(cls, v):
        if v is not None and v not in TURNOS_VALIDOS:
            raise ValueError(f"Turno debe ser uno de: {', '.join(TURNOS_VALIDOS)}")
        return v

    @field_validator("hora_entrada", "hora_salida")
    @classmethod
    def validar_hora(cls, v):
        if v is not None and not HORA_REGEX.match(v):
            raise ValueError("Formato de hora invalido, usar HH:MM")
        return v

    @field_validator("duracion_contrato")
    @classmethod
    def validar_duracion(cls, v):
        if v is not None and v not in DURACIONES_VALIDAS:
            raise ValueError(f"Duracion debe ser una de: {', '.join(DURACIONES_VALIDAS)}")
        return v

    @field_validator("dia_libre")
    @classmethod
    def validar_dia_libre(cls, v):
        if v is not None and v not in DIAS_VALIDOS:
            raise ValueError(f"Dia libre debe ser uno de: {', '.join(DIAS_VALIDOS)}")
        return v

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
    sueldo: Optional[float] = None
    activo: Optional[bool] = None

    @field_validator("nombre", "apellido")
    @classmethod
    def validar_nombre(cls, v):
        if v is not None:
            v = v.strip()
            if not v or len(v) > 100:
                raise ValueError("Debe tener entre 1 y 100 caracteres")
        return v

    @field_validator("documento")
    @classmethod
    def validar_documento(cls, v):
        if v is not None:
            v = v.strip()
            if not v or len(v) > 20:
                raise ValueError("Documento debe tener entre 1 y 20 caracteres")
            if not DOCUMENTO_REGEX.match(v):
                raise ValueError("Documento solo permite letras, numeros y guiones")
        return v

    @field_validator("puesto")
    @classmethod
    def validar_puesto(cls, v):
        if v is not None and v not in PUESTOS_VALIDOS:
            raise ValueError(f"Puesto debe ser uno de: {', '.join(PUESTOS_VALIDOS)}")
        return v

    @field_validator("turno")
    @classmethod
    def validar_turno(cls, v):
        if v is not None and v not in TURNOS_VALIDOS:
            raise ValueError(f"Turno debe ser uno de: {', '.join(TURNOS_VALIDOS)}")
        return v

    @field_validator("hora_entrada", "hora_salida")
    @classmethod
    def validar_hora(cls, v):
        if v is not None and not HORA_REGEX.match(v):
            raise ValueError("Formato de hora invalido, usar HH:MM")
        return v

    @field_validator("duracion_contrato")
    @classmethod
    def validar_duracion(cls, v):
        if v is not None and v not in DURACIONES_VALIDAS:
            raise ValueError(f"Duracion debe ser una de: {', '.join(DURACIONES_VALIDAS)}")
        return v

    @field_validator("dia_libre")
    @classmethod
    def validar_dia_libre(cls, v):
        if v is not None and v not in DIAS_VALIDOS:
            raise ValueError(f"Dia libre debe ser uno de: {', '.join(DIAS_VALIDOS)}")
        return v

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
    sueldo: Optional[float]
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
            sueldo=personal.sueldo,
        )
        nuevo_personal.calcular_fecha_fin()

        db.add(nuevo_personal)
        db.commit()
        db.refresh(nuevo_personal)

        nuevo_personal.user_id = nuevo_personal.id
        db.commit()
        db.refresh(nuevo_personal)

        logger.info(f"Personal creado: id={nuevo_personal.id} '{personal.nombre} {personal.apellido}' doc={personal.documento}")
        registrar_audit(db, "crear", "personal", nuevo_personal.id, f"{personal.nombre} {personal.apellido} ({personal.documento})")
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
    limit: int = 200,
    activos: bool = True,
    db: Session = Depends(get_db)
):
    """Obtener lista de personal"""
    try:
        skip = max(0, skip)
        limit = max(1, min(limit, 500))

        query = db.query(Personal)
        if activos:
            query = query.filter(Personal.activo == True)

        personal = query.offset(skip).limit(limit).all()
        return personal
    except Exception as e:
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

# DASHBOARD
@router.get("/stats/dashboard")
def dashboard_stats(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(get_db),
):
    """Estadisticas para el dashboard: asistencia general del mes"""
    from app.models.asistencia import Asistencia

    if mes is None:
        mes = datetime.now().month
    if anio is None:
        anio = datetime.now().year

    dias_en_mes = monthrange(anio, mes)[1]
    fecha_inicio_dt = datetime(anio, mes, 1)
    fecha_fin_dt = datetime(anio, mes, dias_en_mes, 23, 59, 59)

    personal_activo = db.query(Personal).filter(Personal.activo == True).all()

    resumen = []
    total_retrasos = 0
    total_faltas = 0
    total_extras = 0
    por_puesto = defaultdict(int)

    DIAS_SEMANA_MAP = {0: "lunes", 1: "martes", 2: "miercoles", 3: "jueves", 4: "viernes", 5: "sabado", 6: "domingo"}

    # Una sola query para todos los registros del mes (evita N+1)
    ids_activos = [p.id for p in personal_activo]
    todos_registros = []
    if ids_activos:
        todos_registros = db.query(Asistencia).filter(
            and_(
                Asistencia.personal_id.in_(ids_activos),
                Asistencia.fecha_hora >= fecha_inicio_dt,
                Asistencia.fecha_hora <= fecha_fin_dt,
            )
        ).order_by(Asistencia.fecha_hora.asc()).all()

    registros_por_personal: dict = defaultdict(lambda: defaultdict(list))
    for reg in todos_registros:
        fecha_str = reg.fecha_hora.strftime("%Y-%m-%d")
        registros_por_personal[reg.personal_id][fecha_str].append(reg)

    for p in personal_activo:
        por_puesto[p.puesto or "otros"] += 1
        por_fecha = registros_por_personal[p.id]

        dias_trabajados = 0
        dias_falta = 0
        minutos_retraso = 0
        minutos_extra = 0
        hora_entrada_esp = p.hora_entrada or "08:00"
        hora_salida_esp = p.hora_salida or "17:00"
        dia_libre_p = p.dia_libre or "domingo"

        for dia_num in range(1, dias_en_mes + 1):
            fecha = date(anio, mes, dia_num)
            if fecha > date.today():
                break
            fecha_str = fecha.strftime("%Y-%m-%d")
            dow = DIAS_SEMANA_MAP[fecha.weekday()]
            if dow == dia_libre_p:
                continue

            regs_dia = por_fecha.get(fecha_str, [])
            entradas = [r for r in regs_dia if r.tipo == "entrada"]

            if entradas:
                dias_trabajados += 1
                hora_real = entradas[0].fecha_hora.strftime("%H:%M")
                try:
                    diff = (datetime.strptime(hora_real, "%H:%M") - datetime.strptime(hora_entrada_esp, "%H:%M")).total_seconds() / 60
                    if diff > 0:
                        minutos_retraso += int(diff)
                except Exception:
                    pass

                salidas = [r for r in regs_dia if r.tipo == "salida"]
                if salidas:
                    hora_sal = salidas[-1].fecha_hora.strftime("%H:%M")
                    try:
                        diff = (datetime.strptime(hora_sal, "%H:%M") - datetime.strptime(hora_salida_esp, "%H:%M")).total_seconds() / 60
                        if diff > 0:
                            minutos_extra += int(diff)
                    except Exception:
                        pass
            else:
                dias_falta += 1

        total_retrasos += minutos_retraso
        total_faltas += dias_falta
        total_extras += minutos_extra

        resumen.append({
            "id": p.id,
            "nombre": f"{p.nombre} {p.apellido}",
            "puesto": p.puesto,
            "dias_trabajados": dias_trabajados,
            "dias_falta": dias_falta,
            "minutos_retraso": minutos_retraso,
            "minutos_extra": minutos_extra,
        })

    top_retrasos = sorted(resumen, key=lambda x: x["minutos_retraso"], reverse=True)[:5]
    top_faltas = sorted(resumen, key=lambda x: x["dias_falta"], reverse=True)[:5]

    return {
        "mes": mes,
        "anio": anio,
        "total_personal": len(personal_activo),
        "total_minutos_retraso": total_retrasos,
        "total_dias_falta": total_faltas,
        "total_minutos_extra": total_extras,
        "por_puesto": dict(por_puesto),
        "top_retrasos": top_retrasos,
        "top_faltas": top_faltas,
    }

# EXPORTAR LISTA DE PERSONAL
@router.get("/exportar-lista")
def exportar_lista_personal(
    formato: str = "csv",
    activos: bool = True,
    db: Session = Depends(get_db),
):
    """Exporta la lista completa de personal en CSV o Excel"""
    query = db.query(Personal)
    if activos:
        query = query.filter(Personal.activo == True)
    personal = query.all()

    PUESTOS_LBL = {"cajero":"Cajero","mesero":"Mesero","cocinero":"Cocinero","lavaplatos":"Lavaplatos",
                    "servidora":"Servidora","guardia":"Guardia","despacho":"Despacho","otros":"Otros"}
    TURNOS_LBL = {"mañana":"Manana","tarde":"Tarde","especial":"Especial"}

    headers = ["ID","Nombre","Apellido","Documento","Puesto","Turno","Hora Entrada","Hora Salida",
               "Fecha Inicio","Fecha Fin","Dia Libre","Activo"]

    rows = []
    for p in personal:
        rows.append([
            p.id,
            p.nombre,
            p.apellido,
            p.documento,
            PUESTOS_LBL.get(p.puesto, p.puesto or ""),
            TURNOS_LBL.get(p.turno, p.turno or ""),
            p.hora_entrada or "",
            p.hora_salida or "",
            str(p.fecha_inicio) if p.fecha_inicio else "",
            str(p.fecha_fin) if p.fecha_fin else "",
            p.dia_libre or "",
            "Si" if p.activo else "No",
        ])

    if formato == "excel":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Personal"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=lista_personal.xlsx"}
        )
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        output.seek(0)
        logger.info(f"Lista exportada: {len(rows)} registros en {formato}")
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=lista_personal.csv"}
        )


class AsistenciaManualRequest(BaseModel):
    personal_id: int
    fecha: str  # YYYY-MM-DD
    hora_ingreso: Optional[str] = None  # HH:MM
    hora_salida: Optional[str] = None  # HH:MM

    @field_validator("fecha")
    @classmethod
    def validar_fecha(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Formato de fecha invalido, usar YYYY-MM-DD")
        return v

    @field_validator("hora_ingreso", "hora_salida")
    @classmethod
    def validar_hora(cls, v):
        if v is not None and not HORA_REGEX.match(v):
            raise ValueError("Formato de hora invalido, usar HH:MM")
        return v

# Asistencia manual (debe ir antes de /{personal_id} routes con sub-paths)
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
    logger.info(f"Asistencia manual: personal_id={data.personal_id} fecha={data.fecha} registros={registros_creados}")
    return {
        "status": "ok",
        "registros_creados": registros_creados,
        "mensaje": f"Asistencia del {data.fecha} actualizada correctamente",
    }

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

        update_data = personal_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(personal, field, value)

        # Recalcular fecha_fin si cambio fecha_inicio o duracion_contrato
        if "fecha_inicio" in update_data or "duracion_contrato" in update_data:
            personal.calcular_fecha_fin()

        personal.fecha_actualizacion = datetime.utcnow()
        db.commit()
        db.refresh(personal)
        logger.info(f"Personal actualizado: id={personal_id} campos={list(update_data.keys())}")
        registrar_audit(db, "actualizar", "personal", personal_id, f"Campos: {', '.join(update_data.keys())}")
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
        logger.info(f"Personal desactivado: id={personal_id} '{personal.nombre} {personal.apellido}'")
        registrar_audit(db, "desactivar", "personal", personal_id, f"{personal.nombre} {personal.apellido}")
        return {"mensaje": "Personal desactivado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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

    limit = max(1, min(limit, 1000))

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

    if not (1 <= mes <= 12):
        raise HTTPException(status_code=400, detail="Mes debe estar entre 1 y 12")
    if not (2000 <= anio <= 2100):
        raise HTTPException(status_code=400, detail="Anio debe estar entre 2000 y 2100")

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


# ============ EXPORTAR REPORTE ============
@router.get("/{personal_id}/exportar-reporte")
def exportar_reporte(
    personal_id: int,
    mes: int = None,
    anio: int = None,
    formato: str = "csv",
    db: Session = Depends(get_db),
):
    """Exporta el reporte mensual en CSV o Excel"""
    # Reusar la logica del reporte mensual
    data = reporte_mensual(personal_id, mes, anio, db)

    DIAS_LABEL = {
        "lunes": "Lunes", "martes": "Martes", "miercoles": "Miercoles",
        "jueves": "Jueves", "viernes": "Viernes", "sabado": "Sabado", "domingo": "Domingo"
    }

    headers = ["Fecha", "Dia", "Ingreso", "Salida", "Retraso (min)", "Extra (min)", "Estado"]
    rows = []
    for dia in data["dias"]:
        estado = "LIBRE" if dia["es_libre"] else ("Trabajo" if dia["trabajo"] else "Falta")
        rows.append([
            dia["fecha"],
            DIAS_LABEL.get(dia["dia_semana"], dia["dia_semana"]),
            dia["hora_ingreso"] or "",
            dia["hora_salida"] or "",
            dia["minutos_retraso"] if not dia["es_libre"] else "",
            dia["minutos_extra"] if not dia["es_libre"] else "",
            estado,
        ])

    # Fila resumen
    rows.append([])
    rows.append(["Resumen", "", "", "", "", "", ""])
    rows.append(["Dias trabajados", data["dias_trabajados"]])
    rows.append(["Dias falta", data["dias_falta"]])
    rows.append(["Total min. retraso", data["total_minutos_retraso"]])
    rows.append(["Total min. extra", data["total_minutos_extra"]])

    nombre = data["nombre"].replace(" ", "_")
    mes_str = str(data["mes"]).zfill(2)

    if formato == "excel":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = f"Reporte {mes_str}-{data['anio']}"

        # Titulo
        ws.append([f"Reporte de Asistencia - {data['nombre']}"])
        ws.append([f"Periodo: {mes_str}/{data['anio']} | Turno: {data['turno']} | Libre: {data['dia_libre']}"])
        ws.append([])
        ws.append(headers)

        for row in rows:
            ws.append(row)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=reporte_{nombre}_{mes_str}_{data['anio']}.xlsx"}
        )
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([f"Reporte de Asistencia - {data['nombre']}"])
        writer.writerow([f"Periodo: {mes_str}/{data['anio']} | Turno: {data['turno']} | Libre: {data['dia_libre']}"])
        writer.writerow([])
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=reporte_{nombre}_{mes_str}_{data['anio']}.csv"}
        )
