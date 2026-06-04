"""
Router de cursos: endpoints REST sobre datos EN VIVO de la UdeA (sin base de datos).

  GET /cursos                  -> catálogo (pensum) por nivel/semestre
  GET /cursos/en-vivo          -> oferta COMPLETA en vivo (todas las materias)
  GET /cursos/{codigo}/grupos  -> grupos/cupos/horarios EN VIVO de una materia

El catálogo proviene del pensum oficial (portal Cursum) y los grupos/horarios del
portal de Admisiones y Registro. Ambos comparten el mismo código de materia, así
que el cruce es exacto.
"""
from fastapi import APIRouter, HTTPException

from app.schemas.curso import (
    GrupoOut,
    MateriaPensumOut,
    MateriaVivaOut,
    GrupoVivoOut,
    ProfesorOut,
    SesionHorario,
)
from app.services import udea_horarios_service as udea
from app.services import udea_pensum_service as pensum

router = APIRouter(prefix="/cursos", tags=["Cursos"])


def _sesiones(grupo) -> list[SesionHorario]:
    return [
        SesionHorario(dia=s.dia, hora_inicio=s.hora_inicio, hora_fin=s.hora_fin)
        for s in grupo.horario
    ]


@router.get("", response_model=list[MateriaPensumOut], summary="Catálogo de cursos (pensum)")
def listar_cursos(nivel: int | None = None):
    """
    Catálogo de materias del programa, tomado del pensum oficial en vivo.
    Con `?nivel=N` filtra por nivel/semestre (1=primero…; 99=electivas).
    """
    try:
        materias = pensum.materias_por_nivel(nivel) if nivel else pensum.obtener_pensum()
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
    "/{codigo}/grupos",
    response_model=list[GrupoOut],
    summary="Cupos/horarios EN VIVO de una materia",
)
def grupos_de_curso(codigo: str):
    """
    Grupos de una materia (por su código) con cupos y horarios, EN VIVO del portal
    de la UdeA. El código es el mismo del catálogo/pensum.
    """
    try:
        grupos_vivos = udea.grupos_por_codigo(codigo)
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
