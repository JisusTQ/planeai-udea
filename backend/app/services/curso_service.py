"""
Servicio de cursos: lógica de negocio para consultar el catálogo de cursos.

Separa las consultas a la BD de los routers (que solo manejan HTTP). Usa
`selectinload` para traer los prerrequisitos en pocas consultas y evitar el
problema N+1. Los grupos/horarios/cupos NO se consultan aquí: vienen en vivo
del portal de la UdeA (ver app/services/udea_horarios_service).
"""
from sqlalchemy.orm import Session, selectinload

from app.models import Curso


def listar_cursos(
    db: Session,
    programa: str | None = None,
    semestre: int | None = None,
) -> list[Curso]:
    """Lista cursos, con filtros opcionales por programa y semestre."""
    query = db.query(Curso)
    if programa:
        query = query.filter(Curso.programa == programa)
    if semestre is not None:
        query = query.filter(Curso.semestre == semestre)
    return query.order_by(Curso.semestre, Curso.nombre).all()


def obtener_curso(db: Session, curso_id: int) -> Curso | None:
    """Obtiene un curso por id, con sus prerrequisitos."""
    return (
        db.query(Curso)
        .options(selectinload(Curso.prerrequisitos))
        .filter(Curso.id == curso_id)
        .first()
    )
