"""Esquemas Pydantic (DTOs) del chat conversacional."""
from pydantic import BaseModel, Field


class MensajeHistorial(BaseModel):
    rol: str  # "user" o "bot"
    texto: str


class ChatRequest(BaseModel):
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["Soy de 2do semestre, ¿qué grupos con cupo me sirven en la mañana?"],
    )
    historial: list[MensajeHistorial] = Field(default_factory=list)


class PasoAgente(BaseModel):
    """Una herramienta que el agente decidió invocar (traza del bucle)."""
    herramienta: str
    args: dict[str, str] = {}


class ChatResponse(BaseModel):
    respuesta: str
    pasos: list[PasoAgente] = []


class SugerenciasRequest(BaseModel):
    historial: list[MensajeHistorial] = Field(default_factory=list)


class SugerenciasResponse(BaseModel):
    sugerencias: list[str] = []
