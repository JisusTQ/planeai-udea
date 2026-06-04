"""
Paquete de modelos ORM (SQLAlchemy).

Importamos aquí los modelos (y la tabla de asociación de prerrequisitos) para
que SQLAlchemy y Alembic los "descubran" al importar el paquete. Esto es
necesario para crear las tablas y para autogenerar las migraciones correctamente.
"""
from app.models.curso import Curso, curso_prerrequisito
from app.models.profesor import Profesor
from app.models.grupo import Grupo

__all__ = ["Curso", "Profesor", "Grupo", "curso_prerrequisito"]
