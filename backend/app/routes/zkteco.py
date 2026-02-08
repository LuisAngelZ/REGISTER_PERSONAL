"""
Rutas para integración con dispositivo biométrico ZKTeco
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.services.zkteco_service import zkteco_service
from app.database.db import get_db
from app.models.personal import Personal
from app.models.asistencia import Asistencia
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zkteco", tags=["ZKTeco"])

CONFIG_FILE = Path(__file__).parent.parent.parent / "device_config.json"


def _cargar_config_guardada():
    """Carga la config guardada del archivo JSON"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _guardar_config(ip: str, puerto: int, password: int):
    """Guarda la config del dispositivo a archivo JSON"""
    config = {"ip": ip, "puerto": puerto, "password": password}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# Cargar config guardada al iniciar el módulo
_config_guardada = _cargar_config_guardada()
if _config_guardada:
    zkteco_service.ip = _config_guardada["ip"]
    zkteco_service.port = _config_guardada["puerto"]
    zkteco_service.password = _config_guardada.get("password", 0)
    logger.info(f"Config cargada desde archivo: {_config_guardada['ip']}:{_config_guardada['puerto']}")


DEBOUNCE_SEGUNDOS = 30  # Ignorar marcajes duplicados dentro de este rango

# Turnos predefinidos con hora_entrada y hora_salida
TURNOS = {
    "mañana":   {"hora_entrada": "08:00", "hora_salida": "17:00"},
    "tarde":    {"hora_entrada": "13:00", "hora_salida": "22:00"},
    "especial": {"hora_entrada": "12:00", "hora_salida": "21:00"},
}


def _asignar_tipos_alternados(registros: list) -> list:
    """
    Asigna entrada/salida alternando por usuario por día.
    - Filtra marcajes duplicados (< 30 seg entre marcajes del mismo usuario)
    - Primer marcaje válido del día = entrada, segundo = salida, etc.
    """
    por_usuario_dia = defaultdict(list)
    for i, reg in enumerate(registros):
        ts = reg["timestamp"]
        if ts:
            fecha = ts.date() if hasattr(ts, "date") else str(ts)[:10]
            key = (str(reg["user_id"]), str(fecha))
            por_usuario_dia[key].append((i, reg))

    for key, grupo in por_usuario_dia.items():
        grupo.sort(key=lambda x: x[1]["timestamp"])

        # Filtrar duplicados: si hay < 30 seg entre marcajes, ignorar el segundo
        validos = []
        ultimo_ts = None
        for _, reg in grupo:
            ts = reg["timestamp"]
            if ultimo_ts is not None:
                diff = (ts - ultimo_ts).total_seconds()
                if diff < DEBOUNCE_SEGUNDOS:
                    reg["tipo_auto"] = "duplicado"
                    continue
            validos.append(reg)
            ultimo_ts = ts

        # Alternar entrada/salida solo con marcajes válidos
        for orden, reg in enumerate(validos):
            reg["tipo_auto"] = "entrada" if orden % 2 == 0 else "salida"

    # Registros sin timestamp quedan como entrada
    for reg in registros:
        if "tipo_auto" not in reg:
            reg["tipo_auto"] = "entrada"

    return registros


class ConfigurarIPRequest(BaseModel):
    ip: str
    puerto: int = 4370
    password: int = 0


class ExportarUsuarioRequest(BaseModel):
    personal_id: int
    uid: Optional[int] = None
    password: str = ""
    privilegio: int = 0  # 0=Usuario, 14=Admin


@router.get("/turnos")
def obtener_turnos():
    """Retorna los turnos disponibles con sus horarios"""
    return TURNOS


@router.get("/config")
def obtener_config():
    """Obtiene la configuración actual del dispositivo"""
    return {
        "ip": zkteco_service.ip,
        "puerto": zkteco_service.port,
        "password": zkteco_service.password,
        "guardado": CONFIG_FILE.exists(),
    }


@router.post("/configurar-ip")
def configurar_ip(config: ConfigurarIPRequest):
    """Configurar y guardar IP, puerto y password del dispositivo ZKTeco"""
    zkteco_service.ip = config.ip
    zkteco_service.port = config.puerto
    zkteco_service.password = config.password
    _guardar_config(config.ip, config.puerto, config.password)
    logger.info(f"Config guardada: {config.ip}:{config.puerto}")
    return {
        "status": "configurado",
        "ip": config.ip,
        "puerto": config.puerto,
        "mensaje": "Configuración guardada correctamente",
    }


@router.get("/test-conexion")
def test_conexion():
    """Prueba la conexión con el dispositivo ZKTeco"""
    resultado = zkteco_service.test_conexion()
    if resultado["conectado"]:
        return {
            "status": "conectado",
            "mensaje": "Conexión exitosa",
            "info": resultado["info"],
        }
    raise HTTPException(
        status_code=503,
        detail=f"No se pudo conectar: {resultado.get('error', 'Error desconocido')}",
    )


