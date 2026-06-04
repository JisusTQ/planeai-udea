"""
Router del chat conversacional.

  POST /chat  -> recibe el mensaje del estudiante, consulta la oferta en la BD,
                 se la pasa a Gemini como contexto y devuelve la recomendación.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import gemini_service

router = APIRouter(prefix="/chat", tags=["Chat IA"])


@router.post("", response_model=ChatResponse, summary="Conversar con PlaneAI")
def chat(peticion: ChatRequest, db: Session = Depends(get_db)):
    """
    Procesa el mensaje del estudiante:
    1. Construye el contexto con los cursos reales de la BD.
    2. Lo envía a Gemini junto con la pregunta.
    3. Devuelve la respuesta del asistente.
    """
    try:
        respuesta, num_cursos = gemini_service.responder(db, peticion.mensaje)
    except ValueError as exc:
        # API key no configurada -> 503 Service Unavailable (config pendiente).
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — error al llamar a Gemini
        raise HTTPException(
            status_code=502,
            detail=f"Error al consultar el modelo de IA: {exc}",
        ) from exc

    return ChatResponse(respuesta=respuesta, cursos_considerados=num_cursos)
