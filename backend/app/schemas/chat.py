"""
Esquemas Pydantic (DTOs) para el endpoint de chat conversacional.
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Mensaje que envía el estudiante al asistente."""
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Pregunta o petición del estudiante en lenguaje natural.",
        examples=["Soy de 2do semestre, ¿qué grupos con cupo me sirven en la mañana?"],
    )


class ChatResponse(BaseModel):
    """Respuesta generada por el asistente (Gemini) usando los datos de la BD."""
    respuesta: str
    cursos_considerados: int = Field(
        ...,
        description="Cantidad de cursos de la BD que se enviaron como contexto a la IA.",
    )
