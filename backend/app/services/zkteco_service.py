"""
Servicio para comunicación con dispositivos biométricos ZKTeco
Usa la librería pyzk (protocolo ZK sobre UDP/TCP puerto 4370)
"""
from zk import ZK
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ZKTecoService:
    """Maneja conexión y operaciones con dispositivos ZKTeco de asistencia"""

    def __init__(self):
        self.ip = settings.zkteco_ip
        self.port = settings.zkteco_port
        self.timeout = settings.zkteco_timeout
        self.password = settings.zkteco_password
        self._conn = None

    def conectar(self):
        """
        Conecta al dispositivo ZKTeco.
        Retorna la conexión activa o lanza excepción.
        Intenta con ommit_ping=True si el primer intento falla.
        """
        try:
            self.desconectar()
            # Primer intento: con ommit_ping para evitar fallo de ping en Windows
            zk = ZK(self.ip, port=self.port, timeout=self.timeout, password=self.password,
                     force_udp=False, ommit_ping=True)
            self._conn = zk.connect()
            logger.info(f"Conectado a ZKTeco en {self.ip}:{self.port}")
            return self._conn
        except Exception as e:
            self._conn = None
            logger.error(f"Error al conectar a ZKTeco {self.ip}:{self.port}: {e}")
            raise ConnectionError(f"No se pudo conectar al dispositivo en {self.ip}:{self.port} - {e}")

    def desconectar(self):
        """Desconecta del dispositivo ZKTeco"""
        if self._conn:
            try:
                self._conn.disconnect()
            except Exception:
                pass
            finally:
                self._conn = None

    def obtener_dispositivo_info(self) -> dict:
        """Obtiene información detallada del dispositivo"""
        conn = self.conectar()
        try:
            conn.read_sizes()
            info = {
                "ip": self.ip,
                "port": self.port,
                "serial_number": conn.get_serialnumber(),
                "firmware": conn.get_firmware_version(),
                "plataforma": conn.get_platform(),
                "nombre_dispositivo": conn.get_device_name(),
                "mac": conn.get_mac(),
                "usuarios_registrados": conn.users,
                "huellas_registradas": conn.fingers,
                "registros_asistencia": conn.records,
                "capacidad_usuarios": conn.users_cap,
                "capacidad_huellas": conn.fingers_cap,
                "estado": "conectado",
            }
            return info
        finally:
            self.desconectar()

    def obtener_usuarios(self) -> list:
        """
        Obtiene la lista de usuarios del dispositivo.
        Retorna lista de dicts con datos del usuario.
        """
        conn = self.conectar()
        try:
            conn.disable_device()
            usuarios_raw = conn.get_users()
            conn.enable_device()

            usuarios = []
            for u in usuarios_raw:
                usuarios.append({
                    "uid": u.uid,
                    "user_id": u.user_id,
                    "nombre": u.name,
                    "privilegio": u.privilege,
                    "password": u.password,
                    "group_id": u.group_id,
                    "card": u.card,
                })
            logger.info(f"Se obtuvieron {len(usuarios)} usuarios del dispositivo")
            return usuarios
        finally:
            self.desconectar()

    def obtener_registros_asistencia(self) -> list:
        """
        Obtiene los registros de asistencia del dispositivo.
        Retorna lista de dicts con datos de asistencia.
        """
        conn = self.conectar()
        try:
            conn.disable_device()
            registros_raw = conn.get_attendance()
            conn.enable_device()

            registros = []
            for r in registros_raw:
                registros.append({
                    "user_id": r.user_id,
                    "timestamp": r.timestamp,
                    "status": r.status,  # 0=Entrada, 1=Salida, 2=Break-Out, 3=Break-In
                    "punch": r.punch,    # 0=Huella, 1=Password, 2=Tarjeta
                })
            logger.info(f"Se obtuvieron {len(registros)} registros de asistencia")
            return registros
        finally:
            self.desconectar()

    def registrar_usuario(self, uid: int, name: str, privilege: int = 0,
                          password: str = "", user_id: str = "", card: int = 0) -> bool:
        """
        Registra/actualiza un usuario en el dispositivo.
        privilege: 0=Usuario, 14=Admin
        """
        conn = self.conectar()
        try:
            conn.disable_device()
            conn.set_user(
                uid=uid,
                name=name,
                privilege=privilege,
                password=password,
                user_id=str(user_id) if user_id else str(uid),
                card=card,
            )
            conn.enable_device()
            logger.info(f"Usuario registrado en dispositivo: uid={uid}, name={name}")
            return True
        finally:
            self.desconectar()

    def eliminar_usuario(self, uid: int) -> bool:
        """Elimina un usuario del dispositivo por su uid"""
        conn = self.conectar()
        try:
            conn.disable_device()
            conn.delete_user(uid=uid)
            conn.enable_device()
            logger.info(f"Usuario eliminado del dispositivo: uid={uid}")
            return True
        finally:
            self.desconectar()

    def test_conexion(self) -> dict:
        """Prueba la conexión al dispositivo y retorna info básica"""
        try:
            info = self.obtener_dispositivo_info()
            return {"conectado": True, "info": info}
        except ConnectionError as e:
            return {"conectado": False, "error": str(e)}


zkteco_service = ZKTecoService()
