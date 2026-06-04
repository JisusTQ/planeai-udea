"""
Servicio del PENSUM oficial (plan de estudios) desde el portal Cursum de la
Facultad de Ingeniería de la UdeA.

Entrega, para el programa de Ingeniería de Sistemas, las materias organizadas
por NIVEL (cada nivel equivale a un semestre: nivel 1 = semestre 1, etc.).
El asistente lo usa para saber QUÉ materias corresponden a un semestre antes de
revisar sus cupos/horarios en vivo.

API (descubierta desde la SPA https://ingenieria2.udea.edu.co/cursum):
    GET {BASE}/programas            -> lista de programas (incluye versionActual)
    GET {BASE}/pensum/{prog}/{ver}  -> materias del pensum de esa versión

El pensum cambia muy rara vez, así que se cachea por más tiempo que la oferta.
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
class MateriaPensum:
    codigo: int
    nombre: str
    nivel: int
    creditos: int
    tipo: str
    requisitos: list = field(default_factory=list)


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
            requisitos=x.get("requisitos") or [],
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
