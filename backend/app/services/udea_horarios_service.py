"""
Servicio de horarios EN VIVO desde el portal oficial de la UdeA.

Reemplaza a la base de datos como fuente de los grupos, cupos, horarios y
profesores: consulta en tiempo real la página pública
"GRUPOS, CUPOS Y HORARIOS POR PROGRAMA" de Admisiones y Registro.

    https://ayudame2.udea.edu.co/php_mares/do.php?app=pub_cuposprog

El portal exige una sesión válida: primero un GET (que fija la cookie PHPSESSID
y entrega un token `numrand`) y luego el POST del formulario. Sin ese flujo el
sitio responde "Ha ingresado de forma inadecuada".

Para no golpear el sitio en cada mensaje del chat, la oferta se cachea en
memoria durante CACHE_TTL_SEGUNDOS (10 min por defecto).
"""
from __future__ import annotations

import re
import ssl
import time
import unicodedata
from dataclasses import dataclass, field

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# --- Parámetros del programa a consultar (Facultad / Programa de la UdeA) ---
FACULTAD_ID = "25"          # FACULTAD DE INGENIERÍA
FACULTAD_NOMBRE = "FACULTAD DE INGENIERÍA"
PROGRAMA_ID = "504"         # [00504] INGENIERÍA DE SISTEMAS
PROGRAMA_NOMBRE = "[00504] INGENIERÍA DE SISTEMAS"

_BASE = "https://ayudame2.udea.edu.co/php_mares"
_URL = f"{_BASE}/do.php?app=pub_cuposprog"
_USER_AGENT = "Mozilla/5.0 (PlaneAI-UdeA; asistente academico)"
_TIMEOUT = 30  # segundos por petición HTTP

CACHE_TTL_SEGUNDOS = 600  # 10 minutos

# Códigos de día usados por la UdeA (sin colisión: Martes=M, Miércoles=W).
_DIAS = {
    "L": "lunes",
    "M": "martes",
    "W": "miércoles",
    "J": "jueves",
    "V": "viernes",
    "S": "sábado",
    "D": "domingo",
}

# Una fila de la tabla: nombre(código) | Gr | CupoMax | CupoDisp | Horario(aula) | Profesor
_FILA_RE = re.compile(
    r"<tr align='center'>\s*"
    r"<td align='left'>(.*?)</td>\s*"
    r"<td>(.*?)</td>\s*"
    r"<td>(.*?)</td>\s*"
    r"<td>(.*?)</td>\s*"
    r"<td align='left'>(.*?)</td>\s*"
    r"<td align='left'>(.*?)</td>",
    re.S,
)
_CODIGO_RE = re.compile(r"\(([0-9]+)\)\s*$")
# Un bloque de día(s)+hora dentro del horario, p. ej. "MJ6-8" o "LWV10-12".
_BLOQUE_RE = re.compile(r"^([LMWJVSD]+)(\d{1,2})-(\d{1,2})$")


@dataclass
class Sesion:
    dia: str
    hora_inicio: str
    hora_fin: str


@dataclass
class GrupoVivo:
    numero: str
    cupos_totales: int
    cupos_disponibles: int
    aula: str
    profesor: str
    horario: list[Sesion] = field(default_factory=list)


@dataclass
class MateriaViva:
    nombre: str
    codigo: str
    grupos: list[GrupoVivo] = field(default_factory=list)


# --- Caché simple en memoria: {"datos": [...], "ts": monotonic} ---
_cache: dict = {"datos": None, "ts": 0.0}

# Semestre académico vigente detectado en el portal (p. ej. "20261").
_semestre: str = ""


def semestre_actual() -> str:
    """Semestre académico vigente según el portal (cadena vacía si aún no se consultó)."""
    return _semestre


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados (para comparar nombres)."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_acentos).strip().lower()


def _parsear_horario(celda: str) -> tuple[str, list[Sesion]]:
    """
    Convierte "INGENIA MJ6-8" en (aula="INGENIA", sesiones=[mar 06:00-08:00,
    jue 06:00-08:00]). El aula es el/los token(s) que no son bloques día-hora.
    """
    celda = celda.replace("&nbsp;", " ").strip()
    aula_tokens: list[str] = []
    sesiones: list[Sesion] = []

    for token in celda.split():
        m = _BLOQUE_RE.match(token)
        if not m:
            aula_tokens.append(token)
            continue
        letras, ini, fin = m.group(1), int(m.group(2)), int(m.group(3))
        for letra in letras:
            sesiones.append(
                Sesion(
                    dia=_DIAS.get(letra, letra),
                    hora_inicio=f"{ini:02d}:00",
                    hora_fin=f"{fin:02d}:00",
                )
            )

    return " ".join(aula_tokens) or "N/D", sesiones


def _limpiar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.replace("&nbsp;", " ")).strip()


