"""
Rutas de autenticacion - login/registro de usuarios del sistema
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from app.database.db import get_db
from app.models.usuario import Usuario
from passlib.context import CryptContext
import hashlib
import hmac
import re
import logging

router = APIRouter(prefix="/api/auth", tags=["Auth"])
logger = logging.getLogger("auth")

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MIN_PASSWORD_LENGTH = 8
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 60

# Rate limiting simple: {ip: [timestamp, timestamp, ...]}
_login_attempts: dict[str, list[float]] = {}


def _check_rate_limit(ip: str) -> bool:
    """Retorna True si el IP excedio el limite de intentos"""
    import time
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    # Limpiar intentos fuera de la ventana
    attempts = [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_attempt(ip: str):
    """Registra un intento de login"""
    import time
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(time.time())


def hash_password(password: str) -> str:
    """Hash con bcrypt"""
    return _pwd_context.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica password. Soporta bcrypt (nuevo) y SHA-256+salt (legado)."""
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        return _pwd_context.verify(password, stored_hash)
    # Legado: salt:sha256hex
    try:
        salt, hashed = stored_hash.split(":", 1)
        computed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return hmac.compare_digest(computed, hashed)
    except Exception:
        return False


def _registrar_audit(db: Session, accion: str, entidad: str, entidad_id: int = None, detalle: str = None):
    """Registra una entrada en el audit log"""
    from app.models.auditlog import AuditLog
    try:
        db.add(AuditLog(accion=accion, entidad=entidad, entidad_id=entidad_id, detalle=detalle))
        db.commit()
    except Exception:
        pass


USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.\-]+$")


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validar_username(cls, v):
        v = v.strip()
        if not v or len(v) > 50:
            raise ValueError("Username debe tener entre 1 y 50 caracteres")
        if not USERNAME_REGEX.match(v):
            raise ValueError("Username solo permite letras, numeros, guion, punto y underscore")
        return v

    @field_validator("password")
    @classmethod
    def validar_password(cls, v):
        if len(v) > 128:
            raise ValueError("Password no puede exceder 128 caracteres")
        return v


class RegistroRequest(BaseModel):
    username: str
    password: str
    nombre: str
    rol: str = "operador"

    @field_validator("username")
    @classmethod
    def validar_username(cls, v):
        v = v.strip()
        if not v or len(v) > 50:
            raise ValueError("Username debe tener entre 1 y 50 caracteres")
        if not USERNAME_REGEX.match(v):
            raise ValueError("Username solo permite letras, numeros, guion, punto y underscore")
        return v

    @field_validator("password")
    @classmethod
    def validar_password(cls, v):
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
        if len(v) > 128:
            raise ValueError("Password no puede exceder 128 caracteres")
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v):
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("Nombre debe tener entre 1 y 100 caracteres")
        return v

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v):
        if v not in ("admin", "operador"):
            raise ValueError("Rol debe ser 'admin' u 'operador'")
        return v


