"""
Orquestador de ingesta de datos (batch) para PlaneAI UdeA.

Flujo:
  1. Intenta extraer la oferta de cursos de las fuentes oficiales (scraper.py).
  2. Si no obtiene datos, usa scraper/seed_data.json como respaldo.
  3. Persiste los datos en PostgreSQL de forma IDEMPOTENTE (no duplica al
     re-ejecutar): cursos, profesores (de-duplicados por nombre), grupos y,
     en una segunda pasada, los prerrequisitos entre cursos.

Uso (desde la raíz del proyecto):
    python -m scraper.run_scraper              # intenta scraping y cae al seed
    python -m scraper.run_scraper --solo-seed  # usa directamente el seed
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# --- Hacer visible el paquete `app` del backend (carpeta hermana) ---
_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ / "backend"))

from app.database import SessionLocal  # noqa: E402
from app.models import Curso, Grupo, Profesor  # noqa: E402

from scraper.scraper import scrape_cursos  # noqa: E402

SEED_PATH = Path(__file__).resolve().parent / "seed_data.json"


def cargar_seed() -> list[dict]:
    """Lee el dataset semilla de respaldo (seed_data.json)."""
    with open(SEED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[seed] Cargados {len(data['cursos'])} cursos desde {SEED_PATH.name}")
    return data["cursos"]


def _obtener_o_crear_profesor(db, cache: dict, info: dict | None):
    """Devuelve un Profesor existente (por nombre) o lo crea. De-duplica docentes."""
    if not info or not info.get("nombre"):
        return None
    nombre = info["nombre"]
    if nombre in cache:
        return cache[nombre]
    prof = db.query(Profesor).filter_by(nombre=nombre).first()
    if not prof:
        prof = Profesor(
            nombre=nombre,
            email=info.get("email"),
            departamento=info.get("departamento"),
        )
        db.add(prof)
        db.flush()
    cache[nombre] = prof
    return prof


def persistir(cursos_data: list[dict]) -> dict:
    """
    Inserta/actualiza los datos en la BD de forma idempotente.
    Devuelve un resumen con los conteos finales.
    """
    db = SessionLocal()
    try:
        cache_cursos: dict[str, Curso] = {}
        cache_profes: dict[str, Profesor] = {}

        # --- 1ª pasada: cursos, profesores y grupos ---
        for c in cursos_data:
            curso = db.query(Curso).filter_by(codigo=c["codigo"]).first()
            if curso is None:
                curso = Curso(codigo=c["codigo"])
                db.add(curso)
            # Establecemos/actualizamos los campos del curso.
            curso.nombre = c["nombre"]
            curso.creditos = c["creditos"]
            curso.semestre = c.get("semestre")
            curso.programa = c["programa"]
            curso.descripcion = c.get("descripcion")
            db.flush()  # asigna curso.id
            cache_cursos[c["codigo"]] = curso

            for g in c.get("grupos", []):
                prof = _obtener_o_crear_profesor(db, cache_profes, g.get("profesor"))
                grupo = (
                    db.query(Grupo)
                    .filter_by(
                        curso_id=curso.id,
                        numero=g["numero"],
                        semestre_academico=g["semestre_academico"],
                    )
                    .first()
                )
                if grupo is None:
                    grupo = Grupo(
                        curso_id=curso.id,
                        numero=g["numero"],
                        semestre_academico=g["semestre_academico"],
                    )
                    db.add(grupo)
                grupo.cupos_totales = g.get("cupos_totales", 0)
                grupo.cupos_disponibles = g.get("cupos_disponibles", 0)
                grupo.horario = g.get("horario", [])
                grupo.aula = g.get("aula")
                grupo.profesor = prof

        db.flush()

        # --- 2ª pasada: prerrequisitos (ya existen todos los cursos) ---
        for c in cursos_data:
            curso = cache_cursos[c["codigo"]]
            curso.prerrequisitos = []  # reiniciamos la relación (idempotencia)
            for cod_pre in c.get("prerrequisitos", []):
                pre = cache_cursos.get(cod_pre) or db.query(Curso).filter_by(codigo=cod_pre).first()
                if pre is not None:
                    curso.prerrequisitos.append(pre)
                else:
                    print(f"[aviso] Prerrequisito {cod_pre} de {c['codigo']} no existe; se omite.")

        db.commit()

        return {
            "cursos": db.query(Curso).count(),
            "profesores": db.query(Profesor).count(),
            "grupos": db.query(Grupo).count(),
        }

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta de cursos de PlaneAI UdeA")
    parser.add_argument(
        "--solo-seed",
        action="store_true",
        help="Omite el scraping y carga directamente el dataset semilla.",
    )
    args = parser.parse_args()

    cursos = None
    if not args.solo_seed:
        cursos = scrape_cursos()

    if not cursos:
        print("[ingesta] Usando dataset semilla de respaldo.")
        cursos = cargar_seed()
    else:
        print("[ingesta] Usando datos extraídos de la fuente oficial.")

    resumen = persistir(cursos)
    print("\n=== Ingesta completada ===")
    print(f"  Cursos     : {resumen['cursos']}")
    print(f"  Profesores : {resumen['profesores']}")
    print(f"  Grupos     : {resumen['grupos']}")


if __name__ == "__main__":
    main()