class _TlsLegacyAdapter(HTTPAdapter):
    """
    Adaptador TLS para el portal de la UdeA, que usa una configuración antigua:
    - Solo ofrece TLSv1.2 con un cifrado RSA (AES256-GCM-SHA384) que OpenSSL 3.x
      excluye por defecto -> se rebaja el nivel de seguridad (SECLEVEL=1).
    - Presenta una CA autofirmada de la universidad que el bundle estándar de
      Python no reconoce -> se omite la verificación del certificado.
    """

    def _ctx(self) -> ssl.SSLContext:
        ctx = create_urllib3_context(ciphers="DEFAULT@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._ctx()
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self._ctx()
        return super().proxy_manager_for(*args, **kwargs)


def _nueva_sesion() -> requests.Session:
    """Crea una sesión HTTP con el adaptador TLS adaptado al portal UdeA."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    sesion = requests.Session()
    sesion.mount("https://", _TlsLegacyAdapter())
    sesion.headers.update({"User-Agent": _USER_AGENT})
    sesion.verify = False
    return sesion


def _descargar_html() -> str:
    """Ejecuta el flujo de sesión (GET + POST) y devuelve el HTML de resultados."""
    sesion = _nueva_sesion()

    # 1) GET inicial: fija la cookie PHPSESSID y entrega el token numrand.
    inicial = sesion.get(_URL, timeout=_TIMEOUT)
    inicial.encoding = "ISO-8859-1"
    m = re.search(r'name="numrand"\s+value="([0-9]+)"', inicial.text)
    if not m:
        raise RuntimeError("No se pudo obtener el token 'numrand' del portal UdeA.")
    numrand = m.group(1)

    # 2) Cargar los programas de la facultad (mantiene coherente el estado de sesión).
    sesion.get(
        f"{_BASE}/programas.php?facultad={FACULTAD_ID}&first=Seleccione",
        timeout=_TIMEOUT,
    )

    # 3) POST del formulario con la facultad y el programa elegidos.
    respuesta = sesion.post(
        _URL,
        headers={"Referer": _URL},
        data={
            "Facultad": FACULTAD_ID,
            "Programa": PROGRAMA_ID,
            "NombrePrograma": PROGRAMA_NOMBRE,
            "NombreFacultad": FACULTAD_NOMBRE,
            "numrand": numrand,
            "Parametros": "",
        },
        timeout=_TIMEOUT,
    )
    respuesta.encoding = "ISO-8859-1"
    if "inadecuada" in respuesta.text.lower():
        raise RuntimeError("El portal UdeA rechazó la consulta (sesión inválida).")
    return respuesta.text


def _parsear(html: str) -> list[MateriaViva]:
    """Convierte el HTML de resultados en una lista de materias con sus grupos."""
    global _semestre
    sem = re.search(r"Semestre:\s*</b>\s*([0-9]+)", html)
    if sem:
        _semestre = sem.group(1)

    materias: dict[str, MateriaViva] = {}

    for cruda in _FILA_RE.findall(html):
        nombre_codigo, gr, cm, cd, horario, profesor = (_limpiar(x) for x in cruda)

        cod_m = _CODIGO_RE.search(nombre_codigo)
        codigo = cod_m.group(1) if cod_m else ""
        nombre = _CODIGO_RE.sub("", nombre_codigo).strip()
        if not nombre:
            continue

        aula, sesiones = _parsear_horario(horario)

        materia = materias.setdefault(
            codigo or nombre, MateriaViva(nombre=nombre, codigo=codigo)
        )
        materia.grupos.append(
            GrupoVivo(
                numero=gr or "?",
                cupos_totales=int(cm) if cm.isdigit() else 0,
                cupos_disponibles=int(cd) if cd.isdigit() else 0,
                aula=aula,
                profesor=profesor or "Sin asignar",
                horario=sesiones,
            )
        )

    return sorted(materias.values(), key=lambda x: x.nombre)


def obtener_oferta(forzar: bool = False) -> list[MateriaViva]:
    """
    Devuelve la oferta en vivo del programa, usando la caché si sigue vigente.
    `forzar=True` ignora la caché y vuelve a consultar el portal.
    """
    ahora = time.monotonic()
    if (
        not forzar
        and _cache["datos"] is not None
        and (ahora - _cache["ts"]) < CACHE_TTL_SEGUNDOS
    ):
        return _cache["datos"]

    datos = _parsear(_descargar_html())
    _cache["datos"] = datos
    _cache["ts"] = ahora
    return datos


def buscar_materias(filtro: str) -> list[MateriaViva]:
    """Materias cuyo nombre o código contiene `filtro` (sin distinguir acentos)."""
    objetivo = normalizar(filtro)
    return [
        m
        for m in obtener_oferta()
        if objetivo in normalizar(m.nombre) or objetivo in m.codigo
    ]


def grupos_por_nombre(nombre: str) -> list[GrupoVivo]:
    """
    Grupos en vivo de la materia cuyo nombre coincide con `nombre`.
    Cruza por nombre normalizado (la BD y el portal usan códigos distintos).
    """
    objetivo = normalizar(nombre)
    for m in obtener_oferta():
        n = normalizar(m.nombre)
        if n == objetivo or objetivo in n or n in objetivo:
            return m.grupos
    return []
