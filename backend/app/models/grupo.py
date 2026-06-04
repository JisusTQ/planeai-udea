"""
Modelo Grupo: la oferta CONCRETA de un curso en un semestre académico.

Es la entidad central del dominio: conecta un Curso con un Profesor y guarda
la información operativa (cupos, horario, aula). Aquí viven los "cupos por
grupo", que es justo lo que el estudiante necesita consultar antes de matricular.
"""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Grupo(Base):
    __tablename__ = "grupos"

    id = Column(Integer, primary_key=True, index=True)

    # Número de grupo dentro del curso (p. ej. "1", "2").
    numero = Column(String(10), nullable=False)

    # Semestre académico de la oferta (p. ej. "2025-1").
    semestre_academico = Column(String(10), nullable=False, index=True)

    # --- Gestión de cupos ---
    cupos_totales = Column(Integer, nullable=False, default=0)
    cupos_disponibles = Column(Integer, nullable=False, default=0)

    # --- Horario estructurado como JSONB (tipo nativo de PostgreSQL) ---
    # Ejemplo de contenido:
    #   [{"dia": "lunes",     "hora_inicio": "08:00", "hora_fin": "10:00"},
    #    {"dia": "miercoles", "hora_inicio": "08:00", "hora_fin": "10:00"}]
    # Guardar el horario como JSONB nos permite registrar varias sesiones por
    # grupo y, más adelante, DETECTAR CHOQUES de horario al armar el plan del
    # estudiante. (Decisión de diseño: ver README, sección "Modelo de datos").
    horario = Column(JSONB, default=list)

    aula = Column(String(50))

    # --- Llaves foráneas (con ondelete a nivel de BD, coincide con schema.sql) ---
    #   · CASCADE : si se elimina el curso, se eliminan sus grupos.
    #   · SET NULL: si se elimina el profesor, el grupo queda sin docente asignado.
    curso_id = Column(
        Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profesor_id = Column(
        Integer, ForeignKey("profesores.id", ondelete="SET NULL"), index=True
    )

    # --- Relaciones ORM ---
    curso = relationship("Curso", back_populates="grupos")
    profesor = relationship("Profesor", back_populates="grupos")

    def __repr__(self) -> str:
        return f"<Grupo {self.numero} (curso_id={self.curso_id}, sem={self.semestre_academico})>"
