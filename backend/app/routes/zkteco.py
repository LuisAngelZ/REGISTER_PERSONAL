"""
Rutas para integración con dispositivo ZKTeco
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.zkteco_service import zkteco_service
from app.database.db import get_db
from app.models.personal import Personal
from app.models.asistencia import Asistencia
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zkteco", tags=["ZKTeco"])

@router.post("/configurar-ip")
def configurar_ip(ip: str, puerto: int = 4370):
    """
    Configurar IP del dispositivo ZKTeco
    """
    try:
        # Aquí actualizarías la configuración de forma dinámica
        zkteco_service.ip = ip
        zkteco_service.port = puerto
        logger.info(f"IP configurada: {ip}:{puerto}")
        return {
            "status": "configurado",
            "ip": ip,
            "puerto": puerto,
            "mensaje": "Dispositivo configurado correctamente"
        }
    except Exception as e:
        logger.error(f"Error al configurar IP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-conexion")
def test_conexion(ip: str = None, puerto: int = 4370):
    """
    Prueba la conexión con el dispositivo ZKTeco
    """
    try:
        # Si se proporciona IP, configúrala
        if ip:
            zkteco_service.ip = ip
            zkteco_service.port = puerto
        
        if zkteco_service.conectar():
            info = zkteco_service.obtener_dispositivo_info()
            zkteco_service.desconectar()
            return {
                "status": "conectado",
                "mensaje": "Conexión exitosa",
                "info": info
            }
        else:
            raise HTTPException(status_code=503, detail="No se pudo conectar al dispositivo")
    except Exception as e:
        logger.error(f"Error en test_conexion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usuarios")
def obtener_usuarios(ip: str = None, puerto: int = 4370):
    """
    Obtiene la lista de usuarios del dispositivo ZKTeco
    """
    try:
        if ip:
            zkteco_service.ip = ip
            zkteco_service.port = puerto
            
        usuarios = zkteco_service.obtener_usuarios()
        if not usuarios:
            raise HTTPException(status_code=404, detail="No se encontraron usuarios")
        
        usuarios_formateados = []
        for usuario in usuarios:
            usuarios_formateados.append({
                "user_id": usuario.user_id,
                "nombre": usuario.name,
                "carnet": usuario.badge,
                "privilegio": usuario.privilege
            })
        
        return {
            "total": len(usuarios_formateados),
            "usuarios": usuarios_formateados
        }
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sincronizar-usuarios")
def sincronizar_usuarios(ip: str = None, puerto: int = 4370, db: Session = Depends(get_db)):
    """
    Sincroniza usuarios del dispositivo con la base de datos
    """
    try:
        if ip:
            zkteco_service.ip = ip
            zkteco_service.port = puerto
            
        usuarios = zkteco_service.obtener_usuarios()
        if not usuarios:
            return {"total_sincronizados": 0, "mensaje": "No hay usuarios en el dispositivo"}
        
        sincronizados = 0
        for usuario in usuarios:
            # Verificar si el usuario ya existe
            personal_existente = db.query(Personal).filter(
                Personal.user_id == usuario.user_id
            ).first()
            
            if not personal_existente:
                # Crear nuevo personal
                nuevo_personal = Personal(
                    user_id=usuario.user_id,
                    nombre=usuario.name,
                    apellido="",
                    documento=str(usuario.badge),
                    puesto="Sin especificar",
                    departamento="Sin especificar"
                )
                db.add(nuevo_personal)
                sincronizados += 1
        
        db.commit()
        logger.info(f"Usuarios sincronizados: {sincronizados}")
        
        return {
            "total_sincronizados": sincronizados,
            "total_usuarios": len(usuarios),
            "mensaje": f"Se sincronizaron {sincronizados} usuarios nuevos"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error al sincronizar usuarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/registros-asistencia")
def obtener_registros(ip: str = None, puerto: int = 4370):
    """
    Obtiene los registros de asistencia del dispositivo
    """
    try:
        if ip:
            zkteco_service.ip = ip
            zkteco_service.port = puerto
            
        registros = zkteco_service.obtener_registros_asistencia()
        if not registros:
            raise HTTPException(status_code=404, detail="No se encontraron registros")
        
        registros_formateados = []
        for registro in registros:
            registros_formateados.append({
                "user_id": registro.user_id,
                "timestamp": registro.timestamp.isoformat() if hasattr(registro, 'timestamp') else None,
                "status": registro.status  # 0=Entrada, 1=Salida
            })
        
        return {
            "total": len(registros_formateados),
            "registros": registros_formateados
        }
    except Exception as e:
        logger.error(f"Error al obtener registros: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sincronizar-registros")
def sincronizar_registros(ip: str = None, puerto: int = 4370, db: Session = Depends(get_db)):
    """
    Sincroniza registros de asistencia del dispositivo con la base de datos
    """
    try:
        if ip:
            zkteco_service.ip = ip
            zkteco_service.port = puerto
            
        registros = zkteco_service.obtener_registros_asistencia()
        if not registros:
            return {"total_sincronizados": 0, "mensaje": "No hay registros en el dispositivo"}
        
        sincronizados = 0
        for registro in registros:
            # Obtener el personal asociado al user_id
            personal = db.query(Personal).filter(
                Personal.user_id == registro.user_id
            ).first()
            
            if personal:
                # Verificar si el registro ya existe (evitar duplicados)
                registro_existente = db.query(Asistencia).filter(
                    Asistencia.personal_id == personal.id,
                    Asistencia.fecha_hora == registro.timestamp,
                    Asistencia.tipo == ('entrada' if registro.status == 0 else 'salida')
                ).first()
                
                if not registro_existente:
                    tipo = 'entrada' if registro.status == 0 else 'salida'
                    nueva_asistencia = Asistencia(
                        personal_id=personal.id,
                        user_id=registro.user_id,
                        tipo=tipo,
                        fecha_hora=registro.timestamp,
                        dispositivo_ip=zkteco_service.ip,
                        sincronizado='S'
                    )
                    db.add(nueva_asistencia)
                    sincronizados += 1
        
        db.commit()
        logger.info(f"Registros sincronizados: {sincronizados}")
        
        return {
            "total_sincronizados": sincronizados,
            "total_registros": len(registros),
            "mensaje": f"Se sincronizaron {sincronizados} registros de asistencia"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error al sincronizar registros: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
