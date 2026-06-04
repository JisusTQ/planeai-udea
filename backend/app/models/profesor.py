"""
Modelo Profesor: docente que dicta uno o más grupos.

Se modela como tabla aparte (en vez de un simple texto en Grupo) para evitar
duplicar el nombre del profesor en cada grupo que dicta y para poder, más
adelante, recomendar o filtrar por profesor (normalización de datos).
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Profesor(Base):
    __tablename__ = "profesores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    email = Column(String(150))
    departamento = Column(String(150))

    # Relación 1:N -> un profesor puede dictar muchos grupos.
    grupos = relationship("Grupo", back_populates="profesor")

    def __repr__(self) -> str:
        return f"<Profesor {self.nombre}>"
