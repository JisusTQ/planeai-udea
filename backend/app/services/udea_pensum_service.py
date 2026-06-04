"""
Pensum oficial de Ingeniería de Sistemas desde el portal Cursum.

Las materias se organizan por NIVEL (= semestre). El agente lo usa para saber
qué materias corresponden a un semestre antes de revisar cupos/horarios.

API:  GET {BASE}/programas -> versión vigente; GET {BASE}/pensum/{prog}/{ver}.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.services.udea_horarios_service import crear_sesion

_BASE = "https://wsingenieria.udea.edu.co:8094/cursum/ingenieria"
_ORIGIN = "https://ingenieria2.udea.edu.co"
PROGRAMA_ID = 504  # INGENIERÍA DE SISTEMAS
_TIMEOUT = 30

CACHE_TTL_SEGUNDOS = 3600  # 1 hora (el plan de estudios es muy estable)

# Nivel especial que el portal usa para las electivas / banco de materias.
NIVEL_ELECTIVAS = 99


@dataclass
class Requisito:
    codigo: int          # código de la materia requisito
    tipo: str            # "PRERREQ" (prerrequisito) o "CORREQ" (correquisito)


@dataclass
class MateriaPensum:
    codigo: int
    nombre: str
    nivel: int
    creditos: int
    tipo: str
    requisitos: list[Requisito] = field(default_factory=list)


_cache: dict = {"datos": None, "ts": 0.0, "version": None}


def _version_actual(sesion) -> int:
    """Obtiene la versión vigente del pensum del programa desde /programas."""
    r = sesion.get(f"{_BASE}/programas", headers={"Origin": _ORIGIN}, timeout=_TIMEOUT)
    r.raise_for_status()
    for p in r.json():
        if p.get("codigo") == PROGRAMA_ID:
            return int(p["versionActual"])
    raise RuntimeError(f"No se encontró el programa {PROGRAMA_ID} en el portal Cursum.")


def _descargar() -> tuple[list[MateriaPensum], int]:
    sesion = crear_sesion()
    version = _version_actual(sesion)
    r = sesion.get(
        f"{_BASE}/pensum/{PROGRAMA_ID}/{version}",
        headers={"Origin": _ORIGIN},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()

    materias = [
        MateriaPensum(
            codigo=int(x["materia"]),
            nombre=(x.get("nombreMateria") or "").strip(),
            nivel=int(x.get("nivel") or 0),
            creditos=int(x.get("creditos") or 0),
            tipo=(x.get("tipoMateria") or "").strip(),
            requisitos=[
                Requisito(
                    codigo=int(req["materiaRequisito"]),
                    tipo=(req.get("tipoRequisito") or "").strip(),
                )
                for req in (x.get("requisitos") or [])
                if req.get("materiaRequisito")
            ],
        )
        for x in r.json()
    ]
    return materias, version


def obtener_pensum(forzar: bool = False) -> list[MateriaPensum]:
    """Devuelve el pensum completo (usando la caché si sigue vigente)."""
    ahora = time.monotonic()
    if (
        not forzar
        and _cache["datos"] is not None
        and (ahora - _cache["ts"]) < CACHE_TTL_SEGUNDOS
    ):
        return _cache["datos"]

    datos, version = _descargar()
    _cache.update(datos=datos, ts=ahora, version=version)
    return datos


def version_actual() -> int | None:
    """Versión del pensum cargada en caché (None si aún no se consultó)."""
    return _cache["version"]


def materias_por_nivel(nivel: int) -> list[MateriaPensum]:
    """Materias de un nivel (= semestre). Para electivas usar NIVEL_ELECTIVAS (99)."""
    return [m for m in obtener_pensum() if m.nivel == nivel]


def niveles_disponibles() -> list[int]:
    """Niveles (semestres) presentes en el pensum, ordenados."""
    return sorted({m.nivel for m in obtener_pensum()})


def catalogo_por_codigo() -> dict[int, MateriaPensum]:
    """Índice {código -> materia} para resolver requisitos por su código."""
    return {m.codigo: m for m in obtener_pensum()}


def nombre_de(codigo: int) -> str:
    """Nombre de una materia dado su código (o el código como texto si no existe)."""
    materia = catalogo_por_codigo().get(codigo)
    return materia.nombre if materia else str(codigo)
