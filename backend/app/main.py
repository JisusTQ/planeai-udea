"""
Punto de entrada de la API de PlaneAI UdeA.

Al arrancar precalienta en segundo plano las consultas al pensum y a la oferta
de la UdeA, para que la primera petición del usuario no sea lenta.

Ejecutar:  uvicorn app.main:app --reload
"""
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, cursos
from app.services import udea_horarios_service as udea
from app.services import udea_pensum_service as pensum

settings = get_settings()


def _precalentar():
    for cargar in (pensum.obtener_pensum, udea.obtener_oferta):
        try:
            cargar()
        except Exception:
            pass  # si un portal no responde al arrancar, se reintenta on-demand


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_precalentar, daemon=True).start()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Asistente de planeación académica para la Facultad de Ingeniería UdeA.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


app.include_router(cursos.router)
app.include_router(chat.router)
