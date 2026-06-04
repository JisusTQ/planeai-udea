"""
Orquestador de ingesta de datos (batch) para PlaneAI UdeA.

Flujo:
  1. Intenta extraer el catálogo de cursos de las fuentes oficiales (scraper.py).
  2. Si no obtiene datos, usa scraper/seed_data.json como respaldo.
  3. Persiste el CATÁLOGO en PostgreSQL de forma IDEMPOTENTE (no duplica al
     re-ejecutar): cursos y, en una segunda pasada, los prerrequisitos entre
     cursos. Los grupos/horarios/cupos ya NO se guardan en la BD: se consultan
     en vivo del portal de la UdeA (app/services/udea_horarios_service).

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
from app.models import Curso  # noqa: E402

from scraper.scraper import scrape_cursos  # noqa: E402

SEED_PATH = Path(__file__).resolve().parent / "seed_data.json"


def cargar_seed() -> list[dict]:
    """Lee el dataset semilla de respaldo (seed_data.json)."""
    with open(SEED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[seed] Cargados {len(data['cursos'])} cursos desde {SEED_PATH.name}")
    return data["cursos"]


def persistir(cursos_data: list[dict]) -> dict:
    """
    Inserta/actualiza el catálogo de cursos en la BD de forma idempotente.
    Devuelve un resumen con los conteos finales.
    """
    db = SessionLocal()
    try:
        cache_cursos: dict[str, Curso] = {}

        # --- 1ª pasada: cursos ---
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

        return {"cursos": db.query(Curso).count()}

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
    print(f"  Cursos : {resumen['cursos']}")


if __name__ == "__main__":
    main()
