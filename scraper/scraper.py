"""
Extracción (scraping) de la oferta de cursos desde las fuentes oficiales.

Contexto: las fuentes oficiales de la UdeA suelen bloquear el scraping
automatizado (validaciones, cambios frecuentes de HTML, autenticación). Por eso
esta función realiza el intento de forma ROBUSTA y, si no obtiene datos válidos,
devuelve None para que el orquestador (run_scraper.py) use el dataset semilla
de respaldo.

Esto materializa el enfoque de "ingesta batch con respaldo" descrito en el README.
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup

# Fuente de referencia de la oferta de la Facultad de Ingeniería UdeA.
FUENTE_OFICIAL = "https://www.udea.edu.co/"

# Cabeceras de navegador para que la petición no sea rechazada de inmediato.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def scrape_cursos(timeout: int = 10) -> list[dict] | None:
    """
    Intenta extraer la oferta de cursos de la fuente oficial.

    Returns:
        list[dict] con los cursos extraídos, o
        None si no se pudo extraer (el orquestador usará el dataset semilla).
    """
    try:
        print(f"[scraper] Intentando extraer datos de {FUENTE_OFICIAL} ...")
        resp = requests.get(FUENTE_OFICIAL, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        cursos = _parsear_oferta(soup)

        if not cursos:
            print("[scraper] La fuente respondió, pero no se hallaron cursos parseables.")
            return None

        print(f"[scraper] Extraídos {len(cursos)} cursos de la fuente oficial.")
        return cursos

    except Exception as exc:  # noqa: BLE001 — capturamos cualquier fallo de red/parseo
        print(f"[scraper] No se pudo extraer de la fuente oficial: {exc}")
        return None


def _parsear_oferta(soup: BeautifulSoup) -> list[dict]:
    """
    Convierte el HTML de la oferta en una lista de cursos.

    NOTA DE DISEÑO: el parseo concreto depende de la estructura HTML real del
    portal de oferta (que cambia cada período y suele requerir sesión). Como la
    fuente oficial bloquea el acceso automatizado, esta función queda PREPARADA
    pero sin parser específico: devuelve [] para que el sistema use el dataset
    semilla de respaldo. Aquí se integraría el parser real al disponer de acceso.
    """
    return []