@router.get("/usuarios")
def obtener_usuarios():
    """Obtiene la lista de usuarios del dispositivo ZKTeco"""
    try:
        usuarios = zkteco_service.obtener_usuarios()
        return {
            "total": len(usuarios),
            "usuarios": usuarios,
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sincronizar-usuarios")
def sincronizar_usuarios(db: Session = Depends(get_db)):
    """
    IMPORTAR: Sincroniza usuarios del dispositivo hacia la base de datos.
    Crea registros de personal nuevos para usuarios que no existen.
    """
    try:
        usuarios = zkteco_service.obtener_usuarios()
        if not usuarios:
            return {"total_sincronizados": 0, "mensaje": "No hay usuarios en el dispositivo"}

        sincronizados = 0
        actualizados = 0
        for usuario in usuarios:
            user_id_int = int(usuario["user_id"]) if usuario["user_id"] else None
            personal_existente = db.query(Personal).filter(
                Personal.user_id == user_id_int
            ).first()

            if not personal_existente:
                nuevo_personal = Personal(
                    user_id=user_id_int,
                    nombre=usuario["nombre"] if usuario["nombre"] else f"Usuario {usuario['user_id']}",
                    apellido="",
                    documento=str(usuario["card"]) if usuario["card"] else f"ZK-{usuario['user_id']}",
                    puesto="Sin especificar",
                    departamento="Sin especificar",
                )
                db.add(nuevo_personal)
                sincronizados += 1
            else:
                if usuario["nombre"] and personal_existente.nombre != usuario["nombre"]:
                    personal_existente.nombre = usuario["nombre"]
                    personal_existente.fecha_actualizacion = datetime.now(timezone.utc)
                    actualizados += 1

        db.commit()
        logger.info(f"Usuarios sincronizados: {sincronizados}, actualizados: {actualizados}")

        return {
            "total_sincronizados": sincronizados,
            "total_actualizados": actualizados,
            "total_en_dispositivo": len(usuarios),
            "mensaje": f"Se importaron {sincronizados} usuarios nuevos, {actualizados} actualizados",
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error al sincronizar usuarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exportar-usuario")
def exportar_usuario(data: ExportarUsuarioRequest, db: Session = Depends(get_db)):
    """
    EXPORTAR: Registra un empleado de la BD en el dispositivo biométrico.
    """
    try:
        personal = db.query(Personal).filter(Personal.id == data.personal_id).first()
        if not personal:
            raise HTTPException(status_code=404, detail="Personal no encontrado en la base de datos")

        uid = data.uid if data.uid else (personal.user_id if personal.user_id else personal.id)
        nombre_completo = f"{personal.nombre} {personal.apellido}".strip()[:24]  # ZKTeco limita a 24 chars

        zkteco_service.registrar_usuario(
            uid=uid,
            name=nombre_completo,
            privilege=data.privilegio,
            password=data.password,
            user_id=str(uid),
            card=0,
        )

        if not personal.user_id:
            personal.user_id = uid
            personal.fecha_actualizacion = datetime.now(timezone.utc)
            db.commit()

        return {
            "status": "exportado",
            "mensaje": f"Usuario '{nombre_completo}' registrado en el dispositivo",
            "uid": uid,
            "nombre": nombre_completo,
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al exportar usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exportar-todos")
def exportar_todos_usuarios(db: Session = Depends(get_db)):
    """
    EXPORTAR MASIVO: Registra todos los empleados activos en el dispositivo.
    """
    try:
        personal_list = db.query(Personal).filter(Personal.activo == True).all()
        if not personal_list:
            return {"total_exportados": 0, "mensaje": "No hay personal activo para exportar"}

        exportados = 0
        errores = []
        for personal in personal_list:
            try:
                uid = personal.user_id if personal.user_id else personal.id
                nombre_completo = f"{personal.nombre} {personal.apellido}".strip()[:24]

                zkteco_service.registrar_usuario(
                    uid=uid,
                    name=nombre_completo,
                    privilege=0,
                    password="",
                    user_id=str(uid),
                )

                if not personal.user_id:
                    personal.user_id = uid
                    personal.fecha_actualizacion = datetime.now(timezone.utc)

                exportados += 1
            except Exception as e:
                errores.append({"personal_id": personal.id, "nombre": personal.nombre, "error": str(e)})

        db.commit()
        logger.info(f"Exportación masiva: {exportados} usuarios enviados al dispositivo")

        return {
            "total_exportados": exportados,
            "total_personal": len(personal_list),
            "errores": errores,
            "mensaje": f"Se exportaron {exportados} de {len(personal_list)} usuarios al dispositivo",
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error en exportación masiva: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/eliminar-usuario/{uid}")
def eliminar_usuario_dispositivo(uid: int):
    """Elimina un usuario del dispositivo biométrico por su UID"""
    try:
        zkteco_service.eliminar_usuario(uid=uid)
        return {
            "status": "eliminado",
            "mensaje": f"Usuario con UID {uid} eliminado del dispositivo",
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error al eliminar usuario del dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registros-asistencia")
def obtener_registros():
    """Obtiene los registros de asistencia del dispositivo con tipo auto-detectado"""
    try:
        registros = zkteco_service.obtener_registros_asistencia()
        registros = _asignar_tipos_alternados(registros)

        registros_formateados = []
        duplicados = 0
        punch_map = {0: "huella", 1: "password", 2: "tarjeta"}
        for reg in registros:
            if reg["tipo_auto"] == "duplicado":
                duplicados += 1
                continue
            registros_formateados.append({
                "user_id": reg["user_id"],
                "timestamp": reg["timestamp"].isoformat() if reg["timestamp"] else None,
                "tipo": reg["tipo_auto"],
                "status_raw": reg["status"],
                "metodo": punch_map.get(reg["punch"], f"otro({reg['punch']})"),
            })

        return {
            "total": len(registros_formateados),
            "duplicados_filtrados": duplicados,
            "registros": registros_formateados,
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener registros: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sincronizar-registros")
def sincronizar_registros(db: Session = Depends(get_db)):
    """
    IMPORTAR: Sincroniza registros de asistencia del dispositivo a la BD.
    Usa detección automática: alterna entrada/salida por usuario por día.
    """
    try:
        registros = zkteco_service.obtener_registros_asistencia()
        if not registros:
            return {"total_sincronizados": 0, "mensaje": "No hay registros en el dispositivo"}

        # Asignar tipos alternados (entrada/salida) por usuario por día
        registros = _asignar_tipos_alternados(registros)

        sincronizados = 0
        sin_personal = 0
        duplicados = 0
        for reg in registros:
            if reg["tipo_auto"] == "duplicado":
                duplicados += 1
                continue

            user_id_int = int(reg["user_id"]) if reg["user_id"] else None
            personal = db.query(Personal).filter(
                Personal.user_id == user_id_int
            ).first()

            if not personal:
                sin_personal += 1
                continue

            registro_existente = db.query(Asistencia).filter(
                Asistencia.personal_id == personal.id,
                Asistencia.fecha_hora == reg["timestamp"],
            ).first()

            if not registro_existente:
                nueva_asistencia = Asistencia(
                    personal_id=personal.id,
                    user_id=user_id_int,
                    tipo=reg["tipo_auto"],
                    fecha_hora=reg["timestamp"],
                    dispositivo_ip=zkteco_service.ip,
                    sincronizado="S",
                    fecha_sincronizacion=datetime.now(timezone.utc),
                )
                db.add(nueva_asistencia)
                sincronizados += 1

        db.commit()
        logger.info(f"Registros sincronizados: {sincronizados}, duplicados filtrados: {duplicados}")

        return {
            "total_sincronizados": sincronizados,
            "total_registros": len(registros),
            "duplicados_filtrados": duplicados,
            "sin_personal_asociado": sin_personal,
            "mensaje": f"Se importaron {sincronizados} registros ({duplicados} duplicados filtrados)",
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error al sincronizar registros: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/re-sincronizar-registros")
def re_sincronizar_registros(db: Session = Depends(get_db)):
    """
    Borra TODOS los registros de asistencia y los re-importa con tipos corregidos.
    Útil cuando los registros anteriores tienen tipo incorrecto.
    """
    try:
        eliminados = db.query(Asistencia).delete()
        db.commit()
        logger.info(f"Se eliminaron {eliminados} registros de asistencia para re-sincronización")

        registros = zkteco_service.obtener_registros_asistencia()
        if not registros:
            return {
                "eliminados": eliminados,
                "total_sincronizados": 0,
                "mensaje": f"Se eliminaron {eliminados} registros. No hay registros en el dispositivo para importar.",
            }

        registros = _asignar_tipos_alternados(registros)

        sincronizados = 0
        sin_personal = 0
        duplicados = 0
        for reg in registros:
            if reg["tipo_auto"] == "duplicado":
                duplicados += 1
                continue

            user_id_int = int(reg["user_id"]) if reg["user_id"] else None
            personal = db.query(Personal).filter(
                Personal.user_id == user_id_int
            ).first()

            if not personal:
                sin_personal += 1
                continue

            nueva_asistencia = Asistencia(
                personal_id=personal.id,
                user_id=user_id_int,
                tipo=reg["tipo_auto"],
                fecha_hora=reg["timestamp"],
                dispositivo_ip=zkteco_service.ip,
                sincronizado="S",
                fecha_sincronizacion=datetime.now(timezone.utc),
            )
            db.add(nueva_asistencia)
            sincronizados += 1

        db.commit()
        logger.info(f"Re-sincronización: {sincronizados} registros, {duplicados} duplicados filtrados")

        return {
            "eliminados": eliminados,
            "total_sincronizados": sincronizados,
            "total_registros": len(registros),
            "duplicados_filtrados": duplicados,
            "sin_personal_asociado": sin_personal,
            "mensaje": f"Se eliminaron {eliminados} registros, se importaron {sincronizados} ({duplicados} duplicados filtrados)",
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error en re-sincronización: {e}")
        raise HTTPException(status_code=500, detail=str(e))
