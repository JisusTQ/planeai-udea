"""
Router del chat conversacional.

  POST /chat  -> recibe el mensaje del estudiante y lo entrega al agente Gemini,
                 que consulta EN VIVO el pensum y los cupos de la UdeA y responde.
"""
from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import gemini_service

router = APIRouter(prefix="/chat", tags=["Chat IA"])


@router.post("", response_model=ChatResponse, summary="Conversar con PlaneAI")
def chat(peticion: ChatRequest):
    """
    Procesa el mensaje del estudiante con el agente:
    1. Gemini decide qué herramientas usar (pensum / cupos en vivo).
    2. Devuelve la recomendación basada en datos reales.
    """
    try:
        respuesta = gemini_service.responder(peticion.mensaje)
    except ValueError as exc:
        # API key no configurada -> 503 Service Unavailable (config pendiente).
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — error al llamar a Gemini o a los portales
        raise HTTPException(
            status_code=502,
            detail=f"Error al consultar el modelo de IA: {exc}",
        ) from exc

    return ChatResponse(respuesta=respuesta)
