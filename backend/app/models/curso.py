"""
Modelo Curso: representa una asignatura del pensum (p. ej. "Cálculo Diferencial").

Un Curso es la entidad "catálogo": describe la materia en abstracto (su código,
nombre, créditos y a qué programa pertenece). Las ofertas concretas de cada
semestre —con su horario, cupos y profesor— se modelan aparte en la tabla Grupo.

Además, un Curso puede tener PRERREQUISITOS: otros cursos que deben aprobarse
antes de poder matricularlo. Es una relación muchos-a-muchos del Curso CONSIGO
MISMO (auto-referencial), modelada con la tabla de asociación `curso_prerrequisito`.
"""
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from app.database import Base


# --- Tabla de asociación de prerrequisitos (muchos-a-muchos sobre Curso) ---
# Cada fila significa: "el curso `curso_id` requiere haber aprobado
# `prerrequisito_id`". Al ser una tabla puente pura (solo dos llaves foráneas),
# se define como Table y no como clase de modelo.
curso_prerrequisito = Table(
    "curso_prerrequisito",
    Base.metadata,
    Column("curso_id", Integer, ForeignKey("cursos.id", ondelete="CASCADE"), primary_key=True),
    Column("prerrequisito_id", Integer, ForeignKey("cursos.id", ondelete="CASCADE"), primary_key=True),
)


class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True, index=True)

    # Código institucional UdeA de la materia (p. ej. "2521101"). Debe ser único.
    codigo = Column(String(20), unique=True, nullable=False, index=True)

    nombre = Column(String(200), nullable=False)

    # Número de créditos académicos de la materia.
    creditos = Column(Integer, nullable=False)

    # Semestre sugerido dentro del plan de estudios (1 a 10).
    semestre = Column(Integer)

    # Programa al que pertenece (p. ej. "Ingeniería de Sistemas").
    programa = Column(String(150), nullable=False, index=True)

    descripcion = Column(Text)

    # Relación 1:N -> un curso tiene muchos grupos.
    # cascade="all, delete-orphan": si se elimina el curso, se eliminan sus grupos.
    grupos = relationship(
        "Grupo",
        back_populates="curso",
        cascade="all, delete-orphan",
    )

    # Relación N:M auto-referencial -> prerrequisitos del curso.
    #   curso.prerrequisitos       -> lista de cursos que ESTE curso requiere.
    #   curso.es_prerrequisito_de  -> lista de cursos que requieren a ESTE (backref).
    # primaryjoin/secondaryjoin son necesarios porque la relación apunta a la
    # misma tabla y SQLAlchemy debe saber cuál columna es "el curso" y cuál
    # "el prerrequisito".
    prerrequisitos = relationship(
        "Curso",
        secondary=curso_prerrequisito,
        primaryjoin=id == curso_prerrequisito.c.curso_id,
        secondaryjoin=id == curso_prerrequisito.c.prerrequisito_id,
        backref="es_prerrequisito_de",
    )

    def __repr__(self) -> str:
        return f"<Curso {self.codigo} - {self.nombre}>"