@router.post("/login")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesion"""
    ip = request.client.host if request.client else "unknown"

    # Rate limiting: max 5 intentos por minuto por IP
    if _check_rate_limit(ip):
        logger.warning(f"Rate limit excedido para IP {ip} (login '{data.username}')")
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera 1 minuto.")

    usuario = db.query(Usuario).filter(
        Usuario.username == data.username,
        Usuario.activo == True
    ).first()

    if not usuario or not verify_password(data.password, usuario.password_hash):
        _record_attempt(ip)
        logger.warning(f"Login fallido para '{data.username}' desde {ip}")
        raise HTTPException(status_code=401, detail="Usuario o password incorrectos")

    logger.info(f"Login exitoso: '{data.username}' (id={usuario.id}) desde {ip}")
    _registrar_audit(db, "login", "usuario", usuario.id, f"{data.username} desde {ip}")
    return {
        "status": "ok",
        "usuario": {
            "id": usuario.id,
            "username": usuario.username,
            "nombre": usuario.nombre,
            "rol": usuario.rol,
        }
    }


@router.post("/registro")
def registro(request: Request, data: RegistroRequest, db: Session = Depends(get_db)):
    """Registrar nuevo usuario del sistema"""
    ip = request.client.host if request.client else "unknown"
    existente = db.query(Usuario).filter(Usuario.username == data.username).first()
    if existente:
        logger.warning(f"Registro fallido: username '{data.username}' duplicado desde {ip}")
        raise HTTPException(status_code=400, detail="El username ya existe")

    nuevo = Usuario(
        username=data.username,
        password_hash=hash_password(data.password),
        nombre=data.nombre,
        rol=data.rol,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    logger.info(f"Usuario registrado: '{data.username}' (id={nuevo.id}, rol={data.rol}) desde {ip}")
    _registrar_audit(db, "registro", "usuario", nuevo.id, f"{data.username} ({data.rol}) desde {ip}")
    return {
        "status": "ok",
        "mensaje": f"Usuario '{data.username}' creado exitosamente",
        "usuario": {
            "id": nuevo.id,
            "username": nuevo.username,
            "nombre": nuevo.nombre,
            "rol": nuevo.rol,
        }
    }


@router.get("/check")
def check_auth_required(db: Session = Depends(get_db)):
    """Verifica si hay usuarios registrados (si no hay, no requiere login)"""
    total = db.query(Usuario).filter(Usuario.activo == True).count()
    return {"auth_required": total > 0, "total_usuarios": total}


class CambiarPasswordRequest(BaseModel):
    username: str
    password_actual: str
    password_nuevo: str

    @field_validator("password_nuevo")
    @classmethod
    def validar_password_nuevo(cls, v):
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
        if len(v) > 128:
            raise ValueError("Password no puede exceder 128 caracteres")
        return v


@router.put("/cambiar-password")
def cambiar_password(request: Request, data: CambiarPasswordRequest, db: Session = Depends(get_db)):
    """Cambiar password de un usuario"""
    ip = request.client.host if request.client else "unknown"
    usuario = db.query(Usuario).filter(
        Usuario.username == data.username,
        Usuario.activo == True
    ).first()
    if not usuario or not verify_password(data.password_actual, usuario.password_hash):
        logger.warning(f"Cambio de password fallido para '{data.username}' desde {ip}")
        raise HTTPException(status_code=401, detail="Usuario o password actual incorrecto")

    usuario.password_hash = hash_password(data.password_nuevo)
    db.commit()
    logger.info(f"Password cambiado para '{data.username}' desde {ip}")
    _registrar_audit(db, "cambiar_password", "usuario", usuario.id, f"{data.username} desde {ip}")
    return {"status": "ok", "mensaje": "Password actualizado correctamente"}


@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    """Lista todos los usuarios del sistema"""
    usuarios = db.query(Usuario).order_by(Usuario.fecha_creacion.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "nombre": u.nombre,
            "rol": u.rol,
            "activo": u.activo,
            "fecha_creacion": u.fecha_creacion.isoformat() if u.fecha_creacion else None,
        }
        for u in usuarios
    ]


@router.delete("/usuarios/{usuario_id}")
def desactivar_usuario(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    """Desactiva un usuario del sistema"""
    ip = request.client.host if request.client else "unknown"
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Proteger: no desactivar si es el unico admin activo
    if usuario.rol == "admin":
        admins_activos = db.query(Usuario).filter(
            Usuario.rol == "admin", Usuario.activo == True
        ).count()
        if admins_activos <= 1:
            raise HTTPException(status_code=400, detail="No se puede desactivar el unico administrador activo")

    usuario.activo = False
    db.commit()
    logger.info(f"Usuario desactivado: '{usuario.username}' (id={usuario_id}) desde {ip}")
    _registrar_audit(db, "desactivar", "usuario", usuario_id, f"{usuario.username} desde {ip}")
    return {"status": "ok", "mensaje": f"Usuario '{usuario.username}' desactivado"}
