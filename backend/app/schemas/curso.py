"""Esquemas Pydantic (DTOs) de cursos, grupos y profesores que expone la API."""
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


class MateriaPensumOut(BaseModel):
    """Materia del pensum oficial, ubicada en su nivel (= semestre)."""
    codigo: int
    nombre: str
    nivel: int
    creditos: int
    tipo: str


class GrupoVivoOut(BaseModel):
    """Grupo obtenido EN VIVO del portal de la UdeA (profesor como texto plano)."""
    numero: str
    cupos_totales: int
    cupos_disponibles: int
    aula: str
    profesor: str
    horario: list[SesionHorario] = []


class MateriaVivaOut(BaseModel):
    """Materia de la oferta en vivo, con sus grupos del portal de la UdeA."""
    nombre: str
    codigo: str
    grupos: list[GrupoVivoOut] = []
