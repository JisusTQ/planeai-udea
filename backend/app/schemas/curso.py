"""
Esquemas Pydantic (DTOs) para cursos, grupos y profesores.

Estos esquemas definen el CONTRATO de la API: qué forma tienen los datos que
salen por cada endpoint. Se separan de los modelos SQLAlchemy para no exponer
la estructura interna de la BD y poder versionar la API con independencia.

`from_attributes=True` permite construir el DTO directamente desde un objeto
ORM (p. ej. CursoDetalle.model_validate(curso)).
"""
from pydantic import BaseModel, ConfigDict


class ProfesorOut(BaseModel):
    """Datos públicos de un profesor."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str | None = None
    departamento: str | None = None


class SesionHorario(BaseModel):
    """Una sesión de clase dentro del horario de un grupo."""
    dia: str
    hora_inicio: str
    hora_fin: str


class GrupoOut(BaseModel):
    """Grupo (oferta concreta) con sus cupos, horario y profesor."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    semestre_academico: str
    cupos_totales: int
    cupos_disponibles: int
    horario: list[SesionHorario] = []
    aula: str | None = None
    profesor: ProfesorOut | None = None


class CursoResumen(BaseModel):
    """Curso sin grupos: ideal para listados."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    creditos: int
    semestre: int | None = None
    programa: str


class CursoDetalle(CursoResumen):
    """Curso completo: incluye descripción, grupos y prerrequisitos."""
    descripcion: str | None = None
    grupos: list[GrupoOut] = []
    prerrequisitos: list[CursoResumen] = []
