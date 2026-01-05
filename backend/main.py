"""
Aplicación principal de FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import uvicorn
from pathlib import Path
from app.config import settings
from app.routes import zkteco
from app.database.db import Base, engine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Registro de Personal",
    description="API para gestión de asistencia con dispositivo ZKTeco",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
from app.routes import personal as personal_routes
app.include_router(zkteco.router)
app.include_router(personal_routes.router)

# Servir archivos estáticos del frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
def read_root():
    """Endpoint raíz - redirige al frontend"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {
        "nombre": "Sistema de Registro de Personal",
        "version": "1.0.0",
        "estado": "activo"
    }

@app.get("/health")
def health_check():
    """Verificar estado de la API"""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
