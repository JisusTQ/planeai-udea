"""Router del chat: POST /chat (agente) y POST /chat/sugerencias."""
from fastapi import APIRouter, HTTPException

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SugerenciasRequest,
    SugerenciasResponse,
)
from app.services import gemini_service

router = APIRouter(prefix="/chat", tags=["Chat IA"])


@router.post("", response_model=ChatResponse, summary="Conversar con PlaneAI")
def chat(peticion: ChatRequest):
    try:
        historial = [m.model_dump() for m in peticion.historial][-20:]
        respuesta, pasos = gemini_service.responder(peticion.mensaje, historial)
    except ValueError as exc:
        # API key sin configurar: 503 (configuración pendiente, no error del servidor).
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error al consultar la IA: {exc}") from exc

    return ChatResponse(respuesta=respuesta, pasos=pasos)


@router.post("/sugerencias", response_model=SugerenciasResponse, summary="Sugerencias de seguimiento")
def sugerencias(peticion: SugerenciasRequest):
    historial = [m.model_dump() for m in peticion.historial][-20:]
    return SugerenciasResponse(sugerencias=gemini_service.sugerencias(historial))
