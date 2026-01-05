"""
Servicio para comunicación con dispositivos ZKTeco
"""
from pyzkaccess import ZKAccess
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ZKTecoService:
    """Clase para manejar conexión y extracción de datos de ZKTeco"""
    
    def __init__(self):
        self.ip = settings.zkteco_ip
        self.port = settings.zkteco_port
        self.timeout = settings.zkteco_timeout
        self.zk = None
    
    def conectar(self) -> bool:
        """
        Conecta al dispositivo ZKTeco
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            self.zk = ZKAccess(self.ip, port=self.port, timeout=self.timeout)
            logger.info(f"Conectado a ZKTeco en {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Error al conectar a ZKTeco: {str(e)}")
            return False
    
    def desconectar(self):
        """Desconecta del dispositivo ZKTeco"""
        try:
            if self.zk:
                logger.info("Desconectado de ZKTeco")
        except Exception as e:
            logger.error(f"Error al desconectar: {str(e)}")
    
    def obtener_usuarios(self) -> list:
        """
        Obtiene la lista de usuarios del dispositivo
        
        Returns:
            list: Lista de usuarios con su información
        """
        try:
            if not self.zk:
                if not self.conectar():
                    return []
            
            usuarios = self.zk.get_users()
            logger.info(f"Se obtuvieron {len(usuarios)} usuarios")
            return usuarios
        except Exception as e:
            logger.error(f"Error al obtener usuarios: {str(e)}")
            return []
    
    def obtener_registros_asistencia(self) -> list:
        """
        Obtiene los registros de asistencia del dispositivo
        
        Returns:
            list: Lista de registros de entrada/salida
        """
        try:
            if not self.zk:
                if not self.conectar():
                    return []
            
            registros = self.zk.get_attendance()
            logger.info(f"Se obtuvieron {len(registros)} registros de asistencia")
            return registros
        except Exception as e:
            logger.error(f"Error al obtener registros: {str(e)}")
            return []
    
    def obtener_dispositivo_info(self) -> dict:
        """
        Obtiene información del dispositivo
        
        Returns:
            dict: Información del dispositivo
        """
        try:
            if not self.zk:
                if not self.conectar():
                    return {}
            
            info = {
                'ip': self.ip,
                'port': self.port,
                'modelo': 'ZKTeco',
                'estado': 'conectado'
            }
            return info
        except Exception as e:
            logger.error(f"Error al obtener info del dispositivo: {str(e)}")
            return {}


# Instancia global del servicio
zkteco_service = ZKTecoService()
