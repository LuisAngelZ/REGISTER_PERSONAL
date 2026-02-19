"""
Aplicacion principal de FastAPI
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import secrets
import uvicorn
from pathlib import Path
from app.config import settings
from app.routes import zkteco
from app.database.db import Base, engine
from app.models.usuario import Usuario  # Registrar modelo para crear tabla
from app.models.auditlog import AuditLog  # Registrar modelo audit log

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Crear aplicacion FastAPI
app = FastAPI(
    title="Sistema de Registro de Personal",
    description="API para gestion de asistencia con dispositivo ZKTeco",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS - solo origenes permitidos
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "X-CSRF-Token"],
)

# Middleware: autenticacion por API Key (solo rutas /api/)
@app.middleware("http")
async def verificar_api_key(request: Request, call_next):
    # Rutas publicas que no requieren API key
    ruta = request.url.path
    rutas_publicas = ["/", "/health", "/api/docs", "/api/redoc", "/openapi.json", "/api/auth/login", "/api/auth/registro", "/api/auth/check", "/api/sucursal", "/api/csrf-token"]
    es_estatico = ruta.startswith("/static")
    es_publica = ruta in rutas_publicas or es_estatico

    if not es_publica and settings.api_key:
        api_key = request.headers.get("X-API-Key", "")
        if api_key != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "API Key invalida o no proporcionada"}
            )

    response = await call_next(request)
    return response

# Middleware: CSRF protection para mutaciones (POST/PUT/DELETE)
_csrf_tokens: dict[str, float] = {}  # token -> timestamp
CSRF_TOKEN_MAX_AGE = 3600 * 8  # 8 horas

@app.middleware("http")
async def verificar_csrf(request: Request, call_next):
    if request.method in ("POST", "PUT", "DELETE"):
        ruta = request.url.path
        # Excluir rutas publicas de CSRF
        rutas_sin_csrf = ["/api/auth/login", "/api/auth/registro"]
        if ruta not in rutas_sin_csrf:
            csrf_token = request.headers.get("X-CSRF-Token", "")
            if not csrf_token or csrf_token not in _csrf_tokens:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token invalido o faltante"}
                )
            # Verificar expiración
            import time
            if time.time() - _csrf_tokens[csrf_token] > CSRF_TOKEN_MAX_AGE:
                del _csrf_tokens[csrf_token]
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token expirado"}
                )
    response = await call_next(request)
    return response

# Middleware: manejo global de errores
@app.middleware("http")
async def manejar_errores(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error no manejado en {request.method} {request.url.path}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

# Middleware: logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        import time
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000)
        ip = request.client.host if request.client else "-"
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms) [{ip}]")
        return response
    response = await call_next(request)
    return response

# Incluir rutas
from app.routes import personal as personal_routes
from app.routes import auth as auth_routes
app.include_router(zkteco.router)
app.include_router(personal_routes.router)
app.include_router(auth_routes.router)

# Servir archivos estaticos del frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
def read_root():
    """Endpoint raiz - sirve el frontend"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"nombre": "Sistema de Registro de Personal", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Verificar estado de la API y conexion a DB"""
    from app.database.db import SessionLocal
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check - DB error: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "database": "disconnected"})

@app.get("/api/csrf-token")
def obtener_csrf_token():
    """Genera un CSRF token para proteger operaciones de escritura"""
    import time
    # Limpiar tokens expirados (max 1000)
    ahora = time.time()
    expirados = [t for t, ts in _csrf_tokens.items() if ahora - ts > CSRF_TOKEN_MAX_AGE]
    for t in expirados:
        del _csrf_tokens[t]
    token = secrets.token_hex(32)
    _csrf_tokens[token] = ahora
    return {"csrf_token": token}

@app.get("/api/sucursal")
def info_sucursal():
    """Retorna informacion de la sucursal"""
    return {"nombre": settings.sucursal_nombre}

@app.get("/api/audit-log")
def obtener_audit_log(limit: int = 50, skip: int = 0):
    """Obtener los ultimos registros del historial de cambios"""
    from app.database.db import SessionLocal
    limit = max(1, min(limit, 200))
    skip = max(0, skip)
    db = SessionLocal()
    try:
        registros = db.query(AuditLog).order_by(AuditLog.fecha.desc()).offset(skip).limit(limit).all()
        total = db.query(AuditLog).count()
        return {
            "total": total,
            "registros": [
                {
                    "id": r.id,
                    "accion": r.accion,
                    "entidad": r.entidad,
                    "entidad_id": r.entidad_id,
                    "detalle": r.detalle,
                    "usuario": r.usuario,
                    "ip": r.ip,
                    "fecha": r.fecha.isoformat() if r.fecha else None,
                }
                for r in registros
            ]
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
