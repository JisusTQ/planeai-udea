"""
Router de cursos: endpoints REST para consultar la oferta académica.

  GET /cursos                  -> lista de cursos del catálogo (BD)
  GET /cursos/en-vivo          -> oferta COMPLETA en vivo del portal UdeA
  GET /cursos/{id}             -> detalle de un curso (catálogo + prerrequisitos)
  GET /cursos/{id}/grupos      -> grupos/cupos/horarios EN VIVO del portal UdeA

Cambio de arquitectura: los grupos, cupos y horarios ya NO salen de la base de
datos, sino del portal oficial de Admisiones y Registro (en vivo, cacheado).
El catálogo (créditos, semestre, prerrequisitos) sí proviene de la BD.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.curso import (
    CursoDetalle,
    CursoResumen,
    GrupoVivoOut,
    MateriaPensumOut,
    MateriaVivaOut,
    ProfesorOut,
    SesionHorario,
    GrupoOut,
)
from app.services import curso_service
from app.services import udea_horarios_service as udea
from app.services import udea_pensum_service as pensum

router = APIRouter(prefix="/cursos", tags=["Cursos"])


def _sesiones(grupo) -> list[SesionHorario]:
    return [
        SesionHorario(dia=s.dia, hora_inicio=s.hora_inicio, hora_fin=s.hora_fin)
        for s in grupo.horario
    ]


@router.get("", response_model=list[CursoResumen], summary="Listar cursos")
def listar_cursos(
    programa: str | None = None,
    semestre: int | None = None,
    db: Session = Depends(get_db),
):
    """Devuelve la lista de cursos del catálogo, opcionalmente filtrada."""
    return curso_service.listar_cursos(db, programa=programa, semestre=semestre)


@router.get(
    "/en-vivo",
    response_model=list[MateriaVivaOut],
    summary="Oferta completa en vivo (portal UdeA)",
)
def oferta_en_vivo():
    """Devuelve TODA la oferta vigente (materias y grupos) consultada en vivo."""
    try:
        oferta = udea.obtener_oferta()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"No se pudo consultar el portal UdeA: {exc}"
        ) from exc

    return [
        MateriaVivaOut(
            nombre=m.nombre,
            codigo=m.codigo,
            grupos=[
                GrupoVivoOut(
                    numero=g.numero,
                    cupos_totales=g.cupos_totales,
                    cupos_disponibles=g.cupos_disponibles,
                    aula=g.aula,
                    profesor=g.profesor,
                    horario=_sesiones(g),
                )
                for g in m.grupos
            ],
        )
        for m in oferta
    ]


@router.get(
    "/pensum",
    response_model=list[MateriaPensumOut],
    summary="Pensum oficial por nivel (semestre)",
)
def pensum_oficial(nivel: int | None = None):
    """
    Devuelve las materias del pensum oficial (portal Cursum). Con `?nivel=N` filtra
    por nivel/semestre (1=primero, 2=segundo…; 99=electivas).
    """
    try:
        materias = (
            pensum.materias_por_nivel(nivel) if nivel else pensum.obtener_pensum()
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"No se pudo consultar el pensum UdeA: {exc}"
        ) from exc

    return [
        MateriaPensumOut(
            codigo=m.codigo,
            nombre=m.nombre,
            nivel=m.nivel,
            creditos=m.creditos,
            tipo=m.tipo,
        )
        for m in materias
    ]


@router.get("/{curso_id}", response_model=CursoDetalle, summary="Detalle de un curso")
def obtener_curso(curso_id: int, db: Session = Depends(get_db)):
    """Devuelve un curso con sus prerrequisitos (catálogo de la BD)."""
    curso = curso_service.obtener_curso(db, curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso


@router.get(
    "/{curso_id}/grupos",
    response_model=list[GrupoOut],
    summary="Cupos/horarios EN VIVO de un curso",
)
def grupos_de_curso(curso_id: int, db: Session = Depends(get_db)):
    """
    Devuelve los grupos de un curso con sus cupos y horarios, obtenidos EN VIVO
    del portal de la UdeA (se cruza con el catálogo por el nombre del curso).
    """
    curso = curso_service.obtener_curso(db, curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    try:
        grupos_vivos = udea.grupos_por_nombre(curso.nombre)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"No se pudo consultar el portal UdeA: {exc}"
        ) from exc

    semestre = udea.semestre_actual()
    return [
        GrupoOut(
            id=i + 1,
            numero=g.numero,
            semestre_academico=semestre,
            cupos_totales=g.cupos_totales,
            cupos_disponibles=g.cupos_disponibles,
            horario=_sesiones(g),
            aula=g.aula,
            profesor=ProfesorOut(id=0, nombre=g.profesor),
        )
        for i, g in enumerate(grupos_vivos)
    ]
