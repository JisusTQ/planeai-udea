"""Router del chat: POST /chat entrega el mensaje al agente Gemini."""
from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import gemini_service

router = APIRouter(prefix="/chat", tags=["Chat IA"])


@router.post("", response_model=ChatResponse, summary="Conversar con PlaneAI")
def chat(peticion: ChatRequest):
    try:
        respuesta = gemini_service.responder(peticion.mensaje)
    except ValueError as exc:
        # API key sin configurar: 503 (configuración pendiente, no error del servidor).
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error al consultar la IA: {exc}") from exc

    return ChatResponse(respuesta=respuesta)
