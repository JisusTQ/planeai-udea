"""
Router de cursos: endpoints REST para consultar la oferta académica.

  GET /cursos                  -> lista de cursos (filtros: programa, semestre)
  GET /cursos/{id}             -> detalle de un curso (grupos + prerrequisitos)
  GET /cursos/{id}/grupos      -> cupos y horarios por grupo de un curso
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.curso import CursoDetalle, CursoResumen, GrupoOut
from app.services import curso_service

router = APIRouter(prefix="/cursos", tags=["Cursos"])


@router.get("", response_model=list[CursoResumen], summary="Listar cursos")
def listar_cursos(
    programa: str | None = None,
    semestre: int | None = None,
    db: Session = Depends(get_db),
):
    """Devuelve la lista de cursos, opcionalmente filtrada por programa y semestre."""
    return curso_service.listar_cursos(db, programa=programa, semestre=semestre)


@router.get("/{curso_id}", response_model=CursoDetalle, summary="Detalle de un curso")
def obtener_curso(curso_id: int, db: Session = Depends(get_db)):
    """Devuelve un curso con sus grupos (cupos, horario, profesor) y prerrequisitos."""
    curso = curso_service.obtener_curso(db, curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso


@router.get(
    "/{curso_id}/grupos",
    response_model=list[GrupoOut],
    summary="Cupos por grupo de un curso",
)
def grupos_de_curso(curso_id: int, db: Session = Depends(get_db)):
    """Devuelve los grupos de un curso con sus cupos disponibles y horarios."""
    curso = curso_service.obtener_curso(db, curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso_service.obtener_grupos_de_curso(db, curso_id)
