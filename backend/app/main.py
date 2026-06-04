"""
Punto de entrada de la API de PlaneAI UdeA.

Crea la aplicación FastAPI, configura CORS para que el frontend (React + Vite)
pueda consumirla, y registrará los routers. En esta fase inicial solo se expone
un endpoint de salud (/health); los routers de cursos y chat se conectarán en
las siguientes fases del proyecto.

Ejecutar en desarrollo:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, cursos

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Asistente de planeación académica para la Facultad de Ingeniería UdeA.",
    version="0.1.0",
)

# CORS: permite que el frontend (otro origen, p. ej. http://localhost:5173)
# consuma esta API sin ser bloqueado por el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Sistema"])
def health_check():
    """Endpoint de salud: confirma que la API está en funcionamiento."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


# --- Routers ---
app.include_router(cursos.router)
app.include_router(chat.router)
