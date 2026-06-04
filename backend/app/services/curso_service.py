"""
Servicio de cursos: lógica de negocio para consultar cursos y grupos.

Separa las consultas a la BD de los routers (que solo manejan HTTP). Usa
`selectinload` para traer grupos, profesores y prerrequisitos en pocas
consultas y evitar el problema N+1.
"""
from sqlalchemy.orm import Session, selectinload

from app.models import Curso, Grupo


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
    """Obtiene un curso por id, con sus grupos (y profesor) y prerrequisitos."""
    return (
        db.query(Curso)
        .options(
            selectinload(Curso.grupos).selectinload(Grupo.profesor),
            selectinload(Curso.prerrequisitos),
        )
        .filter(Curso.id == curso_id)
        .first()
    )


def obtener_grupos_de_curso(db: Session, curso_id: int) -> list[Grupo]:
    """Devuelve los grupos de un curso, con su profesor cargado."""
    return (
        db.query(Grupo)
        .options(selectinload(Grupo.profesor))
        .filter(Grupo.curso_id == curso_id)
        .order_by(Grupo.numero)
        .all()
    )
